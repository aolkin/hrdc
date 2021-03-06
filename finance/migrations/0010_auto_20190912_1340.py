# Generated by Django 2.1.11 on 2019-09-12 17:40

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('finance', '0009_expense'),
    ]

    operations = [
        migrations.RenameField(
            model_name='expense',
            old_name='email',
            new_name='purchaser_email',
        ),
        migrations.AddField(
            model_name='expense',
            name='submitting_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
