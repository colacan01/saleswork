from django import forms
from .models import WorkItem, Material, Product

class WorkItemForm(forms.ModelForm):
    class Meta:
        model = WorkItem
        fields = ['date_time', 'work_name', 'material_cost', 'labor_cost', 
                 'payment_method', 'notes']
        widgets = {
            'date_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(WorkItemForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[fieldname].label or fieldname.replace('_', ' ').title()
            })

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        fields = ['product', 'quantity', 'unit_price']
    
    def __init__(self, *args, **kwargs):
        super(MaterialForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[fieldname].label or fieldname.replace('_', ' ').title()
            })
        # 추가 속성 설정
        self.fields['product'].widget.attrs.update({'required': True})
        self.fields['quantity'].widget.attrs.update({'required': True, 'min': '1'})

# 동적으로 여러 재료를 추가할 수 있는 폼셋
MaterialFormSet = forms.inlineformset_factory(
    WorkItem, Material, 
    form=MaterialForm, 
    extra=1,  # 기본적으로 1줄 표시
    can_delete=True  # 삭제 가능하게
)