from django.db import migrations, models


def delete_existing_file_backed_photos(apps, schema_editor):
    Photo = apps.get_model("album", "Photo")
    Photo.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("album", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="image_data",
            field=models.BinaryField(default=b""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="photo",
            name="image_filename",
            field=models.CharField(default="", max_length=255),
            preserve_default=False,
        ),
        migrations.RunPython(delete_existing_file_backed_photos, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="photo",
            name="image",
        ),
    ]
