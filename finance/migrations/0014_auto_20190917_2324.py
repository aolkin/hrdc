# Generated by Django 2.1.12 on 2019-09-18 03:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0013_auto_20190912_1507'),
    ]

    operations = [
        migrations.CreateModel(
            name='FinanceInfoExpenses',
            fields=[
            ],
            options={
                'verbose_name': 'Finance-Enabled Show - Expenses',
                'verbose_name_plural': 'Finance-Enabled Shows - Expenses',
                'proxy': True,
                'indexes': [],
            },
            bases=('finance.financeinfo',),
        ),
        migrations.AlterModelOptions(
            name='budgetexpense',
            options={'ordering': ('category',), 'verbose_name': 'Budgeted Expense Subcategory', 'verbose_name_plural': 'Budgeted Expense Subcategories'},
        ),
    ]
