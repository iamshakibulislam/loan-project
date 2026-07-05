from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Lead, Referral, Transaction, BankAccount, Payout, DealSubmission, BlogPost, Contact, BrandMention

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'role', 'company_name', 'referral_code', 'is_approved', 'created_at')
    list_filter = ('role', 'is_approved')
    search_fields = ('email', 'company_name', 'referral_code')
    ordering = ('-created_at',)


@admin.register(BrandMention)
class BrandMentionAdmin(admin.ModelAdmin):
    list_display = ('title', 'url', 'created_at')
    search_fields = ('title', 'url')
    ordering = ('-created_at',)
    fieldsets = UserAdmin.fieldsets + (('Partner Info', {'fields': ('role', 'company_name', 'phone', 'referral_code', 'referred_by', 'is_approved')}),)

@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'company_name', 'email', 'status', 'referred_by', 'source', 'created_at')
    list_filter = ('status', 'source')
    search_fields = ('full_name', 'email', 'company_name', 'phone')

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('partner', 'referral_code', 'converted', 'created_at')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('partner', 'amount', 'transaction_type', 'description', 'created_at')

@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = ('partner', 'bank_name', 'account_type', 'is_verified')

@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('partner', 'amount', 'status', 'created_at')

@admin.register(DealSubmission)
class DealSubmissionAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'company_name', 'partner', 'status', 'is_pay_per_close', 'created_at')


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'published_at', 'read_time', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'excerpt', 'content')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-published_at', '-created_at')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'phone', 'subject', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'message', 'subject')
    list_filter = ('subject',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
