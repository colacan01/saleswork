"""
URL configuration for workmgr project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from . import views
from .views import ProductListView, ProductCreateView, ProductDetailView, ProductUpdateView


urlpatterns = [
    path('', views.index, name='index'),
    path('work/<int:work_id>/', views.work_detail, name='work_detail'),
    path('work/create/', views.create_work_item, name='create_work_item'),
    path('work_item_list/', views.work_item_list, name='work_item_list'),
    path('get-product-price/<int:product_id>/', views.get_product_price, name='get_product_price'),
    path('search-product-by-barcode/<str:barcode>/', views.search_product_by_barcode, name='search_product_by_barcode'),

    # Supplier URLs
    path('suppliers/', views.SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    path('suppliers/new/', views.SupplierCreateView.as_view(), name='supplier-create'),
    path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier-update'),
    path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier-delete'),
    
    # Brand URLs
    path('brands/', views.BrandListView.as_view(), name='brand-list'),
    path('brands/<int:pk>/', views.BrandDetailView.as_view(), name='brand-detail'),
    path('brands/new/', views.BrandCreateView.as_view(), name='brand-create'),
    path('brands/<int:pk>/edit/', views.BrandUpdateView.as_view(), name='brand-update'),
    path('brands/<int:pk>/delete/', views.BrandDeleteView.as_view(), name='brand-delete'),

    # Product URLs
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/create/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),
    path('products/excel-upload/', views.product_excel_upload, name='product_excel_upload'),
]
