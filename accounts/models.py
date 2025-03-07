from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    store = models.ForeignKey('Store', on_delete=models.CASCADE, related_name='profiles', null=True, blank=True, verbose_name='매장')
    is_store_owner = models.BooleanField(default=False, verbose_name='매장 소유자 여부')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username}의 프로필'


# User 모델이 생성될 때 자동으로 UserProfile 생성
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Store(models.Model):
    name = models.CharField(max_length=100, verbose_name='매장명', null=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores', verbose_name='소유자', null=True, blank=True)
    business_number = models.CharField(max_length=20, verbose_name='사업자번호', null=True, blank=True)
    phone_number = models.CharField(max_length=15, verbose_name='전화번호', null=True, blank=True)
    address = models.TextField(verbose_name='주소', null=True, blank=True)
    website = models.URLField(null=True, blank=True, verbose_name='웹사이트')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.name}'
    
    class Meta:
        verbose_name = '매장'
        verbose_name_plural = '매장 목록'
