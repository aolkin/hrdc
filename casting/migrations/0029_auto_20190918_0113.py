# Generated by Django 2.1.12 on 2019-09-18 05:13

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('casting', '0028_auto_20190918_0036'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='castingmeta',
            options={'permissions': (('modify_submission_status', 'Can change list submission status'), ('view_unreleased_callbacks', 'Can view unreleased callbacks'), ('view_unreleased_cast', 'Can view unreleased cast')), 'verbose_name': 'Casting-Enabled Show'},
        ),
    ]
