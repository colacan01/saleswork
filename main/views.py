import pandas as pd
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from .models import WorkItem, Material, Product
from .forms import WorkItemForm, MaterialFormSet, ProductForm
from accounts.models import Store, UserProfile
from datetime import datetime
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import Supplier, Brand, Product, ProductInventory, InventoryItem
from .forms import SupplierForm, BrandForm, ProductForm, ProductInventoryForm, InventoryItemForm
# from .forms import SupplierForm, BrandForm, ProductInventoryForm, InventoryItemForm  # 폼은 별도로 생성해야 함
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect
from django.db import transaction
from django.forms import inlineformset_factory
from django.db.models import Q

from main import models

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
        queryset = Product.get_store_products(store=store)
        
        # 공급사 필터링
        supplier_id = self.request.GET.get('supplier')
        if supplier_id:
            try:
                supplier = Supplier.objects.get(pk=supplier_id)
                brands = Brand.objects.filter(supplier=supplier)
                queryset = queryset.filter(brand__in=brands)
            except:
                Supplier.DoesNotExist
            pass
            
        # 브랜드 필터링
        brand_id = self.request.GET.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
            
        # 상품명 검색
        search_name = self.request.GET.get('search_name')
        if search_name:
            queryset = queryset.filter(name__icontains=search_name)
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '상품 목록'
        
        # 공급처 정보 추가
        store = None
        if hasattr(self.request.user, 'profile'):
            store = self.request.user.profile.store
        context['suppliers'] = Supplier.get_active_suppliers(store=store)
        
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
    
def product_excel_upload(request):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        excel_file = request.FILES['excel_file']
        
        # 파일 확장자 검증
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, '지원하지 않는 파일 형식입니다. Excel 파일(.xlsx, .xls)을 업로드해주세요.')
            return redirect('product_list')
        
        try:
            # 현재 로그인한 사용자의 store 정보 가져오기
            store = None
            if hasattr(request.user, 'profile') and request.user.profile.store:
                store = request.user.profile.store
            
            # pandas로 Excel 파일 읽기 (첫 번째 행은 헤더, 두 번째 행부터 데이터로 처리)
            df = pd.read_excel(excel_file, header=0)
            
            # 필수 열 확인
            required_columns = ['id', 'name', 'sale_price', 'unit_price', 'stock_quantity']
            for col in required_columns:
                if col not in df.columns:
                    messages.error(request, f'필수 열({col})이 Excel 파일에 없습니다.')
                    return redirect('product_list')
            
            # 성공 및 오류 카운터 초기화
            created_count = 0
            updated_count = 0
            error_count = 0
            
            # 각 행 처리 (두 번째 행부터 데이터)
            for _, row in df.iterrows():
                try:
                    # 브랜드 처리 (있으면 가져오고 없으면 None)
                    brand = None
                    if 'brand' in df.columns and pd.notna(row['brand']):
                        brand, _ = Brand.objects.get_or_create(name=row['brand'], store=store)
                    
                    # ID가 있으면 업데이트, 없으면 생성
                    product_id = row['id'] if pd.notna(row['id']) else None
                    
                    defaults = {
                        'name': row['name'],
                        'sale_price': row['sale_price'],
                        'unit_price': row['unit_price'],
                        'stock_quantity': row['stock_quantity'],
                        'brand': brand,
                        'store': store  # 사용자의 store 정보 추가
                    }
                    
                    # 선택적 필드 추가
                    if 'barcode' in df.columns and pd.notna(row['barcode']):
                        defaults['barcode'] = row['barcode']
                    
                    if product_id:
                        # 해당 ID와 store가 일치하는 제품만 업데이트
                        obj, created = Product.objects.update_or_create(
                            id=product_id,
                            store=store,  # store도 함께 검색 조건에 추가
                            defaults=defaults
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                    else:
                        Product.objects.create(**defaults)
                        created_count += 1
                        
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row: {row}, Error: {e}")
            
            # 결과 메시지
            if error_count > 0:
                messages.warning(request, f'{created_count}개 상품 추가, {updated_count}개 상품 업데이트, {error_count}개 처리 중 오류가 발생했습니다.')
            else:
                messages.success(request, f'{created_count}개 상품이 추가되고 {updated_count}개 상품이 업데이트되었습니다.')
                
        except Exception as e:
            messages.error(request, f'Excel 파일 처리 중 오류가 발생했습니다: {str(e)}')
            
    else:
        messages.error(request, 'Excel 파일을 선택해주세요.')
        
    return redirect('product_list')

def get_brands_by_supplier(request):
    """공급사 ID를 받아 해당하는 브랜드 목록을 JSON으로 반환하는 API"""
    supplier_id = request.GET.get('supplier_id')
    
    if supplier_id:
        brands = Brand.objects.filter(supplier_id=supplier_id).values('id', 'name')
    else:
        brands = Brand.objects.all().values('id', 'name')
    
    return JsonResponse(list(brands), safe=False)

class ProductInventoryListView(LoginRequiredMixin, ListView):
    model = ProductInventory
    template_name = 'main/productinventory_list.html'
    context_object_name = 'inventories'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = ProductInventory.objects.all()
        
        # 매장 필터링 (로그인 사용자의 매장)
        if self.request.user.profile.store:
            queryset = queryset.filter(store=self.request.user.profile.store)
        
        # 날짜 필터링
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            queryset = queryset.filter(inventory_date__gte=date_from)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            queryset = queryset.filter(inventory_date__lte=date_to)
        
        # 공급처 필터링
        supplier = self.request.GET.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        
        # 확정 여부 필터링
        is_confirmed = self.request.GET.get('is_confirmed')
        if is_confirmed == '1':
            queryset = queryset.filter(is_confirmed=True)
        elif is_confirmed == '0':
            queryset = queryset.filter(is_confirmed=False)
        
        # 검색어 필터링
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(reference_number__icontains=search) | 
                models.Q(notes__icontains=search)
            )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 공급처 목록 추가
        store = None
        if self.request.user.profile.store:
            store = self.request.user.profile.store
        context['suppliers'] = Supplier.get_active_suppliers(store=store)
        return context

