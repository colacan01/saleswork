from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import WorkItem, Material, Product
from .forms import WorkItemForm, MaterialFormSet

# Create your views here.
def index(request):
    work_items = WorkItem.objects.all().order_by('-date_time')
    context = {
        'work_items': work_items
    }
    return render(request, 'main/index.html', context)

def work_detail(request, work_id):
    work_item = get_object_or_404(WorkItem, pk=work_id)
    materials = Material.objects.filter(work_item=work_item)
    context = {
        'work_item': work_item,
        'materials': materials,
    }
    return render(request, 'main/work_detail.html', context)

@login_required
def create_work_item(request):
    if request.method == 'POST':
        work_form = WorkItemForm(request.POST)
        
        if work_form.is_valid():
            # 작업 내용 저장
            work_item = work_form.save(commit=False)
            work_item.user = request.user  # 현재 로그인한 사용자를 작업자로 설정
            work_item.save()
            
            # 재료 정보 저장
            material_formset = MaterialFormSet(request.POST, instance=work_item)
            if material_formset.is_valid():
                material_formset.save()
                return redirect('work_item_list')  # 목록 페이지로 이동
    else:
        work_form = WorkItemForm()
        material_formset = MaterialFormSet()
    
    return render(request, 'main/create_work_item.html', {
        'work_form': work_form,
        'material_formset': material_formset,
    })

@login_required
def work_item_list(request):
    """작업 항목 목록을 보여주는 뷰"""
    
    # 필터링 파라미터 처리
    filter_params = {}
    
    # 기본적으로 로그인한 사용자의 작업 항목만 표시
    filter_params['user'] = request.user
    
    # 추가 필터링 (예: 날짜 범위, 결제수단 등)
    payment_method = request.GET.get('payment_method')
    if payment_method:
        filter_params['payment_method'] = payment_method
    
    # 작업 항목 조회 (최신순)
    work_items = WorkItem.objects.filter(**filter_params).order_by('-date_time')
    
    # 페이지네이션 구현
    paginator = Paginator(work_items, 10)  # 페이지당 10개 항목
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'payment_choices': WorkItem.PAYMENT_CHOICES,
    }
    
    return render(request, 'main/work_item_list.html', context)

def get_product_price(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({'price': product.unit_price})
    except Product.DoesNotExist:
        return JsonResponse({'error': '제품을 찾을 수 없습니다.'}, status=404)