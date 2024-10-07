# Generated by Django 4.2.16 on 2024-10-07 18:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0014_seller_materials'),
    ]

    operations = [
        migrations.AlterField(
            model_name='seller',
            name='materials',
            field=models.ManyToManyField(related_name='sellers', to='api.material'),
        ),
    ]
