# Generated by Django 2.1.5 on 2019-01-27 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0012_auto_20181218_0327'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='post_register',
            field=models.CharField(default='', editable=False, max_length=240),
        ),
    ]
