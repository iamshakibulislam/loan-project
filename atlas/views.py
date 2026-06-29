import csv
import datetime
from io import StringIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import User, Lead, Referral, Transaction, BankAccount, Payout, DealSubmission, AppSettings, BlogPost, Contact, BrandMention


# ─── Helpers ──────────────────────────────────────────────────────────────────

def is_superadmin(user):
    return user.is_authenticated and user.role == 'superadmin'

def is_partner(user):
    return user.is_authenticated and user.role == 'partner'

def get_ref_code(request):
    return request.GET.get('ref') or request.COOKIES.get('atlas_ref', '')

def build_context(request, extra=None):
    ctx = {'user': request.user, 'now': now()}
    if extra:
        ctx.update(extra)
    return ctx

# ─── Public Pages ─────────────────────────────────────────────────────────────

def home(request):
    recent_posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')[:4]
    return render(request, 'index.html', {'recent_posts': recent_posts})

def about(request):
    return render(request, 'pages/about.html')

def how_it_works(request):
    return render(request, 'pages/how-it-works.html')

def faqs(request):
    return render(request, 'pages/faqs.html')

@csrf_exempt
def contact(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()
        if not first_name or not last_name or not email or not message_text:
            return JsonResponse({'success': False, 'error': 'Please fill in all required fields.'}, status=400)
        Contact.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            subject=subject or 'General Inquiry',
            message=message_text,
        )
        return JsonResponse({'success': True, 'message': 'Message received. We will respond within one business day.'})
    return render(request, 'pages/contact.html', build_context(request))

def blog(request):
    posts = BlogPost.objects.filter(is_published=True).order_by('-published_at')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    return render(request, 'pages/blog.html', build_context(request, {
        'posts': posts_page,
    }))


def blog_post_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    recent_posts = BlogPost.objects.filter(is_published=True).exclude(pk=post.pk).order_by('-published_at')[:6]
    return render(request, 'pages/blog-detail.html', build_context(request, {
        'post': post,
        'recent_posts': recent_posts,
    }))

def resources(request):
    mentions = BrandMention.objects.all().order_by('-created_at')
    paginator = Paginator(mentions, 12)
    page_number = request.GET.get('page', 1)
    mentions_page = paginator.get_page(page_number)
    return render(request, 'pages/resources.html', {
        'brand_mentions': mentions_page,
    })

def terms(request):
    return render(request, 'pages/terms.html')

def product_page(request, slug):
    templates = {
        'merchant-cash-advance': 'pages/merchant-cash-advance.html',
        'line-of-credit': 'pages/line-of-credit.html',
        'sba-loans': 'pages/sba-loans.html',
        'term-loans': 'pages/term-loans.html',
        'equipment-financing': 'pages/equipment-financing.html',
        'invoice-factoring': 'pages/invoice-factoring.html',
        'business-acquisition': 'pages/business-acquisition.html',
    }
    template = templates.get(slug, 'pages/404.html')
    return render(request, template)

def partner_detail(request):
    return render(request, 'pages/partner-detail.html')


# ─── Lead Submission (Homepage Form + Referral Form) ───────────────────────────

