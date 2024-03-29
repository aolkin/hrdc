# Generated by Django 2.2.24 on 2021-07-14 06:18

import django.core.validators
from django.db import migrations, models
import venueapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('venueapp', '0024_auto_20191106_1530'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='cast_breakdown',
            field=models.CharField(help_text='Intended gender preferences for your cast', max_length=80, verbose_name='Cast Gender Breakdown'),
        ),
        migrations.AlterField(
            model_name='application',
            name='script',
            field=models.FileField(blank=True, help_text='Only include for original or unknown works.', upload_to=venueapp.models.Application.upload_destination, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['pdf'])], verbose_name='Script'),
        ),
    ]
