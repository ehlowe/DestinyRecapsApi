# Generated by Django 5.0.3 on 2024-03-30 22:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("destinyapp", "0003_alter_transcriptdata_text_chunks"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transcriptdata",
            name="text_chunks",
            field=models.JSONField(default=list),
        ),
    ]
