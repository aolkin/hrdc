# Generated by Django 2.2.6 on 2020-01-10 23:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('publicity', '0027_showperson_person'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='showperson',
            name='email',
        ),
        migrations.RemoveField(
            model_name='showperson',
            name='name',
        ),
        migrations.RemoveField(
            model_name='showperson',
            name='phone',
        ),
        migrations.RemoveField(
            model_name='showperson',
            name='year',
        ),
    ]
