# Generated by Django 4.2.16 on 2024-10-15 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0017_order_preference_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='designrequest',
            name='status',
            field=models.CharField(choices=[('Pendiente', 'Pendiente'), ('Rechazada', 'Rechazada'), ('Cotizada', 'Cotizada'), ('Cancelada', 'Cancelada'), ('En proceso', 'En proceso'), ('Realizada', 'Realizada'), ('Aceptada', 'Aceptada'), ('Entregada', 'Entregada')], default='Pendiente', max_length=255),
        ),
    ]
