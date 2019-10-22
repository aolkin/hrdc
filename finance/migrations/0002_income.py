# Generated by Django 2.1.11 on 2019-09-11 22:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Income',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('amount_requested', models.DecimalField(decimal_places=2, max_digits=7)),
                ('amount_received', models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True)),
                ('status', models.PositiveSmallIntegerField(choices=[(0, 'Planned'), (1, 'Applied'), (10, 'Confirmed'), (99, 'Rejected'), ('Administrative Statuses', ((11, 'Funds Received'), (12, 'A.R.T. Grant')))], default=0)),
                ('show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='finance.FinanceInfo')),
            ],
            options={
                'verbose_name': 'Grant/Income',
            },
        ),
    ]
