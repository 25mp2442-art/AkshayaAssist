from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserProfileForm
from .models import UserProfile, Scheme

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

# 2. Login View
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
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
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('home')  # Home/Dashboard-ലേക്ക് തിരികെ പോകുന്നു
    else:
        form = UserProfileForm(instance=profile)
        
    return render(request, 'profile_setup.html', {'form': form})

# 5. Dashboard / Home View with Scheme Matching Logic
@login_required(login_url='login')
def home(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    eligible_schemes = []
    profile_complete = False

    # യൂസർ നേരത്തെ അപ്ലൈ ചെയ്ത സ്കീം ID-കൾ എടുക്കുന്നു
    applied_scheme_ids = Application.objects.filter(user=request.user).values_list('scheme_id', flat=True)

    if profile.annual_income is not None and profile.ration_card_type and profile.category:
        profile_complete = True
        all_schemes = Scheme.objects.all()
        
        for scheme in all_schemes:
            income_ok = profile.annual_income <= scheme.max_income_limit
            ration_ok = (scheme.allowed_ration_card == 'ALL') or (scheme.allowed_ration_card == profile.ration_card_type)
            category_ok = (scheme.allowed_category == 'ALL') or (scheme.allowed_category == profile.category)
            
            if income_ok and ration_ok and category_ok:
                # യൂസർ അപ്ലൈ ചെയ്തിട്ടുണ്ടോ എന്ന് ഫ്ലാഗ് വെക്കുന്നു
                scheme.is_applied = scheme.id in applied_scheme_ids
                eligible_schemes.append(scheme)

    context = {
        'profile': profile,
        'eligible_schemes': eligible_schemes,
        'profile_complete': profile_complete,
    }
    return render(request, 'home.html', context)

from .models import UserProfile, Scheme, Application

@login_required(login_url='login')
def apply_scheme(request, scheme_id):
    scheme = Scheme.objects.get(id=scheme_id)
    # നേരത്തെ അപ്ലൈ ചെയ്തിട്ടുണ്ടോ എന്ന് നോക്കുന്നു
    already_applied = Application.objects.filter(user=request.user, scheme=scheme).exists()
    
    if not already_applied:
        Application.objects.create(user=request.user, scheme=scheme)
        messages.success(request, f'Successfully applied for {scheme.title}!')
    else:
        messages.warning(request, 'You have already applied for this scheme.')
        
    return redirect('my_applications')

@login_required(login_url='login')
def my_applications(request):
    applications = Application.objects.filter(user=request.user).order_by('-applied_date')
    return render(request, 'my_applications.html', {'applications': applications})

from django.contrib.admin.views.decorators import staff_member_required

# 1. അക്ഷയ സ്റ്റാഫിനുള്ള ഡാഷ്‌ബോർഡ് View
@staff_member_required(login_url='login')
def staff_dashboard(request):
    applications = Application.objects.all().order_by('-applied_date')
    return render(request, 'staff_dashboard.html', {'applications': applications})

# 2. അപേക്ഷയുടെ സ്റ്റാറ്റസ് മാറ്റാനുള്ള View (Approve / Reject)
@staff_member_required(login_url='login')
def update_application_status(request, app_id, status):
    application = Application.objects.get(id=app_id)
    application.status = status
    application.save()
    messages.success(request, f"Application for {application.user.username} has been {status}!")
    return redirect('staff_dashboard')