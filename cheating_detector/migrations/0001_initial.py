# Generated by Django 5.2.4 on 2025-07-28 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SuspiciousEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('event_type', models.CharField(max_length=100)),
                ('details', models.TextField(blank=True, null=True)),
            ],
        ),
    ]
