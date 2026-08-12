from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import UserProfileForm
from .models import UserProfile, Scheme, Application

# Helper Check for Staff / Superuser
def is_staff_user(user):
    return user.is_staff or user.is_superuser


# 1. Registration View
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


# 2. Login View (Role-Based Redirection)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            
            # 1. അഡ്മിൻ ആണെങ്കിൽ Django Admin Panel-ലേക്ക്
            if user.is_superuser:
                return redirect('/admin/')
            
            # 2. അക്ഷയ സ്റ്റാഫ് ആണെങ്കിൽ Staff Dashboard-ലേക്ക്
            elif user.is_staff:
                return redirect('staff_dashboard')
            
            # 3. സാധാരണ സിറ്റിസൺ ആണെങ്കിൽ Home-ലേക്ക്
            else:
                return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})


# 3. Logout View
def logout_view(request):
    auth_logout(request)
    return redirect('login')


# 4. Profile Setup View
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
        
        profile.save()
        return redirect('home')

    return render(request, 'profile_setup.html', {'profile': profile})


# 5. Dashboard / Home View with Scheme Matching Logic
@login_required(login_url='login')
def home(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    eligible_schemes = []
    profile_complete = False

    applied_scheme_ids = Application.objects.filter(user=request.user).values_list('scheme_id', flat=True)

    if (profile.annual_income is not None and 
        profile.ration_card_type and 
        profile.category and 
        profile.gender):
        
        profile_complete = True
        all_schemes = Scheme.objects.all()

        user_income = float(profile.annual_income)
        user_card = profile.ration_card_type.strip()
        user_cat = profile.category.strip()
        user_gender = profile.gender.strip()
        user_occ = profile.occupation.strip() if profile.occupation else ""
        user_age = profile.age or 0

        for scheme in all_schemes:
            income_ok = user_income <= scheme.max_income
            age_ok = user_age >= scheme.min_age
            ration_ok = (scheme.allowed_ration_cards == 'ALL') or (scheme.allowed_ration_cards == user_card)
            category_ok = (scheme.category == 'ALL') or (scheme.category == user_cat)
            gender_ok = (scheme.allowed_gender == 'ALL') or (scheme.allowed_gender == user_gender)
            occupation_ok = (scheme.required_occupation == 'ALL') or (scheme.required_occupation == user_occ)

            if income_ok and age_ok and ration_ok and category_ok and gender_ok and occupation_ok:
                scheme.is_applied = scheme.id in applied_scheme_ids
                eligible_schemes.append(scheme)

    context = {
        'profile': profile,
        'eligible_schemes': eligible_schemes,
        'profile_complete': profile_complete,
    }
    return render(request, 'home.html', context)


# 6. Apply Scheme View (For Citizen Document Upload)
@login_required(login_url='login')
def apply_scheme(request, scheme_id):
    scheme = get_object_or_404(Scheme, id=scheme_id)
    profile = UserProfile.objects.get(user=request.user)

    existing = Application.objects.filter(user=request.user, scheme=scheme).first()
    if existing:
        return redirect('my_applications')

    if request.method == 'POST':
        phone = request.POST.get('phone_number')
        doc = request.FILES.get('document')

        app = Application.objects.create(
            user=request.user,
            scheme=scheme,
            phone_number=phone,
            document=doc
        )
        messages.success(request, f"Application submitted! Your Token Number is {app.token_number}")
        return redirect('my_applications')

    context = {'scheme': scheme, 'profile': profile}
    return render(request, 'apply_scheme.html', context)


# 7. Citizen Applications List View
@login_required(login_url='login')
def my_applications(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_date')
    return render(request, 'my_applications.html', {'applications': applications})


# 8. Akshaya Staff Dashboard View
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


# 9. Akshaya Staff Processing & Form Filling View
from django.shortcuts import render, redirect, get_object_or_404
from .models import Application  # നിങ്ങളുടെ മോഡലിന്റെ പേര്

def process_application(request, app_id):
    # Application കണ്ടെത്തുക
    app = get_object_or_404(Application, id=app_id) # അല്ലെങ്കിൽ നിങ്ങളുടെ ID ഫീൽഡ് അനുസരിച്ച്

    if request.method == 'POST':
        # ഫോമിൽ നിന്ന് വാല്യൂസ് എടുക്കുന്നു
        app.status = request.POST.get('status')
        app.remarks = request.POST.get('remarks')
        
        # അക്ഷയ സ്റ്റാഫ് ഫിൽ ചെയ്യുന്ന വിവരങ്ങൾ
        app.applicant_name = request.POST.get('applicant_name')
        app.id_number = request.POST.get('id_number') # എധാർ/റേഷൻ കാർഡ് നമ്പർ പോലെ
        app.income = request.POST.get('income')
        
        # ഫയലുകൾ അല്ലെങ്കിൽ ഡോക്യുമെന്റ്സ് ഉണ്ടെങ്കിൽ
        if request.FILES.get('document'):
            app.document = request.FILES['document']

        app.save()
        return redirect('staff_dashboard') # അല്ലെങ്കിൽ നിങ്ങളുടേതായ വിജയകരമായ റീഡയറക്ട് URL

    return render(request, 'process_application.html', {'app': app})