# Generated by Django 2.0.5 on 2018-09-11 03:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('swa_app', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='membership',
            name='usr_acct',
        ),
        migrations.RemoveField(
            model_name='membership',
            name='usr_role',
        ),
        migrations.RemoveField(
            model_name='userrole',
            name='members',
        ),
        migrations.DeleteModel(
            name='Membership',
        ),
        migrations.DeleteModel(
            name='UserAccount',
        ),
        migrations.DeleteModel(
            name='UserRole',
        ),
    ]
