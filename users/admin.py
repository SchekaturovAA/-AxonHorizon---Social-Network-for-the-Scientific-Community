from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Profile, ScientificField


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_researcher', 'is_verified', 'date_joined', 'is_staff')
    list_filter = ('is_researcher', 'is_verified', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'orcid_id')
    inlines = (ProfileInline,)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'orcid_id')}),
        ('Permissions', {'fields': (
        'is_researcher', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_researcher', 'is_verified'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'institution', 'location','phone', 'citations_count', 'h_index', 'created_at')
    list_filter = ('institution','location', 'created_at')
    search_fields = ('user__username', 'institution','location','phone', 'bio')
    filter_horizontal = ('scientific_fields',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'avatar', 'bio', 'scientific_fields')
        }),
        ('Контактная информация', {
            'fields': ('institution', 'location', 'phone', 'website')
        }),
        ('Профессиональная информация', {
            'fields': ('research_interests', 'education')
        }),
        ('Научные метрики', {
            'fields': ('citations_count', 'h_index')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ScientificField)
class ScientificFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')