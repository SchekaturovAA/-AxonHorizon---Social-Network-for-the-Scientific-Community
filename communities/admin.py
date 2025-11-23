from django.contrib import admin
from .models import Community, CommunityMembership

@admin.register(Community)
class CommunityAdmin(admin.ModelAdmin):
    list_display = ('name', 'scientific_field', 'created_by', 'created_at')
    list_filter = ('scientific_field', 'created_at')
    search_fields = ('name', 'description')

@admin.register(CommunityMembership)
class CommunityMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'community', 'date_joined', 'is_moderator')
    list_filter = ('is_moderator', 'date_joined')