class ProductInventoryDetailView(LoginRequiredMixin, DetailView):
    model = ProductInventory
    template_name = 'main/productinventory_detail.html'
    context_object_name = 'inventory'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 사용자의 매장에 속한 입고만 조회 가능
        if self.request.user.profile.store:
            queryset = queryset.filter(store=self.request.user.profile.store)
        return queryset

class ProductInventoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductInventory
    form_class = ProductInventoryForm
    template_name = 'main/productinventory_form.html'
    success_url = reverse_lazy('productinventory_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # 인라인 폼셋 추가
        if self.request.POST:
            data['items'] = InventoryItemFormSet(self.request.POST)
        else:
            data['items'] = InventoryItemFormSet()
        
        # 상품 목록 (매장 필터링)
        store = None
        if self.request.user.profile.store:
            store = self.request.user.profile.store
        data['products'] = Product.get_store_products(store=store)
        
        return data
    
    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        
        # 폼과 폼셋이 모두 유효한지 확인
        if items.is_valid():
            with transaction.atomic():
                # 사용자와 매장 정보 설정
                form.instance.user = self.request.user
                if self.request.user.profile.store:
                    form.instance.store = self.request.user.profile.store
                
                # 메인 폼 저장
                self.object = form.save()
                
                # 아이템 폼셋 저장
                items.instance = self.object
                items.save()
            
            messages.success(self.request, '입고가 성공적으로 등록되었습니다.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class ProductInventoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductInventory
    form_class = ProductInventoryForm
    template_name = 'main/productinventory_form.html'
    context_object_name = 'inventory'
    success_url = reverse_lazy('productinventory_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 사용자의 매장에 속한 입고만 수정 가능
        if self.request.user.profile.store:
            queryset = queryset.filter(store=self.request.user.profile.store)
        # 확정된 입고는 수정 불가
        return queryset.filter(is_confirmed=False)
    
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        # 인라인 폼셋 추가
        if self.request.POST:
            data['items'] = InventoryItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = InventoryItemFormSet(instance=self.object)
        
        # 상품 목록 (매장 필터링)
        store = None
        if self.request.user.profile.store:
            store = self.request.user.profile.store
        data['products'] = Product.get_store_products(store=store)
        data['is_update'] = True
        
        return data
    
    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        
        # 폼과 폼셋이 모두 유효한지 확인
        if items.is_valid():
            with transaction.atomic():
                # 메인 폼 저장
                self.object = form.save()
                
                # 아이템 폼셋 저장
                items.instance = self.object
                items.save()
            
            messages.success(self.request, '입고가 성공적으로 수정되었습니다.')
            return HttpResponseRedirect(self.get_success_url())
        else:
            return self.render_to_response(self.get_context_data(form=form))

class ProductInventoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ProductInventory
    template_name = 'main/productinventory_confirm_delete.html'
    success_url = reverse_lazy('productinventory_list')
    context_object_name = 'inventory'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # 사용자의 매장에 속한 입고만 삭제 가능
        if self.request.user.profile.store:
            queryset = queryset.filter(store=self.request.user.profile.store)
        # 확정된 입고는 삭제 불가
        return queryset.filter(is_confirmed=False)
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, '입고가 성공적으로 삭제되었습니다.')
        return response

# 입고 확정 함수 뷰
from django.contrib.auth.decorators import login_required

@login_required
def confirm_inventory(request, pk):
    inventory = get_object_or_404(ProductInventory, pk=pk)
    
    # 사용자 권한 확인 (자신의 매장 입고만 확정 가능)
    if request.user.profile.store and inventory.store != request.user.profile.store:
        messages.error(request, '해당 입고를 확정할 권한이 없습니다.')
        return redirect('productinventory_list')
    
    # 이미 확정된 입고는 다시 확정 불가
    if inventory.is_confirmed:
        messages.warning(request, '이미 확정된 입고입니다.')
        return redirect('productinventory_detail', pk=pk)
    
    with transaction.atomic():
        # 입고 확정 상태로 변경
        inventory.is_confirmed = True
        inventory.save()
        
        # 입고 항목들을 순회하며 재고 업데이트
        for item in inventory.inventory_items.all():
            item.product.stock_quantity += item.quantity
            item.product.save()
    
    messages.success(request, '입고가 성공적으로 확정되었습니다. 재고가 업데이트되었습니다.')
    return redirect('productinventory_detail', pk=pk)

# 인라인 폼셋 정의
InventoryItemFormSet = inlineformset_factory(
    ProductInventory, InventoryItem, 
    form=InventoryItemForm,
    extra=5,  # 기본으로 보여줄 빈 폼 수
    can_delete=True  # 항목 삭제 허용
)