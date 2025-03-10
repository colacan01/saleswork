from django import forms
from .models import WorkItem, Material, Product, Supplier, Brand, ProductInventory, InventoryItem
from datetime import datetime
from django.utils import timezone

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

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'brand', 'sale_price', 'unit_price', 'stock_quantity', 'barcode', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.Select(attrs={'class': 'form-select'}),
            'sale_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 폼이 렌더링될 때 사용자의 매장 정보를 활용할 수 있도록 준비
        self.fields['brand'].queryset = Brand.objects.all()  # 실제 사용 시에는 매장 기준으로 필터링해야 함
        self.fields['brand'].empty_label = "브랜드 선택"

class ProductInventoryForm(forms.ModelForm):
    class Meta:
        model = ProductInventory
        fields = ['inventory_date', 'supplier', 'reference_number', 'notes']
        widgets = {
            'inventory_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # 사용자의 매장에 속한 공급처만 보이도록 필터링
        if self.user and self.user.profile.store:
            self.fields['supplier'].queryset = Supplier.objects.filter(store=self.user.profile.store)
        
        # 초기값 설정
        if not self.instance.pk:  # 새로운 폼일 때
            self.fields['inventory_date'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')

class InventoryItemForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ['product', 'quantity', 'purchase_price']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # product 필드는 폼셋 컨텍스트에서 products를 받아 사용
        if not self.instance.pk:  # 새로운 폼일 때
            self.fields['purchase_price'].initial = 0
            self.fields['quantity'].initial = 1