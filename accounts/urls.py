from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('store/edit/', views.store_edit_view, name='store_edit'),
]