import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Max

from .models import UserProfile, Scheme, Application, ApplicationDocument

def is_staff_user(user):
    return user.is_staff or user.is_superuser

# 1. User Registration & Login Handlers
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! Please login.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if user.is_superuser:
                return redirect('/admin/')
            elif user.is_staff:
                return redirect('staff_dashboard')
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('login')

# 2. Profile Setup
@login_required(login_url='login')
def profile_setup(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.age = request.POST.get('age') or None
        profile.annual_income = request.POST.get('annual_income') or None
        profile.ration_card_type = request.POST.get('ration_card_type')
        profile.category = request.POST.get('category')
        profile.gender = request.POST.get('gender')
        profile.occupation = request.POST.get('occupation')
        profile.marital_status = request.POST.get('marital_status')

        is_disabled = request.POST.get('is_differently_abled') == 'True'
        profile.is_differently_abled = is_disabled
        if is_disabled:
            profile.disability_type = request.POST.get('disability_type')
            profile.disability_percentage = request.POST.get('disability_percentage') or None
        else:
            profile.disability_type = None
            profile.disability_percentage = None

        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('home')
    return render(request, 'profile_setup.html', {'profile': profile})

# 3. User Home Screen (Filtering Scheme Eligibility)
@login_required(login_url='login')
def home(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    eligible_schemes = []
    profile_complete = False
    applied_scheme_ids = set(Application.objects.filter(user=request.user).values_list('scheme_id', flat=True))

    if (profile.annual_income is not None and profile.ration_card_type and profile.category and profile.gender):
        profile_complete = True
        all_schemes = Scheme.objects.all()

        try:
            user_income = float(profile.annual_income)
        except (ValueError, TypeError):
            user_income = 0.0

        user_card = (profile.ration_card_type or "").strip()
        user_cat = (profile.category or "").strip()
        user_gender = (profile.gender or "").strip()
        user_occ = (profile.occupation or "").strip()
        user_marital = (profile.marital_status or "").strip()
        user_age = profile.age or 0

        for scheme in all_schemes:
            income_ok = user_income <= scheme.max_income
            age_ok = user_age >= scheme.min_age
            ration_ok = (scheme.allowed_ration_cards == 'ALL') or (scheme.allowed_ration_cards == user_card)
            category_ok = (scheme.category == 'ALL') or (scheme.category == user_cat)
            gender_ok = (scheme.allowed_gender == 'ALL') or (scheme.allowed_gender == user_gender)
            occupation_ok = (scheme.required_occupation == 'ALL') or (scheme.required_occupation == user_occ)
            marital_ok = (scheme.allowed_marital_status == 'ALL') or (scheme.allowed_marital_status == user_marital)

            if scheme.is_for_disabled_only:
                disabled_ok = profile.is_differently_abled
            else:
                disabled_ok = True

            if income_ok and age_ok and ration_ok and category_ok and gender_ok and occupation_ok and disabled_ok and marital_ok:
                scheme.is_applied = scheme.id in applied_scheme_ids
                eligible_schemes.append(scheme)

    context = {
        'profile': profile,
        'eligible_schemes': eligible_schemes,
        'profile_complete': profile_complete,
    }
    return render(request, 'home.html', context)

# 4. User Submits Scheme Application
@login_required(login_url='login')
def apply_scheme(request, scheme_id):
    scheme = get_object_or_404(Scheme, id=scheme_id)
    existing = Application.objects.filter(user=request.user, scheme=scheme).first()
    if existing:
        messages.info(request, "You have already applied for this scheme.")
        return redirect('my_applications')

    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        extra_data = {}
        if scheme.extra_fields:
            fields_list = [f.strip() for f in scheme.extra_fields.split(',') if f.strip()]
            for field_name in fields_list:
                extra_data[field_name] = request.POST.get(field_name, "")

        app = Application.objects.create(
            user=request.user,
            scheme=scheme,
            phone_number=phone,
            form_data=extra_data,
            status='PENDING_VERIFICATION'
        )

        files = request.FILES.getlist('documents')
        for uploaded_file in files:
            ApplicationDocument.objects.create(
                application=app,
                document_name=uploaded_file.name,
                file=uploaded_file
            )

        messages.success(request, f"Application submitted! Tracking ID: {app.application_id}. Awaiting Verification.")
        return redirect('my_applications')

    required_docs_list = [d.strip() for d in scheme.required_documents.split(',') if d.strip()] if scheme.required_documents else []
    extra_fields_list = [f.strip() for f in scheme.extra_fields.split(',') if f.strip()] if scheme.extra_fields else []

    context = {
        'scheme': scheme,
        'required_docs_list': required_docs_list,
        'extra_fields_list': extra_fields_list
    }
    return render(request, 'apply_scheme.html', context)

# 5. User Applications List
@login_required(login_url='login')
def my_applications(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_date')
    return render(request, 'my_applications.html', {'applications': applications})

# 6. User Re-uploads Documents
@login_required(login_url='login')
def reupload_docs(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)
    if request.method == 'POST':
        files = request.FILES.getlist('documents')
        if files:
            app.documents.all().delete()
            for uploaded_file in files:
                ApplicationDocument.objects.create(
                    application=app,
                    document_name=uploaded_file.name,
                    file=uploaded_file
                )
            app.status = 'PENDING_VERIFICATION'
            app.rejection_reason = ""
            app.save()
            messages.success(request, "Documents uploaded again. Under review by Akshaya Staff.")
            return redirect('my_applications')
    return render(request, 'reupload_docs.html', {'app': app})

# 7. User Selects Date & Books Token
@login_required(login_url='login')
def book_token(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)
    
    # സ്റ്റാഫ് ഡോക്യുമെന്റുകൾ പരിശോധിച്ചു അപ്രൂവ് ആക്കിയാൽ മാത്രം ടോക്കൺ ബുക്ക് ചെയ്യാൻ അനുവദിക്കുന്നു
    if app.status not in ['DOCS_APPROVED', 'Under Verification', 'Submitted']:
        messages.error(request, "Documents must be approved by staff before booking a token.")
        return redirect('my_applications')

    if request.method == 'POST':
        selected_date = request.POST.get('appointment_date')
        if selected_date:
            last_token = Application.objects.filter(appointment_date=selected_date).aggregate(Max('token_number'))['token_number__max']
            new_token = (last_token or 0) + 1

            app.appointment_date = selected_date
            app.token_number = new_token
            app.status = 'TOKEN_BOOKED'
            app.save()

            messages.success(request, f"Token #{new_token} booked for {selected_date}!")
            return redirect('live_queue', app_id=app.id)

    return render(request, 'book_token.html', {'app': app})

# 8. User Tracks Live Counter Status
@login_required(login_url='login')
def live_queue(request, app_id):
    user_app = get_object_or_404(Application, id=app_id, user=request.user)
    if not user_app.appointment_date:
        return redirect('my_applications')

    today = datetime.date.today()
    current_serving = Application.objects.filter(
        appointment_date=user_app.appointment_date,
        status='IN_PROGRESS'
    ).first()

    ahead_count = Application.objects.filter(
        appointment_date=user_app.appointment_date,
        status='TOKEN_BOOKED',
        token_number__lt=user_app.token_number
    ).count()

    context = {
        'app': user_app,
        'current_serving': current_serving,
        'ahead_count': ahead_count,
        'is_today': user_app.appointment_date == today
    }
    return render(request, 'live_queue.html', context)

# ----------------- STAFF VIEWS -----------------

# 9. Akshaya Staff Dashboard
@login_required(login_url='login')
@user_passes_test(is_staff_user)
def staff_dashboard(request):
    status_filter = request.GET.get('status', 'PENDING_VERIFICATION')
    applications = Application.objects.filter(status=status_filter).order_by('-applied_date')
    return render(request, 'staff_dashboard.html', {
        'applications': applications,
        'selected_status': status_filter
    })

# 10. Staff Document Verification Page
@login_required(login_url='login')
@user_passes_test(is_staff_user)
def staff_verify_docs(request, app_id):
    # prefetch_related ഉപയോഗിച്ച് അപ്‌ലോഡ് ചെയ്ത ഫയലുകൾ കൃത്യമായി എടുക്കുന്നു
    app = get_object_or_404(Application.objects.prefetch_related('documents'), id=app_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            app.status = 'DOCS_APPROVED'
            app.rejection_reason = ""
            messages.success(request, f"Documents for Application approved. User can now book a token.")
        elif action == 'reject':
            app.status = 'REJECTED_DOCS'
            app.rejection_reason = request.POST.get('rejection_reason', 'Documents unclear or incomplete.')
            messages.warning(request, f"Application marked as rejected.")
        
        app.staff_remarks = request.POST.get('staff_remarks', '')
        app.save()
        return redirect('staff_dashboard')

    return render(request, 'staff_verify_docs.html', {'app': app})

# 11. Staff Counter Management
@login_required(login_url='login')
@user_passes_test(is_staff_user)
def staff_counter_process(request):
    today = datetime.date.today()
    waiting_apps = Application.objects.filter(appointment_date=today, status='TOKEN_BOOKED').order_by('token_number')
    current_app = Application.objects.filter(appointment_date=today, status='IN_PROGRESS').first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'call_next':
            next_app = waiting_apps.first()
            if next_app:
                if current_app:
                    current_app.status = 'TOKEN_BOOKED'
                    current_app.save()
                next_app.status = 'IN_PROGRESS'
                next_app.save()
            return redirect('staff_counter_process')

        elif action == 'forward_to_govt':
            app_id = request.POST.get('app_id')
            app = get_object_or_404(Application, id=app_id)
            app.govt_ref_number = request.POST.get('govt_ref_number')
            app.staff_remarks = request.POST.get('staff_remarks')
            app.status = 'FORWARDED_TO_GOVT'
            app.save()
            messages.success(request, f"Application forwarded to Government Portal.")
            return redirect('staff_counter_process')

    return render(request, 'staff_counter.html', {
        'waiting_apps': waiting_apps,
        'current_app': current_app
    })

# 12. Process Individual Application
@login_required(login_url='login')
@user_passes_test(is_staff_user)
def process_application(request, app_id):
    # prefetch_related('documents') വഴി അപ്‌ലോഡ് ചെയ്ത എല്ലാ ഫയലുകളും എളുപ്പത്തിൽ കാണാൻ സഹായിക്കും
    app = get_object_or_404(Application.objects.prefetch_related('documents'), id=app_id)
    
    if request.method == 'POST':
        status = request.POST.get('status')
        remarks = request.POST.get('remarks') or request.POST.get('staff_remarks', '')
        govt_ref = request.POST.get('govt_ref_number', getattr(app, 'govt_ref_number', ''))

        if status:
            app.status = status
            app.staff_remarks = remarks
            if hasattr(app, 'govt_ref_number'):
                app.govt_ref_number = govt_ref
            app.save()
            messages.success(request, f"Application updated successfully.")
            return redirect('staff_dashboard')
            
    return render(request, 'process_application.html', {'app': app})