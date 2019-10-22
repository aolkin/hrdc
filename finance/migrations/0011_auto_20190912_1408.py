# Generated by Django 2.1.11 on 2019-09-12 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0010_auto_20190912_1340'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='purchased_using',
            field=models.PositiveSmallIntegerField(choices=[(0, 'P-Card'), (1, 'Personal Funds')], default=0),
        ),
    ]