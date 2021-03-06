# Generated by Django 2.0.5 on 2018-11-01 14:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('swa_app', '0002_auto_20180911_0306'),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('department', models.CharField(blank=True, max_length=256)),
                ('company_name', models.CharField(blank=True, max_length=30)),
                ('phone_number', models.CharField(blank=True, max_length=20)),
                ('country', models.CharField(blank=True, max_length=2)),
                ('opt_in', models.CharField(blank=True, max_length=3)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
