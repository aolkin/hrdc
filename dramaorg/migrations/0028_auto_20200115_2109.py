# Generated by Django 2.2.6 on 2020-01-16 02:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0027_user_display_affiliation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='display_affiliation',
            field=models.BooleanField(default=False, help_text='Include your affiliation with your name and year?'),
        ),
    ]