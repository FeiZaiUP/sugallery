# Generated by Django 5.1.3 on 2024-12-05 09:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('galleryapp', '0006_alter_sharelink_share_code_tag_image_tags'),
    ]

    operations = [
        migrations.RenameField(
            model_name='image',
            old_name='file_path',
            new_name='file',
        ),
        migrations.AlterField(
            model_name='sharelink',
            name='share_code',
            field=models.CharField(default='65352fd6e86449f1aaaf8f2604da6ba9', max_length=64, unique=True),
        ),
    ]
