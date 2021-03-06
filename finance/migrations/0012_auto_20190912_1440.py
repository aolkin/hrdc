# Generated by Django 2.1.11 on 2019-09-12 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0011_auto_20190912_1408'),
    ]

    operations = [
        migrations.AlterField(
            model_name='expense',
            name='status',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Purchased'), ('P-Card', ((52, 'Confirmed'),)), ('Reimbursement', ((61, 'Requested'), (62, 'Processed')))], default=0),
        ),
    ]
