# Generated by Django 5.0.4 on 2024-04-21 22:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("destinyapp", "0006_transcriptdata_video_characteristics_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="BotData",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("bot_id", models.CharField(max_length=100)),
                ("last_time_ran", models.DateTimeField(default="")),
            ],
        ),
    ]
