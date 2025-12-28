"""
Updated tests for the chat application matching current models and endpoints.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from .models import Conversation, ClassificationResult


class ChatModelTests(TestCase):
    """Test cases for chat models (Conversation & ClassificationResult)."""

    def test_conversation_creation_and_history(self):
        conversation = Conversation.objects.create(session_id='test-session')
        self.assertEqual(conversation.session_id, 'test-session')
        self.assertIsNotNone(conversation.created_at)
        self.assertEqual(conversation.history, [])

        # Append a message and verify persistence
        conversation.history.append({'role': 'user', 'content': 'Hello'})
        conversation.save()
        conversation.refresh_from_db()
        self.assertEqual(len(conversation.history), 1)
        self.assertEqual(conversation.history[0]['content'], 'Hello')

    def test_classification_result_creation(self):
        conversation = Conversation.objects.create(session_id='test-session-2', history=[])
        result = ClassificationResult.objects.create(
            conversation=conversation,
            topic='OTHERS',
            escalation_status='classified',
            response_message='Test response'
        )
        self.assertEqual(result.topic, 'OTHERS')
        self.assertEqual(result.escalation_status, 'classified')
        self.assertTrue(result.response_message.startswith('Test'))


class ChatViewTests(TestCase):
    """Test cases for chat views."""

    def setUp(self):
        self.client = Client()

    def test_index_view(self):
        # Name is 'chatbot_home' in chat/urls.py
        response = self.client.get(reverse('chatbot_home'))
        self.assertEqual(response.status_code, 200)

    def test_chat_api_generic_ack(self):
        # First message "ok" should trigger OTHERS + no_response without LLM call
        payload = {"message": "ok", "session_id": "unit-session"}
        response = self.client.post(reverse('chat_api'), data=payload, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['topic'], 'OTHERS')
        self.assertEqual(data['status'], 'no_response')


        
