from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import UserProfile, Store

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[fieldname].label or fieldname.title()
            })

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'last_name', 'first_name']
        
    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[fieldname].label or fieldname.title()
            })

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        # fields = ['profile_image', 'is_store_owner', 'phone_number', 'address', 'birth_date', 'bio']
        # labels = {
        #     'profile_image': '프로필 이미지',
        #     'is_store_owner': '매장 소유자 여부',
        #     'phone_number': '전화번호',
        #     'address': '주소',
        #     'birth_date': '생일',
        #     'bio': '기타 정보'
        # }
        
        fields = ['profile_image', 'phone_number', 'address', 'birth_date', 'bio']
        labels = {
            'profile_image': _('프로필 이미지'),
            'phone_number': _('전화번호'),
            'address': _('주소'),
            'birth_date': _('생일'),
            'bio': _('기타 정보')
        }
        
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        super(ProfileUpdateForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            # 이미지 필드는 form-control-file 클래스 사용
            if fieldname == 'profile_image':
                self.fields[fieldname].widget.attrs.update({
                    'class': 'form-control-file',
                })
            # 체크박스 필드는 form-check-input 클래스 사용
            elif fieldname == 'is_store_owner':
                self.fields[fieldname].widget.attrs.update({
                    'class': 'form-check-input',
                })
            else:
                self.fields[fieldname].widget.attrs.update({
                    'class': 'form-control',
                    'placeholder': self.fields[fieldname].label or fieldname.title()
                })

class StoreForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['name', 'business_number', 'phone_number', 'address', 'website']
        labels = {
            'name': _('매장명'),
            'business_number': _('사업자번호'),
            'phone_number': _('전화번호'),
            'address': _('주소'),
            'website': _('웹사이트')
        }

    def __init__(self, *args, **kwargs):
        super(StoreForm, self).__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].widget.attrs.update({
                'class': 'form-control',
                'placeholder': self.fields[fieldname].label or fieldname.title()
            })