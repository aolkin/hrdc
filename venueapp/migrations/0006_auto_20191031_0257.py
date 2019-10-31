# Generated by Django 2.2.6 on 2019-10-31 06:57

from django.db import migrations, models
import venueapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('venueapp', '0005_auto_20191031_0153'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='script',
            field=models.FileField(blank=True, help_text='Only include for original or unknown works.', upload_to=venueapp.models.Application.upload_destination),
        ),
    ]
