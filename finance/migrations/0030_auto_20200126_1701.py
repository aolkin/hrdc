# Generated by Django 2.2.6 on 2020-01-26 22:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0029_auto_20200126_1700'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeinfo',
            name='ignore_royalties',
            field=models.BooleanField(default=False, help_text="If checked, don't count royalties against the revenue.", verbose_name='Ignore Royalties Cost'),
        ),
    ]