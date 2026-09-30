from django.urls import path
from . import views

urlpatterns = [
    # Citizen URLs
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_setup, name='profile_setup'),
    path('apply/<int:scheme_id>/', views.apply_scheme, name='apply_scheme'),
    path('my-applications/', views.my_applications, name='my_applications'),
    
    # Citizen Workflow URLs
    path('reupload/<int:app_id>/', views.reupload_docs, name='reupload_docs'),
    path('book-token/<int:app_id>/', views.book_token, name='book_token'),
    path('live-queue/<int:app_id>/', views.live_queue, name='live_queue'),
    
    # Staff URLs
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/verify/<int:app_id>/', views.staff_verify_docs, name='staff_verify_docs'),
    path('staff/counter/', views.staff_counter_process, name='staff_counter_process'),
    path('process-application/<int:app_id>/', views.process_application, name='process_application'),
    # urls.pyൽ ചേർക്കുക:
    path('staff/govt-form/<int:app_id>/', views.staff_govt_form_process, name='staff_govt_form_process'),
]