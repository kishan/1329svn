# Generated by Django 3.2.7 on 2021-10-15 07:23

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('matching', '0006_customuser_num_matches_found'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='match_found_time',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.DateTimeField(), default=list, size=None),
        ),
    ]