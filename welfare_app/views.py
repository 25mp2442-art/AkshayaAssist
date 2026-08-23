from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages

from .forms import UserProfileForm
from .models import UserProfile, Scheme, Application


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
        
        # 💍 1. Marital Status Save ചെയ്യുന്നു
        profile.marital_status = request.POST.get('marital_status')
        
        # ♿ Disability Data Saving
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
        user_marital = (profile.marital_status or "").strip() # 💍 Marital Status എടുക്കുന്നു
        user_age = profile.age or 0

        for scheme in all_schemes:
            income_ok = user_income <= scheme.max_income
            age_ok = user_age >= scheme.min_age
            ration_ok = (scheme.allowed_ration_cards == 'ALL') or (scheme.allowed_ration_cards == user_card)
            category_ok = (scheme.category == 'ALL') or (scheme.category == user_cat)
            gender_ok = (scheme.allowed_gender == 'ALL') or (scheme.allowed_gender == user_gender)
            occupation_ok = (scheme.required_occupation == 'ALL') or (scheme.required_occupation == user_occ)
            
            # 💍 2. Marital Status ഫിൽട്ടറിംഗ് നിബന്ധന
            marital_ok = (scheme.allowed_marital_status == 'ALL') or (scheme.allowed_marital_status == user_marital)
            
            # ♿ 3. ഭിന്നശേഷി സ്കീം ചെക്കിംഗ്
            disabled_ok = True
            if scheme.is_for_disabled_only:
                disabled_ok = profile.is_differently_abled

            # 💍 marital_ok കൂടി ഇവിടെ നിർബന്ധമാക്കുന്നു
            if income_ok and age_ok and ration_ok and category_ok and gender_ok and occupation_ok and disabled_ok and marital_ok:
                scheme.is_applied = scheme.id in applied_scheme_ids
                eligible_schemes.append(scheme)

    context = {
        'profile': profile,
        'eligible_schemes': eligible_schemes,
        'profile_complete': profile_complete,
    }
    return render(request, 'home.html', context)


@login_required(login_url='login')
def apply_scheme(request, scheme_id):
    scheme = get_object_or_404(Scheme, id=scheme_id)
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    existing = Application.objects.filter(user=request.user, scheme=scheme).first()
    if existing:
        messages.info(request, "You have already applied for this scheme.")
        return redirect('my_applications')

    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        doc = request.FILES.get('document')

        # 📝 extra_fields dynamic values (JSON ആയി സേവ് ചെയ്യുന്നു)
        extra_data = {}
        if scheme.extra_fields:
            fields_list = [f.strip() for f in scheme.extra_fields.split(',') if f.strip()]
            for field_name in fields_list:
                extra_data[field_name] = request.POST.get(field_name, '')

        app = Application.objects.create(
            user=request.user,
            scheme=scheme,
            phone_number=phone,
            document=doc,
            form_data=extra_data
        )
        messages.success(request, f"Application submitted! Your Token Number is {app.token_number}")
        return redirect('my_applications')

    # required_documents split ചെയ്ത് ലിസ്റ്റ് ആക്കുന്നു
    required_docs_list = [d.strip() for d in scheme.required_documents.split(',') if d.strip()]
    extra_fields_list = [f.strip() for f in scheme.extra_fields.split(',') if f.strip()] if scheme.extra_fields else []

    context = {
        'scheme': scheme, 
        'profile': profile,
        'required_docs_list': required_docs_list,
        'extra_fields_list': extra_fields_list
    }
    return render(request, 'apply_scheme.html', context)


@login_required(login_url='login')
def my_applications(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_date')
    return render(request, 'my_applications.html', {'applications': applications})


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


@login_required(login_url='login')
@user_passes_test(is_staff_user)
def process_application(request, app_id):
    app = get_object_or_404(Application, id=app_id)

    if request.method == 'POST':
        app.status = request.POST.get('status')
        app.staff_remarks = request.POST.get('remarks')
        
        if request.FILES.get('document'):
            app.document = request.FILES['document']

        app.save()
        messages.success(request, f"Application #{app.id} updated successfully.")
        return redirect('staff_dashboard')

    return render(request, 'process_application.html', {'app': app})