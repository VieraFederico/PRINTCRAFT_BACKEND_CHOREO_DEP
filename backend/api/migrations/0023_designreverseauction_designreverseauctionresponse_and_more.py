# Generated by Django 4.2.16 on 2024-10-17 03:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0022_printreverseauction_response_count'),
    ]

    operations = [
        migrations.CreateModel(
            name='DesignReverseAuction',
            fields=[
                ('requestID', models.AutoField(primary_key=True, serialize=False)),
                ('description', models.TextField()),
                ('quantity', models.IntegerField()),
                ('material', models.CharField(max_length=255, null=True)),
                ('status', models.CharField(choices=[('Open', 'Open'), ('Closed', 'Closed')], default='Open', max_length=255)),
                ('response_count', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='DesignReverseAuctionResponse',
            fields=[
                ('responseID', models.AutoField(primary_key=True, serialize=False)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Rejected', 'Rejected')], default='Pending', max_length=255)),
                ('auction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='responses', to='api.designreverseauction')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.seller')),
            ],
        ),
        migrations.AddField(
            model_name='designreverseauction',
            name='accepted_response',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='accepted_auction', to='api.designreverseauctionresponse'),
        ),
        migrations.AddField(
            model_name='designreverseauction',
            name='design_images',
            field=models.ManyToManyField(to='api.designrequestimage'),
        ),
        migrations.AddField(
            model_name='designreverseauction',
            name='userID',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
