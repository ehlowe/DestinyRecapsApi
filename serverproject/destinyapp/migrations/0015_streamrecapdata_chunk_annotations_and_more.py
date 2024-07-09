# Generated by Django 5.0.4 on 2024-07-13 03:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("destinyapp", "0014_rename_transcriptdata_streamrecapdata"),
    ]

    operations = [
        migrations.AddField(
            model_name="streamrecapdata",
            name="chunk_annotations",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="streamrecapdata",
            name="plot_clickable_area_data",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="streamrecapdata",
            name="plot_image",
            field=models.ImageField(
                default="working_folder/default_image.jpg",
                upload_to="working_folder/stream_images",
            ),
        ),
    ]