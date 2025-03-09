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
from . import views

urlpatterns = [
    path('', views.index, name='sales_index'),
    path('sales/<int:work_id>/', views.sales_detail, name='sales_detail'),
    path('sales/create/', views.create_sales_item, name='create_sales_item'),
    path('sales_item_list/', views.sales_item_list, name='sales_item_list'),
    path('get-product-price/<int:product_id>/', views.get_product_price, name='get_product_price'),
]
