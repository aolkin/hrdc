# Generated by Django 2.2.6 on 2020-01-23 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0030_auto_20200118_1532'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='subscribed',
            field=models.BooleanField(default=False, verbose_name='Subscribe to the Newsletter'),
        ),
    ]
