# Generated by Django 2.0 on 2018-01-01 06:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('emailtracker', '0002_auto_20170725_2104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='queuedemail',
            name='ident',
            field=models.CharField(max_length=80),
        ),
        migrations.AlterField(
            model_name='queuedemail',
            name='name',
            field=models.CharField(max_length=40),
        ),
        migrations.AlterField(
            model_name='queuedemail',
            name='status',
            field=models.CharField(max_length=255),
        ),
    ]
