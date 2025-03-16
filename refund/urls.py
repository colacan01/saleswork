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

app_name = 'refund'

urlpatterns = [
    path('', views.RefundListView.as_view(), name='refund_list'),
    path('<int:pk>/', views.RefundDetailView.as_view(), name='refund_detail'),
    path('create/', views.RefundCreateView.as_view(), name='refund_create'),
    path('<int:pk>/update/', views.RefundUpdateView.as_view(), name='refund_update'),
    path('<int:pk>/delete/', views.RefundDeleteView.as_view(), name='refund_delete'),
    
    # RefundItem 관련 URL
    path('<int:refund_id>/add-item/', views.add_refund_item, name='add_refund_item'),
    path('item/<int:item_id>/delete/', views.delete_refund_item, name='delete_refund_item'),
    
    # 상태 업데이트 API
    path('<int:pk>/update-status/', views.update_refund_status, name='update_refund_status'),
]
