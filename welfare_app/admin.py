from django.contrib import admin
from .models import UserProfile, Scheme, Application, ApplicationDocument

# 1. അപേക്ഷയ്ക്കൊപ്പം അപ്‌ലോഡ് ചെയ്ത ഫയലുകൾ ഒന്നിച്ച് കാണിക്കാൻ
class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 1

# 2. അപേക്ഷകൾ കാണാനുള്ള അഡ്മിൻ വ്യൂ
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('token_number', 'user', 'scheme', 'status', 'applied_date')
    inlines = [ApplicationDocumentInline] # ഡോക്യുമെന്റുകൾ ഇതിനുള്ളിൽ ലിസ്റ്റ് ചെയ്യും

# 3. നിങ്ങൾ നേരത്തെ രജിസ്റ്റർ ചെയ്ത മോഡലുകൾ
admin.site.register(UserProfile)
admin.site.register(Scheme)