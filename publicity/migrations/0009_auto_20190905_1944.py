# Generated by Django 2.1.11 on 2019-09-05 23:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('publicity', '0008_auto_20190905_1401'),
    ]

    operations = [
        migrations.AddField(
            model_name='showperson',
            name='email',
            field=models.EmailField(blank=True, max_length=254),
        ),
        migrations.AddField(
            model_name='showperson',
            name='phone',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
