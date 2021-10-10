# Generated by Django 3.2.7 on 2021-10-10 06:52

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone', models.TextField(max_length=20)),
                ('first_name', models.CharField(blank=True, max_length=130)),
                ('last_name', models.CharField(blank=True, max_length=130)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
