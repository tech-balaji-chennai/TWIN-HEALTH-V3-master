# chat/views.py

import os
import json
import uuid
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from pydantic import ValidationError  # Used for robust JSON validation

# --- Provider-Specific Imports ---
# Use conditional imports based on project settings (Gemini is recommended)
try:
    from google import genai
    from google.genai import types

    GEMINI_CLIENT = genai.Client(api_key=settings.LLM_API_KEY) if settings.LLM_PROVIDER == 'Gemini' else None
except ImportError:
    GEMINI_CLIENT = None

try:
    from openai import OpenAI

    # Initialize the OpenAI client globally if the provider is OpenAI
    OPENAI_CLIENT = OpenAI(api_key=settings.LLM_API_KEY) if settings.LLM_PROVIDER == 'OpenAI' else None
except ImportError:
    OPENAI_CLIENT = None

# --- Custom Imports (Assuming these files are correct and available) ---
from .models import Conversation, ClassificationResult
from .knowledge_base import LLM_RAG_CONTEXT  # This should contain the RAG rules/instructions
from .llm_schemas import ClassificationOutput, PYTHON_ESCALATION_MESSAGES, TopicCategory, Status


# --------------------------------------------------------------------------------
# 1. CORE LLM LOGIC: STRUCTURED CLASSIFICATION
# --------------------------------------------------------------------------------

def get_llm_classification(history_str: str) -> ClassificationOutput:
    """
    Interacts with the configured LLM (Gemini or OpenAI) for structured classification.
    """
    provider = settings.LLM_PROVIDER
    model_name = settings.LLM_MODEL

    # 1. Prepare the full prompt by combining RAG context and conversation history
    # We maintain a system and user message structure for clarity
    system_message = (
        f"{LLM_RAG_CONTEXT}\n\n"
        "Your task is strictly to analyze the conversation and output a JSON object "
        "that adheres to the provided schema. DO NOT generate any free-form text or preamble."
    )
    user_message = (
        "Analyze the following conversation history and classify the topic.\n"
        "**Conversation History:**\n"
        f"{history_str}\n"
        "Provide the complete ClassificationOutput JSON."
    )

    llm_result_json = None

    try:
        if provider == 'Gemini' and GEMINI_CLIENT:
            # --- GEMINI Implementation (Structured Output) ---
            # Valid roles: 'user' and 'model'. Use system_instruction for system content.

            schema = ClassificationOutput.model_json_schema()

            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.0,
                system_instruction=system_message,
            )

            response = GEMINI_CLIENT.models.generate_content(
                model=model_name,
                contents=[
                    {"role": "user", "parts": [{"text": user_message}]},
                ],
                config=config,
            )
            llm_result_json = response.text


        elif provider == 'OpenAI' and OPENAI_CLIENT:
            # --- OPENAI Implementation (Using native Structured Output) ---
            # Requires GPT-4o models (or latest gpt-4) and uses `response_format`

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ]

            response = OPENAI_CLIENT.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=0.0,
                # Enforce JSON output format with the new structured output features
                response_format={"type": "json_object", "json_schema": ClassificationOutput.model_json_schema()}
            )
            llm_result_json = response.choices[0].message.content


        else:
            raise ValueError(f"Unsupported LLM Provider ('{provider}') or missing SDK client.")

        # 2. Parse and Validate the JSON Output
        if not llm_result_json:
            raise ValueError("LLM returned an empty response.")

        # Pydantic validates the JSON against the schema and converts it to an object
        return ClassificationOutput.model_validate_json(llm_result_json)

    except (ValidationError, json.JSONDecodeError, ValueError) as e:
        print(f"LLM Output Parse/Config Failure: {e} | Raw Output: {llm_result_json}")
        error_rule = PYTHON_ESCALATION_MESSAGES["system_error"]
        return ClassificationOutput(
            topic=TopicCategory.OTHERS,
            status=Status(error_rule['status']),
            response_message=error_rule['message'],
            confidence=0.0,
            justification="System error fallback due to output parse/config failure."
        )
    except Exception as e:
        print(f"LLM API/Network Error: {e}")
        error_rule = PYTHON_ESCALATION_MESSAGES["system_error"]
        return ClassificationOutput(
            topic=TopicCategory.OTHERS,
            status=Status(error_rule['status']),
            response_message=error_rule['message'],
            confidence=0.0,
            justification="System error fallback due to API/network error."
        )


# --------------------------------------------------------------------------------
# 2. DJANGO VIEWS
# --------------------------------------------------------------------------------

def chatbot_view(request):
    """Renders the main chatbot interface."""
    return render(request, 'chat/index.html')


@csrf_exempt
def chat_api(request):
    """API endpoint to process user messages and run the classification/RAG logic."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not session_id:
            session_id = str(uuid.uuid4())

        # --- 3.1 Fetch/Update Conversation History ---
        conversation, created = Conversation.objects.get_or_create(
            session_id=session_id,
            defaults={'history': []}
        )
        conversation.history.append({'role': 'user', 'content': user_message})
        # Save the user message immediately, before processing
        conversation.save()

        # --- 3.2 Check for OTHERS/Acknowledgement Exception (Python Logic) ---
        is_generic_ack = user_message.lower() in ['ok', 'okay', 'thanks']
        is_first_message = len(conversation.history) == 1

        if is_generic_ack and is_first_message:
            ack_rule = PYTHON_ESCALATION_MESSAGES["generic_ack"]
            response_data = {
                'topic': 'OTHERS',
                'status': ack_rule['status'],  # 'no_response'
                'response': ''  # Empty response
            }
            # Log the classification result for auditing
            ClassificationResult.objects.create(
                conversation=conversation,
                topic='OTHERS',
                escalation_status=ack_rule['status'],
                response_message='NO_RESPONSE_ACK',
            )
            return JsonResponse(response_data)

        # --- 3.3 Execute RAG Classification Call ---
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in conversation.history])

        # Get the structured classification object
        llm_result: ClassificationOutput = get_llm_classification(history_str)
        response_text = llm_result.response_message
        # Ensure enums are serialized as strings for DB and JSON
        topic_str = llm_result.topic.value if hasattr(llm_result.topic, 'value') else str(llm_result.topic)
        status_str = llm_result.status.value if hasattr(llm_result.status, 'value') else str(llm_result.status)

        # --- 3.4 Process and Save Result ---

        # Save the assistant response to the conversation history
        # (This is the message returned to the user, based on the classification)
        conversation.history.append({'role': 'assistant', 'content': response_text})
        conversation.save()

        # Save the classification result for logging
        ClassificationResult.objects.create(
            conversation=conversation,
            topic=topic_str,
            escalation_status=status_str,
            response_message=response_text,
        )

        # Prepare the final JSON response for the frontend
        response_data = {
            'topic': topic_str,
            'status': status_str,
            'session_id': session_id,
            'response': response_text
        }
        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return JsonResponse({'error': 'An internal server error occurred'}, status=500)
