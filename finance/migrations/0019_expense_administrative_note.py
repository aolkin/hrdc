# Generated by Django 2.1.12 on 2019-10-05 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0018_delete_financeinfoexpenses'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='administrative_note',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
