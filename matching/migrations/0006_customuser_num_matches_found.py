# Generated by Django 3.2.7 on 2021-10-15 06:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0005_auto_20211015_0649'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='num_matches_found',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
