# Generated by Django 2.1.11 on 2019-09-05 05:07

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('publicity', '0003_auto_20190905_0036'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShowPerson',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=120)),
                ('year', models.PositiveSmallIntegerField(blank=True)),
                ('position', models.CharField(blank=True, max_length=120)),
                ('type', models.PositiveSmallIntegerField(choices=[(0, 'Staff'), (1, 'Cast')], default=0)),
                ('show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='publicity.PublicityInfo')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
