# Generated by Django 2.2.6 on 2020-01-23 02:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dramaorg', '0030_auto_20200118_1532'),
        ('publicity', '0031_auto_20200113_0045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='performancedate',
            name='note',
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AlterField(
            model_name='performancedate',
            name='performance',
            field=models.DateTimeField(verbose_name='Time and Date'),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('performance', models.DateTimeField(verbose_name='Time and Date')),
                ('note', models.CharField(blank=True, max_length=120)),
                ('name', models.CharField(max_length=120)),
                ('webpage', models.URLField(blank=True)),
                ('venue', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='dramaorg.Space')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
