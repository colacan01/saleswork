from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from main.models import WorkItem, Material, Product
from .forms import WorkItemForm, MaterialFormSet

# Create your views here.
def index(request):
    return render(request, 'sales/index.html')

def sales_detail(request, work_id):
    work_item = get_object_or_404(WorkItem, pk=work_id)
    materials = Material.objects.filter(work_item=work_item)
    context = {
        'work_item': work_item,
        'materials': materials,
    }
    return render(request, 'sales/sales_detail.html', context)

@login_required
def create_sales_item(request):
    
    if request.method == 'POST':
        work_form = WorkItemForm(request.POST)
        material_formset = MaterialFormSet(request.POST)
        
        if work_form.is_valid():
            # 작업 내용 저장
            work_item = work_form.save(commit=False)
            work_item.user = request.user  # 현재 로그인한 사용자를 작업자로 설정
            work_item.labor_cost = 0
            work_item.work_name = '매장판매'
            work_item.work_class = 'SALE'  # 작업 구분은 '판매'
            
            # 사용자 프로필에서 store 정보를 가져와 저장
            user_profile = request.user.profile
            if hasattr(user_profile, 'store') and user_profile.store:
                work_item.store = user_profile.store
                
            work_item.save()
            
            # 재료 정보 저장
            material_formset = MaterialFormSet(request.POST, instance=work_item)
            if material_formset.is_valid():
                material_formset.save()
                return redirect('sales_item_list')  # 목록 페이지로 이동
    else:
        work_form = WorkItemForm()
        # material_formset = MaterialFormSet()
        material_formset = MaterialFormSet(form_kwargs={'user': request.user})  # 현재 로그인한 사용자 정보 전달
    
    return render(request, 'sales/create_sales_item.html', {
        'work_form': work_form,
        'material_formset': material_formset,
    })
    
@login_required
def sales_item_list(request):
    """작업 항목 목록을 보여주는 뷰"""
    
    # 필터링 파라미터 처리
    filter_params = {}
    
    # 사용자 프로필의 store로 필터링
    user_profile = request.user.profile  # 사용자의 프로필 가져오기
    if hasattr(user_profile, 'store') and user_profile.store:
        filter_params['store'] = user_profile.store  # user 대신 store로 필터링
    
    # 추가 필터링 (예: 날짜 범위, 결제수단 등)
    payment_method = request.GET.get('payment_method')
    if payment_method:
        filter_params['payment_method'] = payment_method
    
    # 일시 필터링 추가
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if start_date:
        filter_params['date_time__gte'] = f"{start_date} 00:00:00"
    
    if end_date:
        filter_params['date_time__lte'] = f"{end_date} 23:59:59"
    
    filter_params['work_class'] = 'SALE'  # 판매 작업만 필터링
    
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
    
    return render(request, 'sales/sales_item_list.html', context)

def get_product_price(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        return JsonResponse({'price': product.sale_price})
    except Product.DoesNotExist:
        return JsonResponse({'error': '제품을 찾을 수 없습니다.'}, status=404)

def search_product_by_barcode(request, barcode):
    """
    바코드로 제품을 검색하여 JSON 응답으로 반환합니다.
    """
    # Debug: Print barcode to console
    print(f"Searching for product with barcode: {barcode}")
    try:
        # Get the store from the user's profile
        store = None
        if hasattr(request.user, 'profile') and hasattr(request.user.profile, 'store'):
            store = request.user.profile.store
        
        # Filter product by barcode and store if available
        if store:
            product = Product.objects.get(barcode=barcode, store=store)
        else:
            product = Product.objects.get(barcode=barcode)
        print(f"Found product: {product}")
        return JsonResponse({
            'success': True,
            'product': {
                'id': product.id,
                'name': product.name,
                'price': float(product.sale_price),  # Decimal을 float로 변환
                'barcode': product.barcode,
                # 필요한 다른 제품 필드도 추가 가능
            }
        })
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': '바코드와 일치하는 제품이 없습니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})