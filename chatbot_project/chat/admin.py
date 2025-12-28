# chat/admin.py

from django.contrib import admin
from django.utils.html import format_html
from .models import Conversation, ClassificationResult


# --- 1. Inline for Classification Results ---

class ClassificationResultInline(admin.TabularInline):
    """
    Displays the ClassificationResult logs directly within the Conversation view.
    """
    model = ClassificationResult
    # Read-only fields to prevent accidental modification of log entries
    readonly_fields = (
        'timestamp',
        'topic',
        'escalation_status',
        'response_message_preview'
    )
    # Fields to display in the inline list
    fields = (
        'timestamp',
        'topic',
        'escalation_status',
        'response_message_preview'
    )
    extra = 0  # Do not show extra empty forms for log entries
    can_delete = False

    # Custom method to truncate long response messages for display
    def response_message_preview(self, obj):
        max_len = 70
        return obj.response_message[:max_len] + '...' if len(obj.response_message) > max_len else obj.response_message

    response_message_preview.short_description = 'Response Preview'


# --- 2. Admin for Conversation Model ---

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """
    Admin interface for the Conversation model, including inline logs.
    """
    list_display = ['session_id_short', 'turn_count', 'updated_at', 'created_at']
    search_fields = ['session_id']
    list_filter = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

    # Display inline Classification logs when viewing a conversation
    inlines = [ClassificationResultInline]

    # Fields to display in the detail view
    fieldsets = (
        (None, {
            'fields': ('session_id', 'created_at', 'updated_at', 'conversation_history_display')
        }),
    )
    readonly_fields = ('session_id', 'created_at', 'updated_at', 'conversation_history_display')

    # Custom method to display a truncated session ID
    def session_id_short(self, obj):
        return f"{obj.session_id[:8]}..."

    session_id_short.short_description = 'Session ID'

    # Custom method to count the number of turns (user + assistant messages)
    def turn_count(self, obj):
        # The history is a list of dicts; count the items
        return len(obj.history) if obj.history else 0

    turn_count.short_description = 'Turns'

    # Custom method to display the full conversation history beautifully
    def conversation_history_display(self, obj):
        html = ""
        for message in obj.history:
            role = message.get('role', 'unknown').capitalize()
            content = message.get('content', '')

            # Use format_html to render a simple, readable message block
            if role == 'User':
                html += format_html(
                    '<div style="margin-bottom: 10px; padding: 5px; border-left: 3px solid #007bff; background-color: #f8f9fa;"><strong>User:</strong> {}</div>',
                    content)
            elif role == 'Assistant':
                html += format_html(
                    '<div style="margin-bottom: 10px; padding: 5px; border-left: 3px solid #28a745; background-color: #e9f7ef;"><strong>Assistant:</strong> {}</div>',
                    content)
            else:
                html += format_html(
                    '<div style="margin-bottom: 10px; padding: 5px; border-left: 3px solid #ffc107; background-color: #fff3cd;"><strong>Unknown Role:</strong> {}</div>',
                    content)

        return html

    conversation_history_display.short_description = 'Full Conversation History'


# --- 3. Admin for ClassificationResult Model (Optional but good for global view) ---
# We keep this model admin registered for a list-view of all logs across all sessions.

@admin.register(ClassificationResult)
class ClassificationResultAdmin(admin.ModelAdmin):
    """
    Admin interface for the ClassificationResult log model (Turn-by-Turn view).
    """
    list_display = ('timestamp', 'conversation_link', 'topic', 'escalation_status', 'response_message_preview_list')
    list_filter = ('topic', 'escalation_status')
    search_fields = ['conversation__session_id', 'response_message']
    readonly_fields = ['conversation', 'timestamp', 'topic', 'escalation_status', 'response_message']
    date_hierarchy = 'timestamp'

    # Custom method to display a hyperlinked Session ID
    def conversation_link(self, obj):
        from django.urls import reverse
        link = reverse("admin:chat_conversation_change", args=[obj.conversation.pk])
        return format_html('<a href="{}">{}</a>', link, obj.conversation.session_id[:8] + '...')

    conversation_link.short_description = 'Session'

    # Custom method to preview content in the list view
    def response_message_preview_list(self, obj):
        return obj.response_message[:50] + '...' if len(obj.response_message) > 50 else obj.response_message

    response_message_preview_list.short_description = 'Response Preview'
