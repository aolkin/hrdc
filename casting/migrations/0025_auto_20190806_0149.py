# Generated by Django 2.1.5 on 2019-08-06 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('casting', '0024_auto_20190203_0005'),
    ]

    operations = [
        migrations.AlterField(
            model_name='castingreleasemeta',
            name='stage',
            field=models.PositiveSmallIntegerField(choices=[(0, 'Auditions'), (1, 'Callback Lists Released'), (2, 'First-Round Casting Released'), (3, 'Cast Lists Released'), (4, 'Signing Open'), (5, 'Sent Signing Reminder'), (6, 'Alternate Signing Open')], default=0),
        ),
    ]
