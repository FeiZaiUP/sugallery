# Generated by Django 5.1.3 on 2024-12-23 08:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('galleryapp', '0008_alter_sharelink_options_sharelink_created_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sharelink',
            name='share_code',
            field=models.CharField(default='2a4bec4be19f4b2da004981f8badbdb7', max_length=64, unique=True),
        ),
    ]