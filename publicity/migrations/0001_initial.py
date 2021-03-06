# Generated by Django 2.1.11 on 2019-09-05 03:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dramaorg', '0014_show_liaisons'),
    ]

    operations = [
        migrations.CreateModel(
            name='PublicityInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('credits', models.TextField(blank=True)),
                ('contact_email', models.EmailField(blank=True, max_length=254)),
                ('runtime', models.CharField(blank=True, max_length=80)),
                ('show_blurb', models.TextField(blank=True)),
                ('content_warning', models.TextField(blank=True)),
                ('show', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='publicity_info', to='dramaorg.Show')),
            ],
            options={
                'verbose_name': 'Publicity-Enabled Show',
            },
        ),
    ]
