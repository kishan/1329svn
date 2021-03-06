# Generated by Django 3.2.7 on 2021-10-16 06:13

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0008_auto_20211015_0759'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='match_create_times',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), default=list, size=None),
        ),
        migrations.AddField(
            model_name='customuser',
            name='num_matched_to_me',
            field=models.IntegerField(blank=True, default=0),
        ),
    ]
