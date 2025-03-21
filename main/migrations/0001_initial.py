# Generated by Django 5.1.6 on 2025-03-04 12:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='상품명')),
                ('sale_price', models.DecimalField(decimal_places=0, max_digits=10, verbose_name='판매금액')),
                ('unit_price', models.DecimalField(decimal_places=0, max_digits=10, verbose_name='단위가격')),
                ('image', models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='상품 이미지')),
                ('stock_quantity', models.PositiveIntegerField(verbose_name='재고 수량')),
            ],
        ),
        migrations.CreateModel(
            name='WorkItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_time', models.DateTimeField(verbose_name='일시')),
                ('work_name', models.CharField(max_length=200, verbose_name='작업명')),
                ('material_cost', models.DecimalField(decimal_places=0, max_digits=10, verbose_name='재료비')),
                ('labor_cost', models.DecimalField(decimal_places=0, max_digits=10, verbose_name='공임')),
                ('payment_method', models.CharField(choices=[('CASH', '현금'), ('CARD', '카드'), ('LOCAL', '지역화폐')], default='CASH', max_length=10, verbose_name='결제수단')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='비고')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='작업자')),
            ],
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='수량')),
                ('unit_price', models.DecimalField(decimal_places=0, max_digits=10, verbose_name='단가')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.product', verbose_name='재료명')),
                ('work_item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='materials', to='main.workitem')),
            ],
        ),
    ]
