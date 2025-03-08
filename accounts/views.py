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
def store_list_view(request):
    # 초기 쿼리셋 (전체 매장)
    queryset = Store.objects.all()
    
    # 검색 기능 구현
    search_name = request.GET.get('name', '')
    search_business_id = request.GET.get('business_id', '')
    
    if search_name:
        queryset = queryset.filter(name__icontains=search_name)
    if search_business_id:
        queryset = queryset.filter(business_id__icontains=search_business_id)
    
    # 생성/수정 폼 처리
    if request.method == 'POST':
        store_id = request.POST.get('store_id')
        
        # 수정인 경우 기존 매장 가져오기
        if store_id:
            try:
                store = Store.objects.get(id=store_id)
                form = StoreForm(request.POST, instance=store)
            except Store.DoesNotExist:
                form = StoreForm(request.POST)
        else:
            # 새로운 매장 생성
            form = StoreForm(request.POST)
            
        if form.is_valid():
            store = form.save(commit=False)
            if not store_id:  # 새로운 매장일 경우
                store.owner = request.user
            store.save()
            messages.success(request, '매장 정보가 성공적으로 저장되었습니다!')
            return redirect('accounts:store_list')
    else:
        form = StoreForm()  # 새로운 빈 폼
    
    context = {
        'stores': queryset,
        'form': form,
        'search_name': search_name,
        'search_business_id': search_business_id
    }
    return render(request, 'accounts/store_list.html', context)

@login_required
def store_delete_view(request, store_id):
    try:
        store = Store.objects.get(id=store_id)
        store_name = store.name  # 삭제 전에 매장 이름 저장
        store.delete()
        messages.success(request, f'{store_name} 매장이 성공적으로 삭제되었습니다.')
    except Store.DoesNotExist:
        messages.error(request, '삭제할 매장을 찾을 수 없습니다.')
    
    return redirect('accounts:store_list')


