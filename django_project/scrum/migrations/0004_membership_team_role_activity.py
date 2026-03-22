from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('scrum', '0003_alter_project_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[
                    ('create_ticket', 'Created ticket'),
                    ('comment', 'Commented'),
                    ('status_change', 'Changed status'),
                    ('create_sprint', 'Created sprint'),
                    ('update_description', 'Updated description'),
                    ('assign', 'Assigned ticket'),
                ], max_length=50)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='scrum.project')),
                ('sprint', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scrum.sprint')),
                ('ticket', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='scrum.ticket')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]