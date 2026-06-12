from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid


class User(AbstractUser):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('partner', 'Partner'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='partner')
    company_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals')
    is_approved = models.BooleanField(default=True)
    ppl_rate = models.DecimalField(max_digits=7, decimal_places=2, default=100.00)  # $ per qualified lead
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = uuid.uuid4().hex[:8].upper()
        if self.email == 'shakil@atlasfundcapital.com':
            self.role = 'superadmin'
            self.is_superuser = True
            self.is_staff = True
        super().save(*args, **kwargs)

    def wallet_balance(self):
        total = self.transactions.filter(transaction_type='credit').aggregate(s=models.Sum('amount'))['s'] or 0
        debits = self.transactions.filter(transaction_type='debit').aggregate(s=models.Sum('amount'))['s'] or 0
        return total - debits

    def __str__(self):
        return f"{self.get_full_name() or self.email}"


class Lead(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('qualified', 'Qualified'),
        ('non_qualified', 'Non Qualified'),
        ('archived', 'Archived'),
    ]
    funding_amount = models.CharField(max_length=100)
    monthly_revenue = models.CharField(max_length=100)
    credit_score = models.CharField(max_length=50)
    time_in_business = models.CharField(max_length=50)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    company_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    consent = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=20, default='direct', choices=[
        ('direct', 'Direct'),
        ('referral', 'Referral'),
        ('partner_submitted', 'Partner Submitted'),
    ])
    referred_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='referred_leads')
    referral_code_used = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']


class AppSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=500)
    description = models.CharField(max_length=300, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.key} = {self.value}"

    @classmethod
    def get(cls, key, default=None):
        obj = cls.objects.filter(key=key).first()
        return obj.value if obj else default

    @classmethod
    def set(cls, key, value, description=''):
        obj, _ = cls.objects.update_or_create(key=key, defaults={'value': str(value), 'description': description})
        return obj

    @classmethod
    def get_ppl(cls):
        return float(cls.get('default_ppl_rate', 100))

    @classmethod
    def get_min_payout(cls):
        return float(cls.get('min_payout_amount', 500))

    def __str__(self):
        return f"{self.full_name} - {self.company_name} ({self.status})"

    @property
    def revenue_numeric(self):
        rev = self.monthly_revenue.lower().replace('$', '').replace(',', '').strip()
        try:
            if 'k' in rev:
                return float(rev.replace('k', '')) * 1000
            return float(rev) if rev else 0
        except:
            return 0

    @property
    def is_business_qualified(self):
        try:
            score = int(''.join(filter(str.isdigit, self.credit_score)))
            time_map = {'0-6': 0, '6-12': 6, '1-2': 12, '2-5': 24, '5-plus': 60}
            months = time_map.get(self.time_in_business, 0)
            return self.revenue_numeric >= 25000 and months >= 12 and score >= 500
        except:
            return False


class Referral(models.Model):
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='referral_tracking')
    visitor_ip = models.GenericIPAddressField(null=True, blank=True)
    visitor_agent = models.TextField(blank=True)
    referral_code = models.CharField(max_length=20)
    converted = models.BooleanField(default=False)
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class Transaction(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    description = models.CharField(max_length=500)
    lead = models.ForeignKey(Lead, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} ${self.amount} - {self.partner.email}"


class BankAccount(models.Model):
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bank_accounts')
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    routing_number = models.CharField(max_length=50)
    account_type = models.CharField(max_length=20, choices=[('checking', 'Checking'), ('savings', 'Savings')])
    is_verified = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number[-4:]}"


class Payout(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ]
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    bank_account = models.ForeignKey(BankAccount, null=True, on_delete=models.SET_NULL)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']


class DealSubmission(models.Model):
    partner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deal_submissions')
    funding_amount = models.CharField(max_length=100)
    monthly_revenue = models.CharField(max_length=100)
    credit_score = models.CharField(max_length=50)
    time_in_business = models.CharField(max_length=50)
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    company_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=30)
    notes = models.TextField(blank=True)
    deal_size = models.CharField(max_length=100, blank=True)
    is_pay_per_close = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='submitted', choices=[
        ('submitted', 'Submitted'),
        ('reviewing', 'Reviewing'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ])
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_deals')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
