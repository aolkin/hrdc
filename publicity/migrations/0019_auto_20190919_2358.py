# Generated by Django 2.1.12 on 2019-09-20 03:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('publicity', '0018_auto_20190919_0152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='showperson',
            name='show',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='publicity.PublicityInfo'),
        ),
    ]
