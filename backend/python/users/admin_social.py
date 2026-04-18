from django.contrib import admin
from allauth.socialaccount.models import SocialApp, SocialAccount, SocialToken
from allauth.socialaccount.providers.google.provider import GoogleProvider


@admin.register(SocialApp)
class SocialAppAdmin(admin.ModelAdmin):
    list_display = ('provider', 'name', 'client_id', 'created_at')
    list_filter = ('provider', 'created_at')
    search_fields = ('name', 'client_id')
    readonly_fields = ('created_at', 'modified_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('provider', 'name', 'client_id')
        }),
        ('Credentials', {
            'fields': ('secret', 'key'),
            'classes': ('collapse',)
        }),
        ('Settings', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'modified_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(provider='google')
        return qs


@admin.register(SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'uid', 'date_joined', 'last_login')
    list_filter = ('provider', 'date_joined', 'last_login')
    search_fields = ('user__username', 'user__email', 'uid')
    readonly_fields = ('uid', 'extra_data', 'date_joined', 'last_login')
    
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'provider', 'uid')
        }),
        ('Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(user=request.user)
        return qs


@admin.register(SocialToken)
class SocialTokenAdmin(admin.ModelAdmin):
    list_display = ('app', 'account', 'token', 'expires_at')
    list_filter = ('app', 'expires_at')
    search_fields = ('account__user__username', 'account__user__email', 'token')
    readonly_fields = ('token', 'token_secret', 'expires_at', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Token Information', {
            'fields': ('app', 'account', 'token', 'token_secret')
        }),
        ('Expiry', {
            'fields': ('expires_at',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            qs = qs.filter(account__user=request.user)
        return qs


# Custom admin site configuration for social authentication
class SocialAuthAdminSite(admin.AdminSite):
    site_header = 'Instagran Social Authentication'
    site_title = 'Social Auth Admin'
    index_title = 'Social Authentication'
    
    def has_permission(self, request):
        return request.user.is_authenticated and (
            request.user.is_superuser or 
            request.user.has_perm('socialaccount.change_socialapp')
        )


# Create custom admin site instance
social_auth_admin = SocialAuthAdminSite(name='social_auth_admin')


# Register models with custom admin site
social_auth_admin.register(SocialApp, SocialAppAdmin)
social_auth_admin.register(SocialAccount, SocialAccountAdmin)
social_auth_admin.register(SocialToken, SocialTokenAdmin)
