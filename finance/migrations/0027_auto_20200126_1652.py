# Generated by Django 2.2.6 on 2020-01-26 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0026_auto_20200126_0225'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='settlement',
            options={'ordering': ('-year', '-season')},
        ),
        migrations.AddField(
            model_name='financeinfo',
            name='box_office',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7, verbose_name='Box Office Revenue'),
        ),
        migrations.AddField(
            model_name='financeinfo',
            name='royalties',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=7),
        ),
        migrations.AddField(
            model_name='settlement',
            name='club_budget_grant',
            field=models.DecimalField(decimal_places=2, default=1000, max_digits=7),
        ),
        migrations.AlterField(
            model_name='settlement',
            name='locked',
            field=models.BooleanField(default=False, help_text='Prevent users from adding, modifying, or updating income and expenses for this show.'),
        ),
    ]
