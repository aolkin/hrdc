# Generated by Django 2.2.6 on 2019-11-04 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('venueapp', '0017_remove_defaultbudgetline_required'),
    ]

    operations = [
        migrations.RenameField(
            model_name='venueapp',
            old_name='instructions',
            new_name='budget_instr',
        ),
        migrations.AddField(
            model_name='venueapp',
            name='question_instr',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='venueapp',
            name='residency_instr',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='application',
            name='length_description',
            field=models.TextField(blank=True, help_text='Please elaborate on your preferences for residency length, if necessary.', verbose_name='Residency Length Preferences'),
        ),
        migrations.AlterField(
            model_name='budgetline',
            name='category',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Income'), (10, 'Administrative Expenses'), (20, 'Production Expenses'), (50, 'Other Expenses')], default=10),
        ),
        migrations.AlterField(
            model_name='defaultbudgetline',
            name='category',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Income'), (10, 'Administrative Expenses'), (20, 'Production Expenses'), (50, 'Other Expenses')], default=10),
        ),
    ]