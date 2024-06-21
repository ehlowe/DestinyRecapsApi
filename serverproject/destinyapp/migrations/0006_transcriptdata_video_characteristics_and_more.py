# Generated by Django 5.0.3 on 2024-04-04 03:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("destinyapp", "0005_transcriptdata_meta_alter_transcriptdata_transcript"),
    ]

    operations = [
        migrations.AddField(
            model_name="transcriptdata",
            name="video_characteristics",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="transcriptdata",
            name="summarized_chunks",
            field=models.JSONField(default=list),
        ),
    ]