@require_POST
@csrf_exempt
def submit_lead(request):
    data = {
        'funding_amount': request.POST.get('funding_amount', ''),
        'monthly_revenue': request.POST.get('monthly_revenue', ''),
        'credit_score': request.POST.get('credit_score', ''),
        'time_in_business': request.POST.get('time_in_business', ''),
        'full_name': request.POST.get('full_name', ''),
        'email': request.POST.get('email', ''),
        'company_name': request.POST.get('company_name', ''),
        'phone': request.POST.get('phone', ''),
        'consent': request.POST.get('consent') == 'on',
    }
    if not data['full_name'] or not data['email']:
        return JsonResponse({'success': False, 'error': 'Required fields missing.'}, status=400)

    ref_code = get_ref_code(request)
    referred_by = None
    source = 'direct'
    if ref_code:
        try:
            referred_by = User.objects.get(referral_code=ref_code, role='partner')
            source = 'referral'
        except User.DoesNotExist:
            pass

    lead = Lead.objects.create(**data, source=source, referred_by=referred_by, referral_code_used=ref_code)

    if referred_by:
        Referral.objects.create(
            partner=referred_by,
            referral_code=ref_code,
            converted=True,
            lead=lead,
            visitor_ip=request.META.get('REMOTE_ADDR', ''),
            visitor_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

    return JsonResponse({'success': True, 'message': 'Lead submitted successfully.'})


# ─── Authentication ──────────────────────────────────────────────────────────

def partner_signup(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm = request.POST.get('confirm_password', '')
        full_name = request.POST.get('full_name', '')
        company = request.POST.get('company_name', '')

        if password != confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'pages/partner-signup.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'An account with this email already exists.')
            return render(request, 'pages/partner-signup.html')

        ref_code = get_ref_code(request)
        referred_by = None
        if ref_code:
            try:
                referred_by = User.objects.get(referral_code=ref_code, role='partner')
            except User.DoesNotExist:
                pass

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=full_name,
            company_name=company,
            role='partner',
            referred_by=referred_by,
        )
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        messages.success(request, 'Welcome! Your partner account has been created.')
        return redirect('partner_dashboard')

    return render(request, 'pages/partner-signup.html')


def partner_login(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=email, password=password)
        if user and user.role in ('partner', 'superadmin'):
            login(request, user)
            nxt = request.GET.get('next', '')
            if nxt:
                return redirect(nxt)
            return redirect('partner_dashboard')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'pages/partner-login.html')


def partner_logout(request):
    logout(request)
    return redirect('/')


# ─── Partner Dashboard ────────────────────────────────────────────────────────

@login_required
@user_passes_test(lambda u: u.role in ('partner', 'superadmin'), login_url='/partner/login/')
def partner_dashboard(request):
    if is_superadmin(request.user):
        return redirect('superadmin_dashboard')

    partner = request.user
    leads = Lead.objects.filter(referred_by=partner).order_by('-created_at')
    total_leads = leads.count()
    qualified = leads.filter(status='qualified').count()
    pending = leads.filter(status='pending').count()
    wallet = partner.wallet_balance()
    paginator = Paginator(leads, 20)
    page = request.GET.get('page', 1)
    leads_page = paginator.get_page(page)

    return render(request, 'pages/partner-dashboard.html', build_context(request, {
        'partner': partner,
        'leads': leads_page,
        'total_leads': total_leads,
        'qualified': qualified,
        'pending': pending,
        'wallet': wallet,
        'referral_link': f"{request.build_absolute_uri('/')}?ref={partner.referral_code}",
        'min_payout': AppSettings.get_min_payout(),
        'nav_active': 'dashboard',
    }))


@login_required
@user_passes_test(is_partner)
def partner_submit_deal(request):
    if request.method == 'POST':
        funding_amount = request.POST.get('funding_amount', '')
        monthly_revenue = request.POST.get('monthly_revenue', '')
        credit_score = request.POST.get('credit_score', '')
        time_in_business = request.POST.get('time_in_business', '')
        full_name = request.POST.get('full_name', '')
        email = request.POST.get('email', '')
        company_name = request.POST.get('company_name', '')
        phone = request.POST.get('phone', '')
        is_ppc = request.POST.get('is_pay_per_close') == 'on'
        notes = request.POST.get('notes', '')

        DealSubmission.objects.create(
            partner=request.user,
            funding_amount=funding_amount,
            monthly_revenue=monthly_revenue,
            credit_score=credit_score,
            time_in_business=time_in_business,
            full_name=full_name,
            email=email,
            company_name=company_name,
            phone=phone,
            is_pay_per_close=is_ppc,
            notes=notes,
        )

        Lead.objects.create(
            full_name=full_name,
            email=email,
            company_name=company_name,
            phone=phone or '',
            funding_amount=funding_amount,
            monthly_revenue=monthly_revenue,
            credit_score=credit_score,
            time_in_business=time_in_business,
            referred_by=request.user,
            referral_code_used=request.user.referral_code,
            source='partner_submitted',
            consent=True,
        )

        Referral.objects.create(
            partner=request.user,
            referral_code=request.user.referral_code,
            converted=True,
            visitor_ip=request.META.get('REMOTE_ADDR', ''),
            visitor_agent=request.META.get('HTTP_USER_AGENT', ''),
        )

        messages.success(request, 'Deal submitted successfully.')
        return redirect('partner_submit_deal')

    partner = request.user
    return render(request, 'pages/partner-submit-deal.html', build_context(request, {
        'partner': partner, 'nav_active': 'submit_deal',
    }))


