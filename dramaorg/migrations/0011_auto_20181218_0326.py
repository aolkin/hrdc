# Generated by Django 2.1.4 on 2018-12-18 08:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0010_user_post_register'),
    ]

    operations = [
        migrations.AddField(
            model_name='building',
            name='latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='building',
            name='longitude',
            field=models.FloatField(null=True),
        ),
    ]
