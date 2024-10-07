# Generated by Django 4.2.16 on 2024-10-07 16:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_remove_product_materials_seller_mp_mail_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='materials',
            field=models.ManyToManyField(through='api.ProductMaterial', to='api.material'),
        ),
    ]