# Generated by Django 4.2.16 on 2024-10-16 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0020_remove_printreverseauction_stl_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='printreverseauction',
            name='stl_file_url',
            field=models.URLField(default='https://supabase.com/dashboard/project/fdsafdsfd/editor/212165?schema=public'),
            preserve_default=False,
        ),
    ]