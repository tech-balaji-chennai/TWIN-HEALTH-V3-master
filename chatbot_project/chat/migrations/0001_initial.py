from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_id', models.CharField(max_length=255, unique=True, db_index=True)),
                ('history', models.JSONField(default=list)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='ClassificationResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('topic', models.CharField(max_length=20, choices=[('LAB', 'Lab Appointments/Results'), ('TWIN_APPOINTMENT', 'Non-Lab Twin Health Appointments'), ('OTHERS', 'None of the Above / Escalation')])),
                ('escalation_status', models.CharField(max_length=50, choices=[('classified', 'Successfully Classified and Responded'), ('escalate', 'Requires Human Specialist Intervention'), ('no_response', 'Generic Acknowledgement (No Reply Sent)')])),
                ('response_message', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('conversation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='classifications', to='chat.conversation')),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['topic', 'escalation_status'], name='chat_class_idx')],
            },
        ),
    ]
