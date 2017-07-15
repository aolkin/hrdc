# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-15 19:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0003_auto_20170712_2005'),
        ('casting', '0005_auto_20170715_1055'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='audition',
            name='building',
        ),
        migrations.AddField(
            model_name='audition',
            name='space',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dramaorg.Space'),
        ),
    ]
