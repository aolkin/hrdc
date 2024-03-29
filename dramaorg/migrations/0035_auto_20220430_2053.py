# Generated by Django 2.2.24 on 2022-05-01 00:53

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0034_auto_20210716_0048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='show',
            name='slug',
            field=models.SlugField(max_length=80, unique=True),
        ),
        migrations.AlterField(
            model_name='show',
            name='space',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='dramaorg.Space', verbose_name='Venue'),
        ),
    ]
