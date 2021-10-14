# Generated by Django 3.2.7 on 2021-10-14 06:41

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0002_customuser_fun_fact'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='match_ids',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, max_length=260), default=[], size=None),
        ),
        migrations.AddField(
            model_name='customuser',
            name='num_matches_found',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
