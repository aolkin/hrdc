# Generated by Django 2.1.12 on 2019-09-20 03:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0014_auto_20190917_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='show',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finance.FinanceInfo'),
        ),
        migrations.AlterField(
            model_name='income',
            name='show',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finance.FinanceInfo'),
        ),
    ]
