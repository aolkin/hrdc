# Generated by Django 2.2.6 on 2020-01-13 05:45

from django.db import migrations
import django_thumbs.fields
import publicity.models


class Migration(migrations.Migration):

    dependencies = [
        ('publicity', '0030_publicityinfo_cover'),
    ]

    operations = [
        migrations.AlterField(
            model_name='publicityinfo',
            name='cover',
            field=django_thumbs.fields.ImageThumbsField(blank=True, null=True, sizes=({'code': 'thumb', 'resize': 'crop', 'wxh': '320x240'}, {'code': 'cover', 'resize': 'scale', 'wxh': '650x250'}), upload_to=publicity.models.PublicityInfo.upload_destination),
        ),
    ]
