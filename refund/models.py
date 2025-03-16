from django.db import models
from django.contrib.auth.models import User
from accounts.models import Store
from main.models import Product
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from main.models import Product, WorkItem

class Refund(models.Model):
    """환불 관리 모델 클래스"""
    
    # 환불 상태 선택 옵션
    STATUS_CHOICES = [
        ('PENDING', _('처리 중')),
        ('APPROVED', _('승인됨')),
        ('COMPLETED', _('완료됨')),
        ('REJECTED', _('거부됨')),
    ]
    
    # 환불 방법 선택 옵션
    REFUND_METHOD_CHOICES = [
        ('CARD', _('카드')),
        ('BANK', _('계좌이체')),
        ('POINT', _('포인트')),
    ]
    
    refund_date = models.DateTimeField(verbose_name=_('환불일시'), default=timezone.now)
    customer_phone = models.CharField(verbose_name=_('고객전화번호'), max_length=20, blank=True, null=True)
    order_number = models.ForeignKey(WorkItem, verbose_name=_('주문번호'), on_delete=models.SET_NULL, blank=True, null=True)
    reason = models.TextField(verbose_name=_('환불사유'), blank=True, null=True)
    status = models.CharField(
        verbose_name=_('상태'),
        max_length=10,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    refund_method = models.CharField(
        verbose_name=_('환불방법'),
        max_length=10, 
        choices=REFUND_METHOD_CHOICES,
        default='CASH'
    )
    notes = models.TextField(verbose_name=_('비고'), blank=True, null=True)
    user = models.ForeignKey(User, verbose_name=_('처리자'), on_delete=models.CASCADE)
    store = models.ForeignKey(Store, verbose_name=_('매장'), on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('등록일'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('수정일'))
    
    def __str__(self):
        return f"환불-{self.id} ({self.refund_date.strftime('%Y-%m-%d')})"
    
    @property
    def total_amount(self):
        """총 환불 금액"""
        return sum(item.total_cost for item in self.refund_items.all())
    
    class Meta:
        verbose_name = _('환불')
        verbose_name_plural = _('환불 목록')
        indexes = [
            models.Index(fields=['store', 'refund_date'], name='idx_refund_date'),
            models.Index(fields=['status'], name='idx_refund_status'),
            models.Index(fields=['order_number'], name='idx_refund_order'),
        ]

class RefundItem(models.Model):
    """환불 상품 모델 클래스"""
    refund = models.ForeignKey(Refund, related_name='refund_items', on_delete=models.CASCADE, 
                              verbose_name=_('환불'))
    product = models.ForeignKey(Product, verbose_name=_('상품'), on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(verbose_name=_('수량'))
    unit_price = models.DecimalField(verbose_name=_('환불 단가'), max_digits=10, decimal_places=0)
    store = models.ForeignKey(Store, verbose_name=_('매장'), on_delete=models.CASCADE, blank=True, null=True)
    
    def __str__(self):
        return f"{self.product.name} ({self.quantity}개)"

    @property
    def total_cost(self):
        """총 환불 금액 (수량 * 환불 단가)"""
        return self.quantity * self.unit_price
    
    class Meta:
        verbose_name = _('환불 상품')
        verbose_name_plural = _('환불 상품 목록')
        indexes = [
            models.Index(fields=['refund', 'product'], name='idx_refund_product'),
        ]

    def save(self, *args, **kwargs):
        """환불 상품 저장 시 상품의 재고 수량 업데이트"""
        # 기존 객체인 경우 이전 수량 확인
        if self.pk:
            old_refund_item = RefundItem.objects.get(pk=self.pk)
            old_quantity = old_refund_item.quantity
        else:
            old_quantity = 0
        
        # 부모 save 메소드 실행
        super().save(*args, **kwargs)
        
        # 재고 수량 업데이트 (환불이므로 재고가 증가함)
        quantity_change = self.quantity - old_quantity
        if quantity_change != 0 and self.refund.status in ['APPROVED', 'COMPLETED']:
            self.product.stock_quantity += quantity_change
            self.product.save(update_fields=['stock_quantity'])

    def delete(self, *args, **kwargs):
        """환불 상품 삭제 시 상품의 재고 수량 조정"""
        # 환불이 완료 상태인 경우만 재고 조정
        if self.refund.status in ['APPROVED', 'COMPLETED']:
            # 삭제 전에 재고에서 다시 차감
            self.product.stock_quantity -= self.quantity
            self.product.save(update_fields=['stock_quantity'])
        
        # 부모 delete 메소드 실행
        super().delete(*args, **kwargs)
