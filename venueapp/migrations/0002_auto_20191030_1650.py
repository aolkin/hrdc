# Generated by Django 2.2.6 on 2019-10-30 20:50

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import dramaorg.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('venueapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AvailableSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start', models.DateField()),
                ('end', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='BudgetLine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.PositiveSmallIntegerField(choices=[(0, 'Income'), (10, 'Administrative Expense'), (20, 'Production Expense'), (50, 'Other Expense')], default=10)),
                ('name', models.CharField(max_length=80)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('notes', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'ordering': ('show', 'venue', 'category'),
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=40)),
                ('question', models.TextField()),
                ('required', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RoleAnswer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RoleQuestion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=40)),
                ('question', models.TextField()),
                ('required', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SeasonStaffMeta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.PositiveSmallIntegerField(default=dramaorg.models._get_year)),
                ('season', models.PositiveSmallIntegerField(choices=[(0, 'Winter'), (1, 'Spring'), (2, 'Summer'), (3, 'Fall')], default=3)),
                ('resume', models.FileField(upload_to='')),
                ('conflicts', models.TextField(help_text='Big-picture conflicts for the upcoming season, such as other leadership positions or involvements.')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StaffMember',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signed_on', models.BooleanField(default=False)),
                ('other_role', models.CharField(blank=True, max_length=40)),
                ('statement', models.TextField(blank=True)),
                ('attachment', models.FileField(blank=True, upload_to='')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.SeasonStaffMeta')),
            ],
        ),
        migrations.CreateModel(
            name='StaffRole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('statement_length', models.PositiveIntegerField(default=0)),
                ('accepts_attachment', models.BooleanField(default=False)),
                ('assistant', models.BooleanField(default=False)),
                ('advisor', models.BooleanField(default=False)),
                ('other', models.BooleanField(default=False)),
            ],
        ),
        migrations.RemoveField(
            model_name='staffapp',
            name='app',
        ),
        migrations.RemoveField(
            model_name='staffapp',
            name='resume',
        ),
        migrations.RemoveField(
            model_name='staffapp',
            name='staff',
        ),
        migrations.RemoveField(
            model_name='application',
            name='budget',
        ),
        migrations.RemoveField(
            model_name='application',
            name='calendar',
        ),
        migrations.RemoveField(
            model_name='application',
            name='personnel_note',
        ),
        migrations.AddField(
            model_name='application',
            name='script',
            field=models.FileField(blank=True, help_text='Only include for original or unknown works.', upload_to=''),
        ),
        migrations.AddField(
            model_name='application',
            name='venues',
            field=models.ManyToManyField(to='venueapp.VenueApp'),
        ),
        migrations.AddField(
            model_name='slotpreference',
            name='length_description',
            field=models.TextField(default='', help_text='Describe your preferences for residency length, if applicable.'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='venueapp',
            name='live',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='slotpreference',
            name='end',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='slotpreference',
            name='start',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='venueapp',
            name='instructions',
            field=models.TextField(blank=True),
        ),
        migrations.AlterUniqueTogether(
            name='slotpreference',
            unique_together={('app', 'ordering')},
        ),
        migrations.DeleteModel(
            name='Resume',
        ),
        migrations.DeleteModel(
            name='StaffApp',
        ),
        migrations.AddField(
            model_name='staffmember',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='venueapp.StaffRole'),
        ),
        migrations.AddField(
            model_name='staffmember',
            name='show',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.Application'),
        ),
        migrations.AddField(
            model_name='rolequestion',
            name='role',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.StaffRole'),
        ),
        migrations.AddField(
            model_name='roleanswer',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.StaffMember'),
        ),
        migrations.AddField(
            model_name='roleanswer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='venueapp.RoleQuestion'),
        ),
        migrations.AddField(
            model_name='budgetline',
            name='show',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.Application'),
        ),
        migrations.AddField(
            model_name='budgetline',
            name='venue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.VenueApp'),
        ),
        migrations.AddField(
            model_name='availableslot',
            name='venue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.VenueApp'),
        ),
        migrations.AddField(
            model_name='answer',
            name='app',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.Application'),
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='venueapp.Question'),
        ),
        migrations.AddField(
            model_name='answer',
            name='venue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='venueapp.VenueApp'),
        ),
        migrations.AddField(
            model_name='slotpreference',
            name='slot',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='venueapp.AvailableSlot'),
        ),
        migrations.AddField(
            model_name='venueapp',
            name='questions',
            field=models.ManyToManyField(blank=True, to='venueapp.Question'),
        ),
    ]
