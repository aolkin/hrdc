# Generated by Django 2.2.6 on 2019-10-31 11:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venueapp', '0011_auto_20191031_0724'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='staffmember',
            options={'ordering': ('role__category', 'role__name', 'other_role')},
        ),
    ]