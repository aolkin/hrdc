# Generated by Django 2.2.6 on 2020-02-04 23:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('casting', '0032_auto_20200130_1821'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='character',
            options={'ordering': ('pk',)},
        ),
    ]
