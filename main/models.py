from django.db import models
from django.contrib.auth.models import User
from accounts.models import Store  # Store 모델 import 추가
from django.utils.translation import gettext_lazy as _

class Supplier(models.Model):
    name = models.CharField(max_length=100, verbose_name='공급처명')
    business_number = models.CharField(max_length=15, verbose_name='사업자번호', blank=True, null=True)
    contact_info = models.CharField(max_length=200, blank=True, null=True, verbose_name='연락처')
    address = models.TextField(blank=True, null=True, verbose_name='주소')
    email = models.EmailField(blank=True, null=True, verbose_name='이메일')
    website = models.URLField(max_length=200, blank=True, null=True, verbose_name='웹사이트')
    contact_person = models.CharField(max_length=100, blank=True, null=True, verbose_name='담당자')
    is_active = models.BooleanField(default=True, verbose_name='활성화 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    store = models.ForeignKey(Store, verbose_name=_('매장'), on_delete=models.CASCADE, blank=True, null=True)
    
    class Meta:
        verbose_name = '공급처'
        verbose_name_plural = '공급처'
        ordering = ['name']
    
    def __str__(self):
        return self.name

    def get_brands(self):
        """해당 공급처와 연결된 모든 활성화된 브랜드 반환"""
        return self.brands.filter(is_active=True)
    
    @classmethod
    def get_active_suppliers(cls, store=None):
        """활성화된 모든 공급처 목록 반환 (매장별 필터링 가능)"""
        queryset = cls.objects.filter(is_active=True)
        if store:
            queryset = queryset.filter(store=store)
        return queryset

class Brand(models.Model):
    name = models.CharField(max_length=100, verbose_name='브랜드명')
    logo = models.ImageField(upload_to='brands/', null=True, blank=True, verbose_name='브랜드 로고')
    description = models.TextField(blank=True, null=True, verbose_name='브랜드 설명')
    website = models.URLField(max_length=200, blank=True, null=True, verbose_name='웹사이트')
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='brands', blank=True, verbose_name='공급처')
    is_active = models.BooleanField(default=True, verbose_name='활성화 여부')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='등록일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    store = models.ForeignKey(Store, verbose_name=_('매장'), on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        verbose_name = '브랜드'
        verbose_name_plural = '브랜드'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_products(self):
        # is_active 필터 제거
        return Product.objects.filter(brand=self)
    
    def get_supplier(self):
        """해당 브랜드의 공급처 반환"""
        return self.supplier
    
    @classmethod
    def get_active_brands(cls, store=None, supplier=None):
        """활성화된 모든 브랜드 목록 반환 (매장별, 공급처별 필터링 가능)"""
        queryset = cls.objects.filter(is_active=True)
        if store:
            queryset = queryset.filter(store=store)
        if supplier:
            queryset = queryset.filter(supplier=supplier)
        return queryset
    
# Create your models here.
class WorkItem(models.Model):
    """작업관리 모델 클래스"""
    
    # 결제수단 선택 옵션
    PAYMENT_CHOICES = [
        ('CASH', _('현금')),
        ('CARD', _('카드')),
        ('LOCAL', _('지역화폐')),
    ]
    
    WORK_CHOICES = [
        ('WORK', _('작업')),
        ('SALE', _('판매')),
        ('ONLINE', _('온라인')),
        ('KIOSK', _('키오스크')),
    ]
    
    date_time = models.DateTimeField(verbose_name=_('일시'))
    customer_phone = models.CharField(verbose_name=_('고객전화번호'), max_length=20, blank=True, null=True)
    work_name = models.CharField(verbose_name=_('작업명'), max_length=200)
    material_cost = models.DecimalField(verbose_name=_('재료비'), max_digits=10, decimal_places=0)
    labor_cost = models.DecimalField(verbose_name=_('공임'), max_digits=10, decimal_places=0)
    payment_method = models.CharField(
        verbose_name=_('결제수단'),
        max_length=10,
        choices=PAYMENT_CHOICES,
        default='CASH'
    )
    notes = models.TextField(verbose_name=_('비고'), blank=True, null=True)
    user = models.ForeignKey(User, verbose_name=_('작업자'), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, verbose_name=_('매장'), on_delete=models.CASCADE, blank=True, null=True)
    work_class = models.CharField(
        verbose_name=_('작업구분'),
        max_length=10,
        choices=WORK_CHOICES,
        default='WORK'
    )    
    
    def __str__(self):
        return f"{self.work_name} ({self.date_time.strftime('%Y-%m-%d')})"
    
    @property
    def total_amount(self):
        """총 금액 (재료비 + 공임)"""
        return self.material_cost + self.labor_cost

class Product(models.Model):
    """상품 모델 클래스"""
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, related_name='products', null=True, blank=True, verbose_name='브랜드')
    name = models.CharField(verbose_name=_('상품명'), max_length=200)
    sale_price = models.DecimalField(verbose_name=_('판매금액'), max_digits=10, decimal_places=0)
    unit_price = models.DecimalField(verbose_name=_('단위가격'), max_digits=10, decimal_places=0)
    image = models.ImageField(verbose_name=_('상품 이미지'), upload_to='products/', blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(verbose_name=_('재고 수량'))
    store = models.ForeignKey(Store, verbose_name=_('매장'), on_delete=models.CASCADE, blank=True, null=True)
    barcode = models.CharField(verbose_name=_('바코드'), max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.name

    @classmethod
    def get_store_products(cls, store=None):
        """특정 매장의 상품 목록 반환"""
        queryset = cls.objects.all()
        if store:
            queryset = queryset.filter(store=store)
        return queryset

class Material(models.Model):
    """재료 모델 클래스"""
    work_item = models.ForeignKey(WorkItem, related_name='materials', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name=_('재료명'), on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name=_('수량'))
    unit_price = models.DecimalField(verbose_name=_('단가'), max_digits=10, decimal_places=0)
    store = models.ForeignKey(Store, verbose_name=_('매장'), on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return self.product.name

    @property
    def total_cost(self):
        """총 비용 (수량 * 단가)"""
        return self.quantity * self.unit_price

