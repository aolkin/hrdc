# Generated by Django 2.1.11 on 2019-09-05 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publicity', '0004_showperson'),
    ]

    operations = [
        migrations.AlterField(
            model_name='showperson',
            name='year',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
