# Generated by Django 2.2.6 on 2020-01-25 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0021_auto_20200125_1516'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='venmo_handle',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AlterField(
            model_name='expense',
            name='reimburse_via',
            field=models.PositiveSmallIntegerField(choices=[(2, 'Venmo'), (0, 'Check - Pick up'), (1, 'Check - Receive by Mail')], default=2),
        ),
    ]
