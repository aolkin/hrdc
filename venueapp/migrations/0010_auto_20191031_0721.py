# Generated by Django 2.2.6 on 2019-10-31 11:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venueapp', '0009_auto_20191031_0708'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='staffmember',
            unique_together={('show', 'person', 'role')},
        ),
    ]