from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.contrib import messages
from .models import Refund, RefundItem
from .forms import RefundForm, RefundItemForm
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

class RefundListView(LoginRequiredMixin, ListView):
    model = Refund
    template_name = 'refund/refund_list.html'
    context_object_name = 'refunds'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 매장 필터링 (현재 사용자의 매장 또는 관리자인 경우 모든 매장)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(store=self.request.user.store)
        
        # 검색 기능
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(customer_phone__icontains=search_query) |
                Q(order_number__order_number__icontains=search_query) |
                Q(reason__icontains=search_query)
            )
            
        # 상태 필터링
        status_filter = self.request.GET.get('status', '')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
            
        # 날짜 범위 필터링
        start_date = self.request.GET.get('start_date', '')
        end_date = self.request.GET.get('end_date', '')
        if start_date and end_date:
            queryset = queryset.filter(refund_date__range=[start_date, end_date])
            
        return queryset.order_by('-refund_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Refund.STATUS_CHOICES
        return context

class RefundDetailView(LoginRequiredMixin, DetailView):
    model = Refund
    template_name = 'refund/refund_detail.html'
    context_object_name = 'refund'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['refund_items'] = self.object.refund_items.all()
        return context

class RefundCreateView(LoginRequiredMixin, CreateView):
    model = Refund
    form_class = RefundForm
    template_name = 'refund/refund_form.html'
    success_url = reverse_lazy('refund:refund_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
        
    def form_valid(self, form):
        form.instance.user = self.request.user
        # 사용자 프로필에서 매장 정보 가져와 설정
        form.instance.store = self.request.user.profile.store
        return super().form_valid(form)

class RefundUpdateView(LoginRequiredMixin, UpdateView):
    model = Refund
    form_class = RefundForm
    template_name = 'refund/refund_form.html'
    success_url = reverse_lazy('refund:refund_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['refund_items'] = RefundItem.objects.filter(refund=self.object)
        return context

class RefundDeleteView(LoginRequiredMixin, DeleteView):
    model = Refund
    template_name = 'refund/refund_confirm_delete.html'
    success_url = reverse_lazy('refund:refund_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, _('환불이 삭제되었습니다.'))
        return super().delete(request, *args, **kwargs)

# RefundItem 관련 뷰
@login_required
def add_refund_item(request, refund_id):
    refund = get_object_or_404(Refund, id=refund_id)
    
    if request.method == 'POST':
        form = RefundItemForm(request.POST)
        if form.is_valid():
            refund_item = form.save(commit=False)
            refund_item.refund = refund
            # 사용자가 특정 매장에 속한 경우 자동으로 매장 설정
            if not request.user.is_superuser and hasattr(request.user, 'store'):
                refund_item.store = request.user.store
            refund_item.save()
            return redirect('refund:refund_detail', pk=refund.id)
    else:
        form = RefundItemForm()
    
    return render(request, 'refund/refund_item_form.html', {
        'form': form,
        'refund': refund
    })

@login_required
def delete_refund_item(request, item_id):
    refund_item = get_object_or_404(RefundItem, id=item_id)
    refund_id = refund_item.refund.id
    
    if request.method == 'POST':
        refund_item.delete()
        messages.success(request, _('환불 상품이 삭제되었습니다.'))
        return redirect('refund:refund_detail', pk=refund_id)
    
    return render(request, 'refund/refund_item_confirm_delete.html', {
        'refund_item': refund_item
    })

@login_required
def update_refund_status(request, pk):
    if request.method == 'POST' and request.is_ajax():
        refund = get_object_or_404(Refund, pk=pk)
        new_status = request.POST.get('status')
        
        if new_status in dict(Refund.STATUS_CHOICES):
            refund.status = new_status
            refund.save()
            return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': '잘못된 요청입니다.'})
