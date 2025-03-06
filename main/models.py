from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class WorkItem(models.Model):
    """작업관리 모델 클래스"""
    
    # 결제수단 선택 옵션
    PAYMENT_CHOICES = [
        ('CASH', '현금'),
        ('CARD', '카드'),
        ('LOCAL', '지역화폐'),
    ]
    
    date_time = models.DateTimeField(verbose_name='일시')
    customer_phone = models.CharField(verbose_name='고객전화번호', max_length=20, blank=True, null=True)
    work_name = models.CharField(verbose_name='작업명', max_length=200)
    material_cost = models.DecimalField(verbose_name='재료비', max_digits=10, decimal_places=0)
    labor_cost = models.DecimalField(verbose_name='공임', max_digits=10, decimal_places=0)
    payment_method = models.CharField(
        verbose_name='결제수단',
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='CASH'
    )
    notes = models.TextField(verbose_name='비고', blank=True, null=True)
    user = models.ForeignKey(User, verbose_name='작업자', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.work_name} ({self.date_time.strftime('%Y-%m-%d')})"
    
    @property
    def total_amount(self):
        """총 금액 (재료비 + 공임)"""
        return self.material_cost + self.labor_cost

class Product(models.Model):
    """상품 모델 클래스"""
    name = models.CharField(verbose_name='상품명', max_length=200)
    sale_price = models.DecimalField(verbose_name='판매금액', max_digits=10, decimal_places=0)
    unit_price = models.DecimalField(verbose_name='단위가격', max_digits=10, decimal_places=0)
    image = models.ImageField(verbose_name='상품 이미지', upload_to='products/', blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(verbose_name='재고 수량')
    
    def __str__(self):
        return self.name

class Material(models.Model):
    """재료 모델 클래스"""
    work_item = models.ForeignKey(WorkItem, related_name='materials', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name='재료명', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name='수량')
    unit_price = models.DecimalField(verbose_name='단가', max_digits=10, decimal_places=0)
    
    def __str__(self):
        return self.product.name

    @property
    def total_cost(self):
        """총 비용 (수량 * 단가)"""
        return self.quantity * self.unit_price

