# Generated by Django 2.0 on 2018-01-04 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    replaces = [('casting', '0004_auto_20180104_0022'), ('casting', '0005_auto_20180104_0056'), ('casting', '0006_auto_20180104_0138')]

    dependencies = [
        ('casting', '0003_auto_20180103_2319_squashed_0004_auto_20180103_2353'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actorseasonmeta',
            name='conflicts',
            field=models.TextField(help_text='Please list any recurring or major conflicts for this season.'),
        ),
        migrations.AlterField(
            model_name='audition',
            name='tech_interest',
            field=models.TextField(blank=True, default=None, help_text='What backstage or technical fields are you interested in?', null=True, verbose_name='Technical Interests'),
        ),
        migrations.AddField(
            model_name='audition',
            name='sign_in_complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='actorseasonmeta',
            name='conflicts',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='audition',
            name='tech_interest',
            field=models.TextField(blank=True, default=None, null=True, verbose_name='Technical Interests'),
        ),
    ]
