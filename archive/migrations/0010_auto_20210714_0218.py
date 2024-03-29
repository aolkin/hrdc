# Generated by Django 2.2.24 on 2021-07-14 06:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archive', '0009_auto_20191018_0246'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='extrafile',
            options={'verbose_name': 'Additional Material', 'verbose_name_plural': 'Additional Materials'},
        ),
        migrations.AlterModelOptions(
            name='productionphoto',
            options={'verbose_name': 'Production Photo', 'verbose_name_plural': 'Production Photos'},
        ),
        migrations.AlterField(
            model_name='extrafile',
            name='credit',
            field=models.CharField(max_length=120, verbose_name='File Credit'),
        ),
        migrations.AlterField(
            model_name='extrafile',
            name='description',
            field=models.CharField(max_length=240, verbose_name='File Description'),
        ),
        migrations.AlterField(
            model_name='productionphoto',
            name='allow_in_publicity',
            field=models.BooleanField(default=False, help_text='Allow this image or images to be used in HRDC publicity materials, such as the weekly newsletter'),
        ),
        migrations.AlterField(
            model_name='productionphoto',
            name='credit',
            field=models.CharField(max_length=120, verbose_name='Photo Credit'),
        ),
    ]
