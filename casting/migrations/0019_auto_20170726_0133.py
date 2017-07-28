# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-26 05:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('casting', '0018_auto_20170725_2104'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='castingmeta',
            options={'verbose_name': 'Casting-Enabled Show'},
        ),
        migrations.AlterModelOptions(
            name='castingreleasemeta',
            options={'verbose_name': 'Casting Release Group'},
        ),
        migrations.AlterField(
            model_name='castingmeta',
            name='release_meta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='casting.CastingReleaseMeta', verbose_name='Casting Release Group'),
        ),
    ]