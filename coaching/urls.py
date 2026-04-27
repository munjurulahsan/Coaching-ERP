from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('get_client_name/', views.get_client_name, name='get_client_name'),
    path('get_next_roll/', views.get_next_roll, name='get_next_roll'),
    path('add_student/', views.add_student, name='add_student'),
    path('manage_payment/', views.manage_payment, name='manage_payment'),
    path('payment_status_check/', views.payment_status_check, name='payment_status_check'),
    path('batch_wise_payment_summary/', views.batch_wise_payment_summary, name='batch_wise_payment_summary'),
    path('coaches/', views.CoachListView.as_view(), name='coach_list'),
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
]