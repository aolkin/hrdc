# Generated by Django 2.2.6 on 2020-01-25 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0020_remove_budgetexpense_reported'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expense',
            old_name='reimburse_via_mail',
            new_name='reimburse_via',
        ),
    ]
