from django import forms
from .models import Refund, RefundItem
from django.utils.translation import gettext_lazy as _
from main.models import WorkItem

class RefundForm(forms.ModelForm):
    # order_number를 ModelChoiceField로 대체 (초기 queryset은 비어있게 설정)
    order_number = forms.ModelChoiceField(
        queryset=WorkItem.objects.none(),  # 초기에는 빈 queryset으로 설정
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label=_('주문 번호')
    )
    
    class Meta:
        model = Refund
        # store 필드 제외
        fields = ['refund_date', 'customer_phone', 'order_number', 'reason', 
                 'status', 'refund_method', 'notes']
        widgets = {
            'refund_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'refund_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            # store 위젯 제거
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 사용자가 있는 경우 해당 사용자의 매장 정보를 기반으로 주문 필터링
        if user and hasattr(user, 'profile') and user.profile.store:
            store = user.profile.store
            self.fields['order_number'].queryset = WorkItem.objects.filter(
                store=store
            ).exclude(
                work_class="WORK"
            )
        else:
            # 사용자 정보가 없거나 매장 정보가 없는 경우 기본 필터링만 적용
            self.fields['order_number'].queryset = WorkItem.objects.exclude(work_class="WORK")
        
        # 인스턴스가 있으면 order_number 필드 비활성화
        if 'instance' in kwargs and kwargs['instance'] is not None:
            self.fields['order_number'].disabled = True  # 이미 생성된 환불의 주문번호는 변경 불가

class RefundItemForm(forms.ModelForm):
    class Meta:
        model = RefundItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0})
        }

class RefundSearchForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '검색어...'}))
    status = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].choices = [('', '전체 상태')] + list(Refund.STATUS_CHOICES)