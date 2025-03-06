from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, StoreForm
from .models import Store
import os
from django.conf import settings

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'{username}님, 회원가입이 완료되었습니다! 로그인 해주세요.')
            return redirect('accounts:login')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')  # 메인 페이지로 리디렉션
        else:
            messages.error(request, '아이디 또는 비밀번호가 올바르지 않습니다.')
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('/')

@login_required
def profile_edit_view(request):
    # Store 정보 처리 로직 추가
    store = None
    if request.user.profile.store:
        store = request.user.profile.store
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        # 매장 소유자인 경우에만 store_form 처리
        store_form = None
        if 'is_store_owner' in request.POST:
            if store:
                store_form = StoreForm(request.POST, instance=store)
            else:
                store_form = StoreForm(request.POST)
        
        forms_valid = user_form.is_valid() and profile_form.is_valid()
        if store_form:
            forms_valid = forms_valid and store_form.is_valid()
            
        if forms_valid:
            user = user_form.save()
            profile = profile_form.save(commit=False)
            
            # 프로필 이미지 저장 경로 확인 및 생성
            if 'profile_image' in request.FILES:
                # 기본 미디어 경로에서 프로필 이미지가 저장될 경로 가져오기
                # 일반적으로 모델에서 정의한 upload_to 경로를 사용합니다
                upload_path = os.path.join(settings.MEDIA_ROOT, 'profile_images')
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path, exist_ok=True)
            
            # Store 정보 저장
            if profile.is_store_owner and store_form:
                if store:
                    store_form.save()
                else:
                    new_store = store_form.save()
                    profile.store = new_store
            elif not profile.is_store_owner:
                profile.store = None
                
            profile.save()
            messages.success(request, '프로필이 성공적으로 업데이트되었습니다!')
            return redirect('accounts:profile_edit')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
        store_form = StoreForm(instance=store) if store else StoreForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'store_form': store_form,
        'has_store': store is not None
    }
    return render(request, 'accounts/profile_edit.html', context)
