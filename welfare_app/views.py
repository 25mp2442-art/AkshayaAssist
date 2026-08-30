import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Max

from .forms import UserProfileForm
from .models import UserProfile, Scheme, Application, ApplicationDocument


def is_staff_user(user):
    return user.is_staff or user.is_superuser


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


@login_required(login_url='login')
def home(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    eligible_schemes = []
    profile_complete = False

    applied_scheme_ids = set(
        Application.objects.filter(user=request.user).values_list('scheme_id', flat=True)
    )

    if (profile.annual_income is not None and 
        profile.ration_card_type and 
        profile.category and 
        profile.gender):
        
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
            
            disabled_ok = True
            if scheme.is_for_disabled_only:
                disabled_ok = profile.is_differently_abled

            if income_ok and age_ok and ration_ok and category_ok and gender_ok and occupation_ok and disabled_ok and marital_ok:
                scheme.is_applied = scheme.id in applied_scheme_ids
                eligible_schemes.append(scheme)

    context = {
        'profile': profile,
        'eligible_schemes': eligible_schemes,
        'profile_complete': profile_complete,
    }
    return render(request, 'home.html', context)


# 1. അപേക്ഷ സമർപ്പിക്കുന്നു (സ്റ്റാറ്റസ്: PENDING_VERIFICATION)
@login_required
def apply_scheme(request, scheme_id):
    scheme = get_object_or_404(Scheme, id=scheme_id)

    # Dynamic comma separated list എടുക്കുന്നു
    extra_fields_list = [f.strip() for f in scheme.extra_fields.split(',') if f.strip()]
    required_docs_list = [d.strip() for d in scheme.required_documents.split(',') if d.strip()]

    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')

        # Extra Fields JSON ആയി സൂക്ഷിക്കുന്നു
        form_data = {}
        for field_name in extra_fields_list:
            form_data[field_name] = request.POST.get(field_name, '')

        # Application ക്രിയേറ്റ് ചെയ്യൽ
        application = Application.objects.create(
            user=request.user,
            scheme=scheme,
            phone_number=phone_number,
            form_data=form_data
        )

        # Multiple ഫയലുകൾ എടുത്ത് ApplicationDocument-ൽ ചേർക്കുന്നു
        files = request.FILES.getlist('documents')
        for uploaded_file in files:
            ApplicationDocument.objects.create(
                application=application,
                document_name=uploaded_file.name,
                file=uploaded_file
            )

        messages.success(request, 'Application submitted successfully!')
        return redirect('my_applications')

    return render(request, 'apply_scheme.html', {
        'scheme': scheme,
        'extra_fields_list': extra_fields_list,
        'required_docs_list': required_docs_list
    })


# 2. യൂസറുടെ ആപ്ലിക്കേഷൻ ലിസ്റ്റ്
@login_required(login_url='login')
def my_applications(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_date')
    return render(request, 'my_applications.html', {'applications': applications})


# 3. റിജക്ട് ആയ ഡോക്യുമെന്റുകൾ യൂസറിന് വീണ്ടും അപ്‌ലോഡ് ചെയ്യാൻ
@login_required(login_url='login')
def reupload_docs(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)

    if request.method == 'POST':
        files = request.FILES.getlist('documents')
        if files:
            # പഴയ ഫയലുകൾ നീക്കം ചെയ്തിട്ട് പുതിയത് നൽകാം
            app.documents.all().delete()
            for uploaded_file in files:
                ApplicationDocument.objects.create(
                    application=app,
                    document_name=uploaded_file.name,
                    file=uploaded_file
                )
            app.status = 'PENDING_VERIFICATION'
            app.staff_remarks = "Re-uploaded documents submitted. Awaiting verification."
            app.save()
            messages.success(request, "Documents re-uploaded successfully!")
            return redirect('my_applications')

    return render(request, 'reupload_docs.html', {'app': app})


# 4. അപ്രൂവ് ആയ അപേക്ഷകൾക്ക് യൂസർ ടോക്കൺ ബുക്ക് ചെയ്യുന്നു
@login_required(login_url='login')
def book_token(request, app_id):
    app = get_object_or_404(Application, id=app_id, user=request.user)

    if app.status != 'DOCS_APPROVED':
        messages.error(request, "Token booking is only allowed after document approval.")
        return redirect('my_applications')

    if request.method == 'POST':
        selected_date = request.POST.get('appointment_date')
        
        # ടോക്കൺ നമ്പർ അനുയോജ്യമായി കണ്ടുപിടിക്കുന്നു
        last_token = Application.objects.filter(appointment_date=selected_date).aggregate(Max('token_number'))['token_number__max']
        new_token = (last_token or 0) + 1

        app.appointment_date = selected_date
        app.token_number = new_token
        app.status = 'TOKEN_BOOKED'
        app.save()

        messages.success(request, f"Token #{new_token} successfully booked for {selected_date}!")
        return redirect('live_queue', app_id=app.id)

    return render(request, 'book_token.html', {'app': app})


# 5. ലൈവ് ക്യൂ ട്രാക്കിംഗ് (യൂസറിന് വേണ്ടി)
@login_required(login_url='login')
def live_queue(request, app_id):
    user_app = get_object_or_404(Application, id=app_id, user=request.user)

    if not user_app.appointment_date:
        return redirect('my_applications')

    current_serving = Application.objects.filter(
        appointment_date=user_app.appointment_date, 
        status='IN_PROGRESS'
    ).first()

    ahead_count = Application.objects.filter(
        appointment_date=user_app.appointment_date, 
        status='TOKEN_BOOKED', 
        token_number__lt=user_app.token_number
    ).count()

    return render(request, 'live_queue.html', {
        'app': user_app,
        'current_serving': current_serving,
        'ahead_count': ahead_count,
    })


# 6. അക്ഷയ സ്റ്റാഫ് ഡാഷ്‌ബോർഡ്
@login_required(login_url='login')
@user_passes_test(is_staff_user)
def staff_dashboard(request):
    status_filter = request.GET.get('status', '')
    if status_filter:
        applications = Application.objects.filter(status=status_filter).order_by('-applied_date')
    else:
        applications = Application.objects.all().order_by('-applied_date')

    return render(request, 'staff_dashboard.html', {
        'applications': applications,
        'selected_status': status_filter
    })


# 7. സ്റ്റാഫ് ഡോക്യുമെന്റുകൾ പരിശോധിച്ച് അപ്രൂവ്/റിജക്ട് ചെയ്യുന്നു
@login_required(login_url='login')
@user_passes_test(is_staff_user)
def process_application(request, app_id):
    app = get_object_or_404(Application, id=app_id)

    if request.method == 'POST':
        action = request.POST.get('action') # 'approve' or 'reject'
        
        if action == 'approve':
            app.status = 'DOCS_APPROVED'
            app.staff_remarks = request.POST.get('remarks', 'Documents verified and approved.')
        elif action == 'reject':
            app.status = 'REJECTED_DOCS'
            app.rejection_reason = request.POST.get('rejection_reason')
            app.staff_remarks = request.POST.get('remarks', 'Documents rejected.')
        
        app.save()

        files = request.FILES.getlist('documents')
        for uploaded_file in files:
            ApplicationDocument.objects.create(
                application=app,
                document_name=uploaded_file.name,
                file=uploaded_file
            )

        messages.success(request, f"Application #{app.application_id} processed successfully.")
        return redirect('staff_dashboard')

    return render(request, 'process_application.html', {'app': app})


# 8. കൗണ്ടർ ലൈവ് ഡാഷ്‌ബോർഡ് (ഗവൺമെന്റിലേക്ക് അയക്കാൻ)
@login_required(login_url='login')
@user_passes_test(is_staff_user)
def staff_counter(request):
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
            return redirect('staff_counter')

        elif action == 'forward_to_govt':
            app_id = request.POST.get('app_id')
            app = get_object_or_404(Application, id=app_id)
            app.govt_ref_number = request.POST.get('govt_ref_number')
            app.staff_remarks = request.POST.get('staff_remarks')
            app.status = 'FORWARDED_TO_GOVT'
            app.save()
            messages.success(request, f"Token #{app.token_number} successfully forwarded to Govt Portal.")
            return redirect('staff_counter')

    return render(request, 'staff_counter.html', {
        'waiting_apps': waiting_apps,
        'current_app': current_app
    })