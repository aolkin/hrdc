# Generated by Django 2.2.6 on 2019-10-31 09:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venueapp', '0007_auto_20191031_0459'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='staffmember',
            options={'ordering': ('role', 'other_role')},
        ),
    ]
