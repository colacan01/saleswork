from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import WorkItem, Material, Product
from .forms import WorkItemForm, MaterialFormSet, ProductForm
from accounts.models import Store, UserProfile
from datetime import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import Supplier, Brand
from .forms import SupplierForm, BrandForm  # 폼은 별도로 생성해야 함

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
        material_formset = MaterialFormSet(request.POST)
        
        if work_form.is_valid():
            # 작업 내용 저장
            work_item = work_form.save(commit=False)
            work_item.user = request.user  # 현재 로그인한 사용자를 작업자로 설정
            work_item.work_class = 'WORK'  # 작업 구분은 '작업'
            
            # 사용자 프로필에서 store 정보를 가져와 저장
            user_profile = request.user.profile
            if hasattr(user_profile, 'store') and user_profile.store:
                work_item.store = user_profile.store
                
            work_item.save()
            
            # 재료 정보 저장
            material_formset = MaterialFormSet(request.POST, instance=work_item)
            if material_formset.is_valid():
                material_formset.save()
                return redirect('work_item_list')  # 목록 페이지로 이동
    else:
        work_form = WorkItemForm()
        # material_formset = MaterialFormSet()
        material_formset = MaterialFormSet(form_kwargs={'user': request.user})  # 현재 로그인한 사용자 정보 전달
    
    return render(request, 'main/create_work_item.html', {
        'work_form': work_form,
        'material_formset': material_formset,
    })

@login_required
def work_item_list(request):
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
    
    filter_params['work_class'] = 'WORK'
    
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


# Supplier 관련 뷰
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'main/supplier_list.html'
    context_object_name = 'suppliers'
    
    def get_queryset(self):
        store = self.request.user.profile.store if hasattr(self.request.user, 'profile') else None
        queryset = Supplier.get_active_suppliers(store=store)
        
        # 공급처명 검색 필터링
        search_name = self.request.GET.get('search_name')
        if (search_name):
            queryset = queryset.filter(name__icontains=search_name)
            
        # 활성화 상태 필터링
        is_active = self.request.GET.get('is_active')
        if is_active == 'True':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'False':
            queryset = queryset.filter(is_active(False))
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '공급처 목록'
        return context


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'main/supplier_detail.html'
    context_object_name = 'supplier'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = self.object.get_brands()
        context['title'] = f'{self.object.name} 상세정보'
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'main/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    
    def form_valid(self, form):
        form.instance.store = self.request.user.profile.store if hasattr(self.request.user, 'profile') else None
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '새 공급처 등록'
        context['is_update'] = False
        return context


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'main/supplier_form.html'
    success_url = reverse_lazy('supplier-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '공급처 정보 수정'
        context['is_update'] = True
        return context


class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'main/supplier_confirm_delete.html'
    success_url = reverse_lazy('supplier-list')
    context_object_name = 'supplier'


# Brand 관련 뷰
class BrandListView(LoginRequiredMixin, ListView):
    model = Brand
    template_name = 'main/brand_list.html'
    context_object_name = 'brands'
    
    def get_queryset(self):
        store = self.request.user.profile.store if hasattr(self.request.user, 'profile') else None
        supplier_id = self.request.GET.get('supplier')
        supplier = None
        
        if supplier_id:
            try:
                supplier = Supplier.objects.get(pk=supplier_id)
            except Supplier.DoesNotExist:
                pass
                
        return Brand.get_active_brands(store=store, supplier=supplier)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        store = self.request.user.profile.store if hasattr(self.request.user, 'profile') else None
        context['suppliers'] = Supplier.get_active_suppliers(store=store)
        context['title'] = '브랜드 목록'
        
        # 선택된 공급처 정보 추가
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            try:
                context['selected_supplier'] = Supplier.objects.get(pk=supplier_id)
            except Supplier.DoesNotExist:
                pass
                
        return context


class BrandDetailView(LoginRequiredMixin, DetailView):
    model = Brand
    template_name = 'main/brand_detail.html'
    context_object_name = 'brand'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['products'] = self.object.get_products()
        context['title'] = f'{self.object.name} 브랜드 상세정보'
        return context


class BrandCreateView(LoginRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = 'main/brand_form.html'
    success_url = reverse_lazy('brand-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        store = self.request.user.profile.store if hasattr(self.request.user, 'profile') else None
        kwargs['store'] = store  # 폼에 store 전달
        return kwargs
    
    def form_valid(self, form):
        form.instance.store = self.request.user.profile.store if hasattr(self.request.user, 'profile') else None
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '새 브랜드 등록'
        context['is_update'] = False
        return context


class BrandUpdateView(LoginRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = 'main/brand_form.html'
    success_url = reverse_lazy('brand-list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        store = self.request.user.profile.store if hasattr(self.request.user, 'profile') else None
        kwargs['store'] = store  # 폼에 store 전달
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '브랜드 정보 수정'
        context['is_update'] = True
        return context


class BrandDeleteView(LoginRequiredMixin, DeleteView):
    model = Brand
    template_name = 'main/brand_confirm_delete.html'
    success_url = reverse_lazy('brand-list')
    context_object_name = 'brand'


# Product 관련 뷰
class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'main/product_list.html'
    context_object_name = 'products'
    paginate_by = 10
    
    def get_queryset(self):
        # 사용자 프로필에서 매장 정보 가져오기
        store = None
        if hasattr(self.request.user, 'profile'):
            store = self.request.user.profile.store
        
        # 매장 기준으로 상품 필터링
        return Product.get_store_products(store=store)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '상품 목록'
        return context

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'main/product_form.html'
    success_url = reverse_lazy('product_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '상품 추가'
        return context
    
    def form_valid(self, form):
        # 사용자의 매장 정보 자동 설정
        if hasattr(self.request.user, 'profile') and self.request.user.profile.store:
            form.instance.store = self.request.user.profile.store
        return super().form_valid(form)

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'main/product_detail.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        # 사용자 매장 기준으로 필터링
        store = None
        if hasattr(self.request.user, 'profile'):
            store = self.request.user.profile.store
        return Product.get_store_products(store=store)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '상품 상세'
        return context

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'main/product_form.html'
    success_url = reverse_lazy('product_list')
    
    def get_queryset(self):
        # 사용자 매장 기준으로 필터링
        store = None
        if hasattr(self.request.user, 'profile'):
            store = self.request.user.profile.store
        return Product.get_store_products(store=store)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '상품 수정'
        return context