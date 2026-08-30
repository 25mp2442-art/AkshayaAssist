from django.contrib import admin
from .models import UserProfile, Scheme, Application, ApplicationDocument

# 1. അപേക്ഷയ്ക്കൊപ്പം അപ്‌ലോഡ് ചെയ്ത ഫയലുകൾ ഒന്നിച്ച് കാണിക്കാൻ
class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 1

# 2. അപേക്ഷകൾ കാണാനുള്ള അഡ്മിൻ വ്യൂ
from django.contrib import admin
from .models import UserProfile, Scheme, Application, ApplicationDocument

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    # 'user' എന്നതിന് പകരം 'application_id', 'status', 'phone_number' തുടങ്ങിയ ഫീൽഡുകൾ നൽകുക
    list_display = ('application_id', 'get_username', 'scheme', 'status', 'appointment_date', 'token_number')
    list_filter = ('status', 'appointment_date', 'scheme')
    search_fields = ('application_id', 'user__username', 'phone_number')

    # Username അഡ്മിൻ പാനലിൽ ഭംഗിയായി കാണിക്കാൻ ഒരു ഹെൽപ്പർ ഫംഗ്ഷൻ:
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Applicant'

# ബാക്കി മോഡലുകൾ റെജിസ്റ്റർ ചെയ്യാൻ:
admin.site.register(UserProfile)
admin.site.register(Scheme)
admin.site.register(ApplicationDocument)
