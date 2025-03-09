from django import forms
from .models import WorkItem, Material, Product, Supplier, Brand
from datetime import datetime

class WorkItemForm(forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = ['date_time', 'customer_phone', 'work_name', 'labor_cost', 'material_cost', 
                 'payment_method', 'notes']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(WorkItemForm, self).__init__(*args, **kwargs)
        
        # 새 폼일 경우 현재 일시를 기본값으로 설정
        if not self.instance.pk and 'date_time' not in self.initial:
            now = datetime.now()
            # datetime-local 입력 형식에 맞게 포맷팅
            formatted_datetime = now.strftime('%Y-%m-%dT%H:%M')
            self.initial['date_time'] = formatted_datetime
        
        # 기존 필드 속성 설정 유지
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[fieldname].label or fieldname.replace('_', ' ').title()
            })
        
        # material_cost 필드를 읽기 전용으로 설정
        self.fields['material_cost'].widget.attrs['readonly'] = True

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['product', 'quantity', 'unit_price']
    
    def __init__(self, *args, **kwargs):
        # user 파라미터를 추출
        user = kwargs.pop('user', None)
        super(MaterialForm, self).__init__(*args, **kwargs)
        
        # 사용자의 store 정보를 기준으로 product 필터링
        if user:
            if hasattr(user, 'profile') and hasattr(user.profile, 'store'):
                self.fields['product'].queryset = Product.objects.filter(store=user.profile.store)
            elif hasattr(user, 'store'):
                self.fields['product'].queryset = Product.objects.filter(store=user.store)
        
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[fieldname].label or fieldname.replace('_', ' ').title()
            })
        # 추가 속성 설정
        self.fields['product'].widget.attrs.update({
            'required': True,
            'class': 'form-control product-select',  # 클래스 추가
            'onchange': 'updateUnitPrice(this)'  # 변경 이벤트 리스너 추가
        })
        self.fields['quantity'].widget.attrs.update({'required': True, 'min': '1'})
        self.fields['unit_price'].widget.attrs.update({'class': 'form-control unit-price-input'})

# 동적으로 여러 재료를 추가할 수 있는 폼셋
MaterialFormSet = forms.inlineformset_factory(
    WorkItem, Material, 
    form=MaterialForm, 
    extra=1,  # 기본적으로 1줄 표시
    can_delete=True  # 삭제 가능하게
)

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'business_number', 'contact_info', 'address', 'email', 
                  'website', 'contact_person', 'is_active']
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'logo', 'description', 'website', 'supplier', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        
    def __init__(self, *args, **kwargs):
        store = kwargs.pop('store', None)
        super().__init__(*args, **kwargs)
        
        # 공급처 필터링 (매장별)
        if store:
            self.fields['supplier'].queryset = Supplier.objects.filter(store=store, is_active=True)