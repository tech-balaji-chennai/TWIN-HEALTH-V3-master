# chat/llm_schemas.py

from enum import Enum
from pydantic import BaseModel, Field

# --- 1. Define ENUMs for Classification Choices (Standard str, Enum) ---

class TopicCategory(str, Enum):
    """Defines the set of possible primary categories for a user's query."""
    LAB = 'LAB'
    TWIN_APPOINTMENT = 'TWIN_APPOINTMENT'
    OTHERS = 'OTHERS'

class Status(str, Enum):
    """Defines the required action or escalation status after classification."""
    CLASSIFIED = 'classified'
    ESCALATE = 'escalate'
    NO_RESPONSE = 'no_response'

# --- 2. Pydantic Schema for LLM Output ---

class ClassificationOutput(BaseModel):
    """
    Structured output for classifying the conversation topic and determining status.
    This schema is used by the native LLM SDKs for guaranteed JSON output.
    """
    topic: TopicCategory = Field(description="The primary classification: LAB, TWIN_APPOINTMENT, or OTHERS.")
    status: Status = Field(description="The action status: 'classified', 'escalate', or 'no_response'.")
    response_message: str = Field(description="The determined response message. If status is 'escalate', this MUST contain the specific escalation message from the rules.")
    confidence: float = Field(description="A 0.0 to 1.0 confidence score for the classification.")
    justification: str = Field(description="A brief, internal-only explanation (1-2 sentences) of why this topic and status were selected.") # Added missing field

# --- 3. Python-Side Message Configuration (For views.py to use directly) ---

PYTHON_ESCALATION_MESSAGES = {
    "visit_prep_or_unrelated": {
        "message": "I'm sorry, I'm unable to help with that. I can forward this to a specialist and they'll respond via text within 1 business day.",
        "status": Status.ESCALATE.value # Use Enum value for consistency
    },
    "incorrect_info": {
        "message": "Thank you, I will forward this to a specialist. If they have questions they will respond within 1 business day.",
        "status": Status.ESCALATE.value
    },
    "non_english_spanish": {
        "message": "I can only converse in English or Spanish. I can forward this to a specialist and they'll respond via text within 1 business day.",
        "status": Status.ESCALATE.value
    },
    "system_error": {
        "message": "I'm sorry, there was a system error. I forwarded this to a specialist and they'll respond via text within 1 business day.",
        "status": Status.ESCALATE.value
    },
    "generic_ack": {
        "message": "NO_RESPONSE_ACK_TRIGGERED",
        "status": Status.NO_RESPONSE.value # Use Enum value for consistency
    }
}
