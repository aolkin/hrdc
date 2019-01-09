# Generated by Django 2.1.4 on 2018-12-13 09:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('casting', '0019_auto_20181213_0302'),
    ]

    operations = [
        migrations.AlterField(
            model_name='castingmeta',
            name='tech_req_pool',
            field=models.ManyToManyField(blank=True, related_name='tech_req_contributor_set', to='casting.CastingMeta', verbose_name='Actors must tech req on one of'),
        ),
    ]