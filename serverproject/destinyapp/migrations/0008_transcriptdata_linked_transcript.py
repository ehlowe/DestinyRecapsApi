# Generated by Django 5.0.4 on 2024-05-30 04:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("destinyapp", "0007_botdata"),
    ]

    operations = [
        migrations.AddField(
            model_name="transcriptdata",
            name="linked_transcript",
            field=models.CharField(default="", max_length=100000000),
        ),
    ]