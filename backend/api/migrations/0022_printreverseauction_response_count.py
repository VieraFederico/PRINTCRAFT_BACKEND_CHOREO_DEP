# Generated by Django 4.2.16 on 2024-10-16 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_printreverseauction_stl_file_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='printreverseauction',
            name='response_count',
            field=models.IntegerField(default=0),
        ),
    ]
