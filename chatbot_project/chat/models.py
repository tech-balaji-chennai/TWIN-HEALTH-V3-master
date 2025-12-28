# chat/models.py
from django.db import models
import uuid
from .llm_schemas import TopicCategory, Status


# --- Helper Function for Unique Default ---

def generate_uuid():
    """Generates a new, unique UUID for the session_id field."""
    return str(uuid.uuid4())


# --- Constant Definitions (Django Field Choices) ---

# This now works correctly because TopicCategory and Status are proper str, Enums
TOPIC_CHOICES = [
    (TopicCategory.LAB.value, 'Lab Appointments/Results'),
    (TopicCategory.TWIN_APPOINTMENT.value, 'Non-Lab Twin Health Appointments'),
    (TopicCategory.OTHERS.value, 'None of the Above / Escalation'),
]

ESCALATION_STATUS_CHOICES = [
    (Status.CLASSIFIED.value, 'Successfully Classified and Responded'),
    (Status.ESCALATE.value, 'Requires Human Specialist Intervention'),
    (Status.NO_RESPONSE.value, 'Generic Acknowledgement (No Reply Sent)'),
]


# --- 1. Conversation Model ---

class Conversation(models.Model):
    """Stores the full conversation history for a session."""

    session_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        default=generate_uuid,
        help_text="Unique identifier for the chat session, usually a UUID."
    )

    history = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"Session: {self.session_id}"


# --- 2. Classification Result Model (Logging) ---

class ClassificationResult(models.Model):
    """
    Logs the result of each LLM classification for a specific turn in a conversation.
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='classifications',
        help_text="The conversation turn belongs to."
    )

    topic = models.CharField(
        max_length=20,
        choices=TOPIC_CHOICES,
        help_text="The classification: LAB, TWIN_APPOINTMENT, or OTHERS."
    )

    escalation_status = models.CharField(
        max_length=50,
        choices=ESCALATION_STATUS_CHOICES,
        help_text="The action: classified, escalate, or no_response."
    )

    response_message = models.TextField(
        help_text="The final response text returned by the system."
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['topic', 'escalation_status']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.conversation.session_id} - {self.topic} ({self.escalation_status})"
