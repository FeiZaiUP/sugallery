# Generated by Django 5.1.3 on 2024-12-23 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_customuser_avatar'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='avatar',
            field=models.ImageField(blank=True, default='default/avatar.png', null=True, upload_to='avatars/'),
        ),
    ]
