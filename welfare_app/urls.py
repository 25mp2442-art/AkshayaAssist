from django.urls import path
from . import views

urlpatterns = [
    # Auth URLs
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Citizen URLs
    path('', views.home, name='home'),
    path('profile-setup/', views.profile_setup, name='profile_setup'),
    path('apply/<int:scheme_id>/', views.apply_scheme, name='apply_scheme'),
    path('my-applications/', views.my_applications, name='my_applications'),
    
    # Akshaya Staff URLs
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/process/<int:app_id>/', views.process_application, name='process_application'),
]