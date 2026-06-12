from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Lead, Referral, Transaction, BankAccount, Payout, DealSubmission

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'role', 'company_name', 'referral_code', 'is_approved', 'created_at')
    list_filter = ('role', 'is_approved')
    search_fields = ('email', 'company_name', 'referral_code')
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
