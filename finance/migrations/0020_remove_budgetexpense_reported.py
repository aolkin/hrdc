# Generated by Django 2.2.6 on 2020-01-25 20:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0019_expense_administrative_note'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='budgetexpense',
            name='reported',
        ),
    ]
