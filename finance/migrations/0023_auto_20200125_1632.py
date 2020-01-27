# Generated by Django 2.2.6 on 2020-01-25 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0022_auto_20200125_1519'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='reimburse_via',
            field=models.PositiveSmallIntegerField(choices=[(2, 'Venmo'), (0, 'Check - Pick up'), (1, 'Check - Receive by Mail')], default=2),
        ),
    ]