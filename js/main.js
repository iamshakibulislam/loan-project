document.addEventListener('DOMContentLoaded', function() {
  var toggle = document.getElementById('mobileToggle');
  var mobileMenu = document.getElementById('mobileMenu');
  if (toggle && mobileMenu) {
    toggle.addEventListener('click', function() {
      mobileMenu.classList.toggle('open');
    });
  }

  document.querySelectorAll('.faq-question').forEach(function(q) {
    q.addEventListener('click', function() {
      this.parentElement.classList.toggle('open');
    });
  });

  initHeroForm();
});

function initHeroForm() {
  var form = document.getElementById('heroForm');
  if (!form) return;

  var successEl = form.querySelector('.form-success');
  var submitBtn = document.getElementById('formSubmit');
  if (!submitBtn) return;

  function showSuccess() {
    var step = form.querySelector('.form-step');
    if (step) step.style.display = 'none';
    if (successEl) successEl.style.display = 'block';
  }

  submitBtn.addEventListener('click', function(e) {
    e.preventDefault();

    var amount = document.getElementById('fundingAmount');
    var revenue = document.getElementById('monthlyRevenue');
    var credit = document.getElementById('creditScore');
    var timeBiz = document.getElementById('timeInBusiness');
    var fullName = document.getElementById('fullName');
    var email = document.getElementById('email');
    var companyName = document.getElementById('companyName');
    var phone = document.getElementById('phone');
    var smsTransactionalConsent = document.getElementById('smsTransactionalConsent');
    var smsMarketingConsent = document.getElementById('smsMarketingConsent');
    var emailConsent = document.getElementById('emailConsent');
    var termsConsent = document.getElementById('termsConsent');

    if (!amount || !amount.value.trim()) { shakeElement(amount); return; }
    if (!revenue || !revenue.value.trim()) { shakeElement(revenue); return; }
    if (!credit || !credit.value.trim()) { shakeElement(credit); return; }
    if (!timeBiz || !timeBiz.value.trim()) { shakeElement(timeBiz); return; }
    if (!fullName || !fullName.value.trim()) { shakeElement(fullName); return; }
    if (!email || !email.value.trim() || !email.value.includes('@')) { shakeElement(email); return; }
    if (!companyName || !companyName.value.trim()) { shakeElement(companyName); return; }
    if (!phone || !phone.value.trim()) { shakeElement(phone); return; }
    if (!termsConsent || !termsConsent.checked) { shakeElement(termsConsent); return; }

    var fd = new FormData();
    fd.append('funding_amount', amount.value);
    fd.append('monthly_revenue', revenue.value);
    fd.append('credit_score', credit.value);
    fd.append('time_in_business', timeBiz.value);
    fd.append('full_name', fullName.value);
    fd.append('email', email.value);
    fd.append('company_name', companyName.value);
    fd.append('phone', phone.value);
    fd.append('sms_transactional_consent', smsTransactionalConsent && smsTransactionalConsent.checked ? 'on' : '');
    fd.append('sms_marketing_consent', smsMarketingConsent && smsMarketingConsent.checked ? 'on' : '');
    fd.append('email_consent', emailConsent && emailConsent.checked ? 'on' : '');
    fd.append('terms_consent', termsConsent && termsConsent.checked ? 'on' : '');

    fetch('/api/submit-lead/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': getCSRF() } })
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data.success) {
          var eventParams = {
            referral_source: data.referrer || 'direct',
            landing_page: data.landing_page || window.location.href,
            form_type: 'hero'
          };
          if (typeof gtag === 'function') {
            gtag('event', 'generate_lead', eventParams);
            console.log('[GA] generate_lead fired:', eventParams);
          } else {
            console.warn('[GA] gtag not available — event not sent:', eventParams);
          }
          showSuccess();
        }
      })
      .catch(function() {
        showSuccess();
      });
  });
}

function getCSRF() {
  var cookie = document.cookie.split('; ').find(function(row) { return row.startsWith('csrftoken='); });
  return cookie ? cookie.split('=')[1] : '';
}

function shakeElement(el) {
  if (!el) return;
  el.style.transition = 'all 0.1s ease';
  el.style.borderColor = '#ef4444';
  el.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.2)';
  setTimeout(function() { el.style.borderColor = ''; el.style.boxShadow = ''; }, 1500);
}
