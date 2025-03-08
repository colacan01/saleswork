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
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            
            # 프로필 이미지 저장 경로 확인 및 생성
            if 'profile_image' in request.FILES:
                upload_path = os.path.join(settings.MEDIA_ROOT, 'profile_images')
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path, exist_ok=True)
            
            profile.save()
            messages.success(request, '프로필이 성공적으로 업데이트되었습니다!')
            return redirect('accounts:profile_edit')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'accounts/profile_edit.html', context)

@login_required
def store_edit_view(request):
    # 사용자가 소유한 매장 찾기
    store = Store.objects.filter(owner=request.user).first()
    
    if request.method == 'POST':
        # POST 데이터에서 매장 소유자 여부 확인 (체크박스)
        is_owner = 'is_store_owner' in request.POST
        
        # 매장 폼 처리
        store_form = None
        if is_owner:
            if store:
                store_form = StoreForm(request.POST, instance=store)
            else:
                store_form = StoreForm(request.POST)
        
        # 매장 정보 저장
        if is_owner and store_form and store_form.is_valid():
            if store:
                store = store_form.save(commit=False)
                store.owner = request.user
                store.save()
            else:
                new_store = store_form.save(commit=False)
                new_store.owner = request.user
                new_store.save()
            
            # 프로필에 매장 소유자 상태 업데이트
            profile = request.user.profile
            profile.is_store_owner = True
            profile.save()
            
            messages.success(request, '매장 정보가 성공적으로 업데이트되었습니다!')
            return redirect('accounts:store_edit')
        elif not is_owner:
            # 소유자 아니라고 표시했으면 연결된 매장 소유권 제거
            if store:
                store.owner = None
                store.save()
            
            # 프로필에 매장 소유자 상태 업데이트
            profile = request.user.profile
            profile.is_store_owner = False
            profile.save()
            
            messages.success(request, '매장 소유자 상태가 변경되었습니다.')
            return redirect('accounts:store_edit')
    else:
        store_form = StoreForm(instance=store) if store else StoreForm()
    
    context = {
        'store_form': store_form,
        # 'has_store': store is not None
    }
    return render(request, 'accounts/store_edit.html', context)
