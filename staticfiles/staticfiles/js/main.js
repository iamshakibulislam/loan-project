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

  var steps = form.querySelectorAll('.form-step');
  var nextBtns = form.querySelectorAll('.form-next');
  var progress = form.querySelector('.form-progress');
  var successEl = form.querySelector('.form-success');
  var submitBtn = document.getElementById('formSubmit');
  var currentStep = 0;
  var totalSteps = steps.length;

  function showStep(n) {
    steps.forEach(function(s) { s.classList.remove('active'); });
    steps[n].classList.add('active');
    currentStep = n;
    if (progress) {
      progress.textContent = 'Step ' + (n + 1) + ' of ' + totalSteps;
    }
  }

  if (nextBtns.length) {
    nextBtns.forEach(function(btn) {
      btn.addEventListener('click', function(e) {
        e.preventDefault();
        if (currentStep === 0) {
          var amount = document.getElementById('fundingAmount');
          var revenue = document.getElementById('monthlyRevenue');
          if (!amount.value.trim() || !revenue.value.trim()) {
            shakeElement(amount || revenue);
            return;
          }
        }
        if (currentStep === 1) {
          var credit = document.getElementById('creditScore');
          var timeBiz = document.getElementById('timeInBusiness');
          if (!credit.value.trim() || !timeBiz.value.trim()) {
            shakeElement(credit || timeBiz);
            return;
          }
        }
        if (currentStep < totalSteps - 1) {
          showStep(currentStep + 1);
        }
      });
    });
  }

  if (submitBtn) {
    submitBtn.addEventListener('click', function(e) {
      e.preventDefault();
      var fullName = document.getElementById('fullName');
      var email = document.getElementById('email');
      var companyName = document.getElementById('companyName');
      var phone = document.getElementById('phone');
      var consent = document.getElementById('consent');

      if (!fullName || !fullName.value.trim()) { shakeElement(fullName); return; }
      if (!email || !email.value.trim() || !email.value.includes('@')) { shakeElement(email); return; }
      if (!companyName || !companyName.value.trim()) { shakeElement(companyName); return; }
      if (!phone || !phone.value.trim()) { shakeElement(phone); return; }
      if (!consent || !consent.checked) { shakeElement(consent); return; }

      var fd = new FormData();
      fd.append('funding_amount', document.getElementById('fundingAmount').value);
      fd.append('monthly_revenue', document.getElementById('monthlyRevenue').value);
      fd.append('credit_score', document.getElementById('creditScore').value);
      fd.append('time_in_business', document.getElementById('timeInBusiness').value);
      fd.append('full_name', fullName.value);
      fd.append('email', email.value);
      fd.append('company_name', companyName.value);
      fd.append('phone', phone.value);
      fd.append('consent', consent.checked ? 'on' : '');

      fetch('/api/submit-lead/', { method: 'POST', body: fd, headers: { 'X-CSRFToken': getCSRF() } })
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.success) {
            steps.forEach(function(s) { s.classList.remove('active'); });
            if (progress) progress.style.display = 'none';
            if (successEl) successEl.style.display = 'block';
          }
        })
        .catch(function() {
          steps.forEach(function(s) { s.classList.remove('active'); });
          if (progress) progress.style.display = 'none';
          if (successEl) successEl.style.display = 'block';
        });
    });
  }
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
