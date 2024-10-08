# Generated by Django 5.1.1 on 2024-09-23 21:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='orderDate',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='orderID',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(default='En proceso', max_length=255),
        ),
        migrations.AlterField(
            model_name='product',
            name='code',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='seller',
            name='store_name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
