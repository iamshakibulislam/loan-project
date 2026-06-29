from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from atlas import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('faqs/', views.faqs, name='faqs'),
    path('contact/', views.contact, name='contact'),
    path('blog/', views.blog, name='blog'),
    path('blog/<slug:slug>/', views.blog_post_detail, name='blog_post_detail'),
    path('resources/', views.resources, name='resources'),
    path('terms/', views.terms, name='terms'),
    path('partners/', views.partner_detail, name='partner_detail'),
    path('product/<slug:slug>/', views.product_page, name='product_page'),
    path('api/submit-lead/', views.submit_lead, name='submit_lead'),
    path('partner/signup/', views.partner_signup, name='partner_signup'),
    path('partner/login/', views.partner_login, name='partner_login'),
    path('partner/logout/', views.partner_logout, name='partner_logout'),
    path('dashboard/', views.partner_dashboard, name='partner_dashboard'),
    path('dashboard/submit-deal/', views.partner_submit_deal, name='partner_submit_deal'),
    path('dashboard/wallet/', views.partner_wallet, name='partner_wallet'),
    path('dashboard/bank/', views.partner_bank, name='partner_bank'),
    path('dashboard/add-bank/', views.partner_add_bank, name='partner_add_bank'),
    path('dashboard/request-payout/', views.partner_request_payout, name='partner_request_payout'),
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/lead/<int:lead_id>/update/', views.superadmin_update_lead, name='superadmin_update_lead'),
    path('superadmin/lead/<int:lead_id>/edit/', views.superadmin_edit_lead, name='superadmin_edit_lead'),
    path('superadmin/lead/<int:lead_id>/delete/', views.superadmin_delete_lead, name='superadmin_delete_lead'),
    path('superadmin/bulk-action/', views.superadmin_bulk_action, name='superadmin_bulk_action'),
    path('superadmin/export-csv/', views.superadmin_export_csv, name='superadmin_export_csv'),
    path('superadmin/deal/<int:deal_id>/', views.superadmin_deal_review, name='superadmin_deal_review'),
    path('superadmin/deal/<int:deal_id>/update-status/', views.superadmin_deal_update_status, name='superadmin_deal_update_status'),
    path('superadmin/add-lead/', views.superadmin_add_lead, name='superadmin_add_lead'),
    path('superadmin/payout/<int:payout_id>/process/', views.superadmin_process_payout, name='superadmin_process_payout'),
    path('superadmin/partner/<int:partner_id>/pay/', views.superadmin_pay_partner, name='superadmin_pay_partner'),
    path('superadmin/partner/<int:partner_id>/ppl/', views.superadmin_update_ppl, name='superadmin_update_ppl'),
    path('superadmin/settings/', views.superadmin_settings, name='superadmin_settings'),
    path('superadmin/blog/', views.superadmin_blog_list, name='superadmin_blog_list'),
    path('superadmin/blog/new/', views.superadmin_blog_create, name='superadmin_blog_create'),
    path('superadmin/blog/save/', views.superadmin_blog_save, name='superadmin_blog_save'),
    path('superadmin/blog/<int:post_id>/edit/', views.superadmin_blog_edit, name='superadmin_blog_edit'),
    path('superadmin/blog/<int:post_id>/delete/', views.superadmin_blog_delete, name='superadmin_blog_delete'),
    path('superadmin/ai-thumbnails/', views.superadmin_ai_thumbnails, name='superadmin_ai_thumbnails'),
    path('superadmin/ai-thumbnails/generate/', views.superadmin_ai_thumbnails_generate, name='superadmin_ai_thumbnails_generate'),
    path('superadmin/ai-thumbnails/status/', views.superadmin_ai_thumbnails_status, name='superadmin_ai_thumbnails_status'),
    path('superadmin/contacts/', views.superadmin_contacts, name='superadmin_contacts'),
    path('superadmin/contacts/<int:contact_id>/delete/', views.superadmin_contact_delete, name='superadmin_contact_delete'),
    path('superadmin/brand-mentions/', views.superadmin_brand_mentions, name='superadmin_brand_mentions'),
    path('superadmin/brand-mentions/<int:mention_id>/delete/', views.superadmin_brand_mention_delete, name='superadmin_brand_mention_delete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
