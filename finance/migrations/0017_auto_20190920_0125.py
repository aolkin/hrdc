# Generated by Django 2.1.12 on 2019-09-20 05:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0016_expense_check_number_squashed_0018_auto_20190920_0006'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='expense',
            options={'ordering': ('date_purchased',)},
        ),
    ]
