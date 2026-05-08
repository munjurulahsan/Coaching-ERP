from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='coaching/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path(
        'password-change/',
        auth_views.PasswordChangeView.as_view(
            template_name='coaching/password_change.html',
            success_url='done/',
        ),
        name='password_change',
    ),
    path(
        'password-change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='coaching/password_change_done.html',
        ),
        name='password_change_done',
    ),
    path('', views.home, name='home'),
    path('get_client_name/', views.get_client_name, name='get_client_name'),
    path('get_next_roll/', views.get_next_roll, name='get_next_roll'),
    path('add_student/', views.add_student, name='add_student'),
    path('import_students/', views.import_students, name='import_students'),
    path('manage_payment/', views.manage_payment, name='manage_payment'),
    path('payment_report/', views.payment_report, name='payment_report'),
    path('batch_list/', views.batch_list, name='batch_list'),
    path('batch/create/', views.batch_create, name='batch_create'),
    path('batch/<int:pk>/edit/', views.batch_edit, name='batch_edit'),
    path('batch/<int:pk>/delete/', views.batch_delete, name='batch_delete'),
    path('batch-notice/', views.batch_notice, name='batch_notice'),
    path('payment_status_check/', views.payment_status_check, name='payment_status_check'),
    path('batch_wise_payment_summary/', views.batch_wise_payment_summary, name='batch_wise_payment_summary'),
    path('clients/<int:pk>/', views.client_profile, name='client_profile'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('coaches/', views.CoachListView.as_view(), name='coach_list'),
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('sessions/', views.SessionListView.as_view(), name='session_list'),
    path('payments/', views.PaymentListView.as_view(), name='payment_list'),
    path('payments/<int:pk>/edit/', views.payment_edit, name='payment_edit'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
]
