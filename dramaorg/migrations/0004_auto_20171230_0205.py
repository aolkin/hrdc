# Generated by Django 2.0 on 2017-12-30 07:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0003_auto_20171230_0053'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='space',
            unique_together={('name', 'building')},
        ),
    ]