@login_required
@user_passes_test(is_partner)
def partner_wallet(request):
    partner = request.user
    wallet = partner.wallet_balance()
    payouts = Payout.objects.filter(partner=partner).order_by('-created_at')[:20]
    bank_accounts = BankAccount.objects.filter(partner=partner)
    transactions = Transaction.objects.filter(partner=partner).order_by('-created_at')[:20]
    return render(request, 'pages/partner-wallet.html', build_context(request, {
        'partner': partner, 'wallet': wallet, 'payouts': payouts,
        'bank_accounts': bank_accounts, 'transactions': transactions,
        'min_payout': AppSettings.get_min_payout(),
        'nav_active': 'wallet',
    }))


@login_required
@user_passes_test(is_partner)
def partner_bank(request):
    partner = request.user
    bank_accounts = BankAccount.objects.filter(partner=partner)
    return render(request, 'pages/partner-bank.html', build_context(request, {
        'partner': partner, 'bank_accounts': bank_accounts, 'nav_active': 'bank',
    }))


@login_required
@user_passes_test(is_partner)
def partner_add_bank(request):
    if request.method == 'POST':
        is_primary = not BankAccount.objects.filter(partner=request.user).exists()
        BankAccount.objects.create(
            partner=request.user,
            account_holder_name=request.POST.get('account_holder_name', ''),
            bank_name=request.POST.get('bank_name', ''),
            account_number=request.POST.get('account_number', ''),
            routing_number=request.POST.get('routing_number', ''),
            account_type=request.POST.get('account_type', 'checking'),
            is_primary=is_primary,
        )
        messages.success(request, 'Bank account added.')
        return redirect('partner_dashboard')


@login_required
@user_passes_test(is_partner)
def partner_request_payout(request):
    partner = request.user
    balance = partner.wallet_balance()
    if balance < AppSettings.get_min_payout():
        messages.error(request, 'Minimum balance of $500 required for payout.')
        return redirect('partner_dashboard')
    account = BankAccount.objects.filter(partner=partner, is_primary=True).first()
    if not account:
        account = BankAccount.objects.filter(partner=partner).first()
    if not account:
        messages.error(request, 'Please add a bank account first.')
        return redirect('partner_dashboard')
    Payout.objects.create(partner=partner, amount=balance, bank_account=account)
    Transaction.objects.create(partner=partner, amount=balance, transaction_type='debit',
                               description='Payout requested via ACH')
    messages.success(request, f'Payout of ${balance:,.2f} requested. Processing weekly.')
    return redirect('partner_dashboard')


# ─── Superadmin Dashboard ─────────────────────────────────────────────────────

