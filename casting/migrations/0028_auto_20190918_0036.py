# Generated by Django 2.1.12 on 2019-09-18 04:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('casting', '0027_auto_20190918_0017'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='audition',
            options={'permissions': (('table_auditions', 'Can table at audition sign-ins'),)},
        ),
        migrations.AlterModelOptions(
            name='castingreleasemeta',
            options={'permissions': (('view_first_cast_lists', 'Can view first-round cast lists'),), 'verbose_name': 'Casting Release Group'},
        ),
    ]
