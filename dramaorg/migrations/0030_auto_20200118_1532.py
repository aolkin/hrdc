# Generated by Django 2.2.6 on 2020-01-18 20:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0029_auto_20200116_1439'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='space',
            options={'ordering': ('order',)},
        ),
        migrations.AddField(
            model_name='space',
            name='order',
            field=models.PositiveSmallIntegerField(default=0),
        ),
    ]