@login_required
@user_passes_test(is_superadmin, login_url='/partner/login/')
def superadmin_dashboard(request):
    leads = Lead.objects.all().order_by('-created_at')
    stats = {
        'total_leads': leads.count(),
        'pending': leads.filter(status='pending').count(),
        'qualified': leads.filter(status='qualified').count(),
        'non_qualified': leads.filter(status='non_qualified').count(),
        'archived': leads.filter(status='archived').count(),
    }

    # Filters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    referral_filter = request.GET.get('referral', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    if status_filter:
        leads = leads.filter(status=status_filter)
    if search_query:
        leads = leads.filter(
            Q(full_name__icontains=search_query) | Q(email__icontains=search_query) |
            Q(company_name__icontains=search_query) | Q(phone__icontains=search_query)
        )
    if referral_filter:
        leads = leads.filter(referral_code_used__iexact=referral_filter)
    if date_from:
        leads = leads.filter(created_at__gte=date_from)
    if date_to:
        leads = leads.filter(created_at__lte=f"{date_to} 23:59:59")

    # Sorting
    sort = request.GET.get('sort', '-created_at')
    allowed_sorts = ['created_at', '-created_at', 'full_name', 'status', 'monthly_revenue', 'referred_by']
    if sort in allowed_sorts:
        leads = leads.order_by(sort)

    paginator = Paginator(leads, 100)
    page_number = request.GET.get('page', 1)
    leads_page = paginator.get_page(page_number)

    partners = User.objects.filter(role__in=['partner', 'superadmin']).annotate(
        lead_count=Count('referred_leads'),
        qualified_count=Count('referred_leads', filter=Q(referred_leads__status='qualified')),
        total_earned=Sum('transactions__amount', filter=Q(transactions__transaction_type='credit')),
    )

    deals = DealSubmission.objects.all().order_by('-created_at')
    payouts = Payout.objects.filter(status='pending').order_by('-created_at')[:50]

    return render(request, 'pages/superadmin-dashboard.html', build_context(request, {
        'leads': leads_page,
        'stats': stats,
        'partners': partners,
        'deals': deals,
        'payouts': payouts,
        'app_settings': {
            'default_ppl_rate': AppSettings.get_ppl(),
            'min_payout': AppSettings.get_min_payout(),
            'openai_api_key': AppSettings.get('openai_api_key', ''),
        },
        'filters': {
            'status': status_filter,
            'search': search_query,
            'referral': referral_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
        'sort': sort,
    }))


@login_required
@user_passes_test(is_superadmin)
def superadmin_update_lead(request, lead_id):
    if request.method == 'POST':
        lead = get_object_or_404(Lead, id=lead_id)
        new_status = request.POST.get('status', lead.status)

        if new_status == 'qualified' and lead.status != 'qualified':
            if lead.referred_by and lead.referred_by.role in ('partner', 'superadmin'):
                partner = lead.referred_by
                credit_amount = float(partner.ppl_rate)
                lead_info = f"{lead.full_name} / {lead.company_name}"
                Transaction.objects.create(
                    partner=partner, amount=credit_amount, transaction_type='credit',
                    description=f'Qualified lead: {lead_info}', lead=lead
                )

        lead.status = new_status
        lead.notes = request.POST.get('notes', lead.notes)
        lead.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_edit_lead(request, lead_id):
    lead = get_object_or_404(Lead, id=lead_id)
    if request.method == 'POST':
        lead.full_name = request.POST.get('full_name', lead.full_name)
        lead.email = request.POST.get('email', lead.email)
        lead.company_name = request.POST.get('company_name', lead.company_name)
        lead.phone = request.POST.get('phone', lead.phone)
        lead.funding_amount = request.POST.get('funding_amount', lead.funding_amount)
        lead.monthly_revenue = request.POST.get('monthly_revenue', lead.monthly_revenue)
        lead.credit_score = request.POST.get('credit_score', lead.credit_score)
        lead.time_in_business = request.POST.get('time_in_business', lead.time_in_business)
        lead.notes = request.POST.get('notes', lead.notes)
        lead.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_delete_lead(request, lead_id):
    if request.method == 'POST':
        lead = get_object_or_404(Lead, id=lead_id)
        lead.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_add_lead(request):
    if request.method == 'POST':
        ref_code = request.POST.get('referral_code', '')
        referred_by = None
        source = request.POST.get('source', 'direct')
        if ref_code:
            try:
                referred_by = User.objects.get(referral_code=ref_code)
                source = 'referral'
            except User.DoesNotExist:
                pass

        lead = Lead.objects.create(
            full_name=request.POST.get('full_name', ''),
            email=request.POST.get('email', ''),
            company_name=request.POST.get('company_name', ''),
            phone=request.POST.get('phone', ''),
            funding_amount=request.POST.get('funding_amount', ''),
            monthly_revenue=request.POST.get('monthly_revenue', ''),
            credit_score=request.POST.get('credit_score', ''),
            time_in_business=request.POST.get('time_in_business', ''),
            source=source,
            referred_by=referred_by,
            referral_code_used=ref_code,
            consent=True,
            notes=request.POST.get('notes', ''),
        )
        if referred_by and referred_by.referral_code:
            Referral.objects.create(partner=referred_by, referral_code=referred_by.referral_code, converted=True, lead=lead)
        return JsonResponse({'success': True, 'lead_id': lead.id})
    return JsonResponse({'success': False, 'error': 'POST required'}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_deal_update_status(request, deal_id):
    if request.method == 'POST':
        deal = get_object_or_404(DealSubmission, id=deal_id)
        new_status = request.POST.get('status', '')
        if new_status:
            deal.status = new_status
            deal.reviewed_by = request.user
            deal.save()
            if new_status == 'approved' and deal.is_pay_per_close:
                try:
                    pct = 0.02
                    amount = float(deal.deal_size.replace('$', '').replace(',', ''))
                    commission = amount * pct
                    Transaction.objects.create(
                        partner=deal.partner, amount=commission, transaction_type='credit',
                        description=f'Pay-per-close deal: {deal.full_name} ({deal.deal_size})'
                    )
                except Exception:
                    pass
            return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_bulk_action(request):
    if request.method == 'POST':
        ids = request.POST.getlist('lead_ids', [])
        action = request.POST.get('action', '')
        if ids and action:
            leads = Lead.objects.filter(id__in=ids)
            if action in ('pending', 'qualified', 'non_qualified', 'archived'):
                for lead in leads:
                    if action == 'qualified' and lead.status != 'qualified' and lead.referred_by:
                        Transaction.objects.create(
                            partner=lead.referred_by, amount=float(lead.referred_by.ppl_rate), transaction_type='credit',
                            description=f'Qualified lead (bulk): {lead.full_name}', lead=lead
                        )
                    lead.status = action
                    lead.save()
            elif action == 'delete':
                leads.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_export_csv(request):
    status_filter = request.GET.get('status', '')
    leads = Lead.objects.all()
    if status_filter:
        leads = leads.filter(status=status_filter)

    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(['Name', 'Email', 'Company', 'Phone', 'Funding Amount', 'Monthly Revenue',
                     'Credit Score', 'Time in Business', 'Status', 'Source', 'Referral Code',
                     'Referred By', 'Created At'])
    for lead in leads:
        writer.writerow([
            lead.full_name, lead.email, lead.company_name, lead.phone,
            lead.funding_amount, lead.monthly_revenue, lead.credit_score,
            lead.time_in_business, lead.status, lead.source,
            lead.referral_code_used, lead.referred_by.email if lead.referred_by else '',
            lead.created_at.strftime('%Y-%m-%d %H:%M')
        ])

    response = HttpResponse(csv_buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="leads-{now().strftime("%Y%m%d")}.csv"'
    return response


@login_required
@user_passes_test(is_superadmin)
def superadmin_deal_review(request, deal_id):
    deal = get_object_or_404(DealSubmission, id=deal_id)
    if request.method == 'POST':
        deal.status = request.POST.get('status', deal.status)
        deal.reviewed_by = request.user
        deal.save()
        if deal.status == 'approved' and deal.is_pay_per_close and deal.deal_size:
            try:
                pct = 0.02
                amount = float(deal.deal_size.replace('$', '').replace(',', ''))
                commission = amount * pct
                Transaction.objects.create(
                    partner=deal.partner, amount=commission, transaction_type='credit',
                    description=f'Pay-per-close deal: {deal.full_name} ({deal.deal_size})'
                )
                messages.success(request, f'Commission of ${commission:,.2f} credited to partner.')
            except:
                pass
        return redirect('superadmin_dashboard')
    return render(request, 'pages/superadmin-deal-review.html', build_context(request, {'deal': deal}))


@login_required
@user_passes_test(is_superadmin)
def superadmin_process_payout(request, payout_id):
    if request.method == 'POST':
        payout = get_object_or_404(Payout, id=payout_id)
        payout.status = 'paid'
        payout.processed_at = now()
        payout.notes = request.POST.get('notes', 'Paid via ACH')
        payout.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_pay_partner(request, partner_id):
    if request.method == 'POST':
        partner = get_object_or_404(User, id=partner_id)
        balance = partner.wallet_balance()
        if balance > 0:
            amount = float(request.POST.get('amount', 0))
            if not amount or amount > balance:
                amount = balance
            Payout.objects.create(partner=partner, amount=amount, status='paid',
                                  notes=f'Manual payout by admin', processed_at=now())
            Transaction.objects.create(partner=partner, amount=amount, transaction_type='debit',
                                       description=f'Admin payout processed')
            return JsonResponse({'success': True, 'payout': float(amount)})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_update_ppl(request, partner_id):
    if request.method == 'POST':
        partner = get_object_or_404(User, id=partner_id)
        new_rate = float(request.POST.get('ppl_rate', AppSettings.get_ppl()))
        if new_rate > 0:
            partner.ppl_rate = new_rate
            partner.save()
            return JsonResponse({'success': True, 'ppl_rate': partner.ppl_rate})
    return JsonResponse({'success': False}, status=400)


@login_required
@user_passes_test(is_superadmin)
def superadmin_settings(request):
    if request.method == 'POST':
        AppSettings.set('default_ppl_rate', request.POST.get('default_ppl_rate', 100), 'Default pay per qualified lead')
        AppSettings.set('min_payout_amount', request.POST.get('min_payout_amount', 500), 'Minimum balance for partner payout')
        AppSettings.set('openai_api_key', request.POST.get('openai_api_key', ''), 'OpenAI API key for AI thumbnail generation')
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=400)


# ─── Blog Management (Superadmin) ─────────────────────────────────────────────

@login_required
@user_passes_test(is_superadmin)
def superadmin_blog_list(request):
    posts = BlogPost.objects.all().order_by('-published_at', '-created_at')
    paginator = Paginator(posts, 20)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    return render(request, 'pages/superadmin-blog-list.html', build_context(request, {
        'posts': posts_page,
    }))


@login_required
@user_passes_test(is_superadmin)
def superadmin_blog_create(request):
    return render(request, 'pages/superadmin-blog-editor.html', build_context(request, {
        'post': None,
    }))


@login_required
@user_passes_test(is_superadmin)
def superadmin_blog_edit(request, post_id):
    post = get_object_or_404(BlogPost, id=post_id)
    return render(request, 'pages/superadmin-blog-editor.html', build_context(request, {
        'post': post,
    }))


@csrf_exempt
def superadmin_blog_save(request):
    try:
        if not request.user.is_authenticated or request.user.role != 'superadmin':
            return JsonResponse({'success': False, 'error': 'Not authorized. Please log in again.'}, status=403)

        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST required'}, status=400)

        post_id = request.POST.get('post_id', '')
        title = request.POST.get('title', '').strip()
        subtitle = request.POST.get('subtitle', '').strip()
        category = request.POST.get('category', 'capital-strategy')
        excerpt = request.POST.get('excerpt', '').strip()
        content = request.POST.get('content', '')
        is_published = request.POST.get('is_published', '') == 'on'

        if not title or not content:
            return JsonResponse({'success': False, 'error': 'Title and content are required.'}, status=400)

        if post_id:
            post = get_object_or_404(BlogPost, id=post_id)
            post.title = title
            post.subtitle = subtitle
            post.category = category
            post.excerpt = excerpt
            post.content = content
            post.is_published = is_published
            if is_published and not post.published_at:
                post.published_at = timezone.now()
        else:
            post = BlogPost(
                title=title,
                subtitle=subtitle,
                category=category,
                excerpt=excerpt,
                content=content,
                is_published=is_published,
                author=request.user,
                published_at=timezone.now() if is_published else None,
            )

        featured_image = request.FILES.get('featured_image')
        if featured_image:
            post.featured_image = featured_image

        post.save()
        return JsonResponse({'success': True, 'post_id': post.id, 'slug': post.slug})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@user_passes_test(is_superadmin)
def superadmin_blog_delete(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)
    post = get_object_or_404(BlogPost, id=post_id)
    post.delete()
    return JsonResponse({'success': True})


# ─── AI Thumbnail Generator ──────────────────────────────────────────────────

import threading
import base64
import io
import json
from django.core.files.base import ContentFile

_thumbnail_progress = {}

@login_required
@user_passes_test(is_superadmin)
def superadmin_ai_thumbnails(request):
    if request.method == 'POST' and request.POST.get('action') == 'save_key':
        AppSettings.set('openai_api_key', request.POST.get('openai_api_key', ''), 'OpenAI API key')
        return JsonResponse({'success': True})

    from atlas.models import BlogPost
    posts_without_image = BlogPost.objects.filter(
        is_published=True,
        featured_image__isnull=True
    ).order_by('-published_at')

    return render(request, 'pages/superadmin-ai-thumbnails.html', build_context(request, {
        'posts_count': posts_without_image.count(),
        'posts_without_image': posts_without_image,
        'openai_api_key': AppSettings.get('openai_api_key', ''),
        'current_progress': _thumbnail_progress.get('state', {}),
    }))


@login_required
@user_passes_test(is_superadmin)
def superadmin_ai_thumbnails_generate(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)

    api_key = AppSettings.get('openai_api_key', '')
    if not api_key:
        return JsonResponse({'success': False, 'error': 'No OpenAI API key saved. Add your key in Settings first.'})

    from atlas.models import BlogPost
    posts = BlogPost.objects.filter(
        is_published=True,
        featured_image__isnull=True
    ).order_by('-published_at')

    total = posts.count()
    if total == 0:
        return JsonResponse({'success': False, 'error': 'All published posts already have featured images.'})

    _thumbnail_progress['state'] = {
        'running': True,
        'total': total,
        'completed': 0,
        'failed': 0,
        'current': '',
        'log': [],
    }

    def _generate():
        from atlas.models import BlogPost as BP
        client = None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
        except Exception:
            _thumbnail_progress['state']['running'] = False
            _thumbnail_progress['state']['log'].append('Failed to initialize OpenAI client.')
            return

        for post in posts:
            if not _thumbnail_progress['state']['running']:
                break
            _thumbnail_progress['state']['current'] = post.title[:80]
            try:
                prompt = (
                    f"A professional, premium financial blog thumbnail image for an article titled "
                    f"\"{post.title}\". Modern corporate style, dark navy and gold color palette, "
                    f"clean minimal design, no text on the image, abstract geometric shapes, "
                    f"luxury financial company aesthetic, 16:9 aspect ratio, photorealistic render."
                )
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )
                image_url = response.data[0].url
                import urllib.request
                img_data = urllib.request.urlopen(image_url).read()
                filename = f"ai_thumb_{post.slug}.png"
                post.featured_image.save(filename, ContentFile(img_data), save=False)
                post.save(update_fields=['featured_image'])
                _thumbnail_progress['state']['completed'] += 1
                _thumbnail_progress['state']['log'].append(f'OK: {post.title[:60]}')
            except Exception as e:
                _thumbnail_progress['state']['failed'] += 1
                _thumbnail_progress['state']['log'].append(f'FAIL: {post.title[:60]} — {str(e)[:100]}')
        _thumbnail_progress['state']['running'] = False
        _thumbnail_progress['state']['current'] = 'Done'
        _thumbnail_progress['state']['log'].append(
            f'Finished. {_thumbnail_progress["state"]["completed"]} generated, {_thumbnail_progress["state"]["failed"]} failed.'
        )

    threading.Thread(target=_generate, daemon=True).start()
    return JsonResponse({'success': True, 'total': total})


@login_required
@user_passes_test(is_superadmin)
def superadmin_ai_thumbnails_status(request):
    state = _thumbnail_progress.get('state', {
        'running': False, 'total': 0, 'completed': 0, 'failed': 0, 'current': '', 'log': []
    })
    return JsonResponse(state)


@login_required
@user_passes_test(is_superadmin)
def superadmin_contacts(request):
    contacts = Contact.objects.all().order_by('-created_at')
    paginator = Paginator(contacts, 25)
    page_number = request.GET.get('page', 1)
    contacts_page = paginator.get_page(page_number)
    return render(request, 'pages/superadmin-contacts.html', build_context(request, {
        'contacts': contacts_page,
        'total_count': contacts.count(),
    }))


@login_required
@user_passes_test(is_superadmin)
def superadmin_contact_delete(request, contact_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)
    contact = get_object_or_404(Contact, id=contact_id)
    contact.delete()
    return JsonResponse({'success': True})


# ─── Brand Mentions ─────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_superadmin)
def superadmin_brand_mentions(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        url = request.POST.get('url', '').strip()
        if not title or not url:
            return JsonResponse({'success': False, 'error': 'Title and URL are required.'})
        BrandMention.objects.create(title=title, url=url)
        return JsonResponse({'success': True})

    mentions = BrandMention.objects.all().order_by('-created_at')
    return render(request, 'pages/superadmin-brand-mentions.html', build_context(request, {
        'mentions': mentions,
    }))


@login_required
@user_passes_test(is_superadmin)
def superadmin_brand_mention_delete(request, mention_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=400)
    mention = get_object_or_404(BrandMention, id=mention_id)
    mention.delete()
    return JsonResponse({'success': True})
