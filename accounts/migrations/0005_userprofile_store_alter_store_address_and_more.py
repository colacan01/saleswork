# Generated by Django 5.1.6 on 2025-03-07 12:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_remove_userprofile_store_store_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to='accounts.store', verbose_name='매장'),
        ),
        migrations.AlterField(
            model_name='store',
            name='address',
            field=models.TextField(blank=True, null=True, verbose_name='주소'),
        ),
        migrations.AlterField(
            model_name='store',
            name='business_number',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='사업자번호'),
        ),
        migrations.AlterField(
            model_name='store',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='매장명'),
        ),
        migrations.AlterField(
            model_name='store',
            name='phone_number',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='전화번호'),
        ),
    ]
