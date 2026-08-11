from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
path('profile-setup/', views.profile_setup, name='profile_setup'),
path('apply/<int:scheme_id>/', views.apply_scheme, name='apply_scheme'),
path('my-applications/', views.my_applications, name='my_applications'),
path('staff-dashboard/', views.staff_dashboard, name='staff_dashboard'),
path('update-status/<int:app_id>/<str:status>/', views.update_application_status, name='update_status'),

]