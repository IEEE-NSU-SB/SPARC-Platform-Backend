/* ============================================================
   SPARC 2026 - Ambassador Form Behaviours
   Multi-step form with validation matching Phase 1, Phase 2, & Hackathon
   ============================================================ */
(function () {
  'use strict';

  var form = document.getElementById('ambassador-form');
  if (!form) return;

  var ieeeFields = document.getElementById('ieee-fields');
  var bio = document.getElementById('id_bio');
  var counter = document.getElementById('bio-counter');
  var photo = document.getElementById('id_photo');
  var photoError = document.getElementById('photo-error');
  var submitBtn = document.getElementById('submit-btn');
  var MAX_WORDS = counter ? parseInt(counter.getAttribute('data-max'), 10) || 50 : 50;
  var MAX_FILE_BYTES = 10 * 1024 * 1024; // 10 MB, per the spec

  /* ---------- 1. Multi-Step Navigation & Validation ---------- */

  window.goToStep = function (stepNumber) {
    var sections = form.querySelectorAll("section[id^='step']");
    for (var i = 0; i < sections.length; i++) {
      sections[i].classList.add("hidden");
    }
    var target = document.getElementById("step" + stepNumber);
    if (target) {
      target.classList.remove("hidden");
    }
    window.scrollTo({ top: 250, behavior: "smooth" });
  };

  window.prevStep = function (currentStep) {
    var prev = Math.max(1, currentStep - 1);
    window.goToStep(prev);
  };

  function clearStepErrors(stepEl) {
    if (!stepEl) return;
    var inputs = stepEl.querySelectorAll('input, select, textarea');
    inputs.forEach(function (el) {
      el.style.borderColor = '';
    });
    var choiceLabels = stepEl.querySelectorAll('.choice');
    choiceLabels.forEach(function (l) {
      l.style.color = '';
    });
  }

  function validateStep(currentStep) {
    var stepEl = document.getElementById('step' + currentStep);
    if (!stepEl) return true;
    clearStepErrors(stepEl);

    if (currentStep === 1) {
      var name = document.getElementById('id_name');
      var email = document.getElementById('id_email');
      var whatsapp = document.getElementById('id_whatsapp');
      var dob = document.getElementById('id_date_of_birth');
      var genderRadios = form.querySelectorAll('input[name="gender"]');
      var uni = document.getElementById('id_university');
      var dept = document.getElementById('id_department');
      var year = document.getElementById('id_year_of_study');
      var sid = document.getElementById('id_student_id');

      var missing = false;
      var firstField = null;

      [name, dob, uni, dept, year, sid].forEach(function (f) {
        if (!f || !f.value.trim()) {
          missing = true;
          if (f) f.style.borderColor = '#ef4444';
          if (!firstField) firstField = f;
        }
      });

      var emailVal = email ? email.value.trim() : '';
      var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailVal || !emailRegex.test(emailVal)) {
        missing = true;
        if (email) email.style.borderColor = '#ef4444';
        if (!firstField) firstField = email;
      }

      var waVal = whatsapp ? whatsapp.value.trim() : '';
      var waRegex = /^\+?[0-9][0-9\s\-()]{6,19}$/;
      if (!waVal || !waRegex.test(waVal)) {
        missing = true;
        if (whatsapp) whatsapp.style.borderColor = '#ef4444';
        if (!firstField) firstField = whatsapp;
      }

      var genderChecked = form.querySelector('input[name="gender"]:checked');
      if (!genderChecked) {
        missing = true;
        genderRadios.forEach(function (r) {
          var lbl = r.closest('.choice');
          if (lbl) lbl.style.color = '#ef4444';
        });
        if (!firstField && genderRadios.length) firstField = genderRadios[0];
      }

      if (missing) {
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Incomplete Section',
            text: 'Please fill in all the required fields in this section before continuing.',
            confirmButtonColor: '#00629B',
          });
        }
        if (firstField && firstField.focus) firstField.focus();
        return false;
      }
      return true;
    }

    if (currentStep === 2) {
      var ieeeChosen = form.querySelector('input[name="is_ieee_member"]:checked');
      if (!ieeeChosen) {
        var ieeeRadios = form.querySelectorAll('input[name="is_ieee_member"]');
        ieeeRadios.forEach(function (r) {
          var lbl = r.closest('.choice');
          if (lbl) lbl.style.color = '#ef4444';
        });
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'IEEE Information Required',
            text: 'Please indicate whether you are an IEEE member.',
            confirmButtonColor: '#00629B',
          });
        }
        return false;
      }

      if (ieeeChosen.value === 'True') {
        var num = document.getElementById('id_ieee_number');
        var grade = document.getElementById('id_ieee_grade');
        var branch = document.getElementById('id_ieee_branch');
        var pos = document.getElementById('id_ieee_position');
        var missingIeee = false;
        var firstIeee = null;

        [num, grade, branch, pos].forEach(function (f) {
          if (!f || !f.value.trim()) {
            missingIeee = true;
            if (f) f.style.borderColor = '#ef4444';
            if (!firstIeee) firstIeee = f;
          }
        });

        if (missingIeee) {
          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: 'warning',
              title: 'IEEE Fields Required',
              text: 'Please fill in your IEEE membership details before continuing.',
              confirmButtonColor: '#00629B',
            });
          }
          if (firstIeee && firstIeee.focus) firstIeee.focus();
          return false;
        }
      }
      return true;
    }

    if (currentStep === 3) {
      var photoEl = document.getElementById('id_photo');
      var bioEl = document.getElementById('id_bio');

      if (!photoEl || !photoEl.files || photoEl.files.length === 0) {
        if (photoEl) photoEl.style.borderColor = '#ef4444';
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Photo Required',
            text: 'Please upload your formal photo before continuing.',
            confirmButtonColor: '#00629B',
          });
        }
        return false;
      }

      var bioText = bioEl ? bioEl.value.trim() : '';
      if (!bioText) {
        if (bioEl) bioEl.style.borderColor = '#ef4444';
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Bio Required',
            text: 'Please write a short bio before continuing.',
            confirmButtonColor: '#00629B',
          });
        }
        if (bioEl) bioEl.focus();
        return false;
      }

      if (form.getAttribute('data-bio-over') === 'true' || countWords(bioText) > MAX_WORDS) {
        if (bioEl) bioEl.style.borderColor = '#ef4444';
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Bio Too Long',
            text: 'The bio must be ' + MAX_WORDS + ' words or fewer.',
            confirmButtonColor: '#00629B',
          });
        }
        if (bioEl) bioEl.focus();
        return false;
      }
      return true;
    }

    if (currentStep === 4) {
      var why = document.getElementById('id_why_ambassador');
      var heardChosen = form.querySelector('input[name="heard_from"]:checked');

      if (!why || !why.value.trim()) {
        if (why) why.style.borderColor = '#ef4444';
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Response Required',
            text: 'Please explain why you want to become a SPARC Ambassador.',
            confirmButtonColor: '#00629B',
          });
        }
        if (why) why.focus();
        return false;
      }

      if (!heardChosen) {
        var heardRadios = form.querySelectorAll('input[name="heard_from"]');
        heardRadios.forEach(function (r) {
          var lbl = r.closest('.choice');
          if (lbl) lbl.style.color = '#ef4444';
        });
        if (typeof Swal !== 'undefined') {
          Swal.fire({
            icon: 'warning',
            title: 'Response Required',
            text: 'Please select how you heard about SPARC.',
            confirmButtonColor: '#00629B',
          });
        }
        return false;
      }
      return true;
    }

    return true;
  }

  window.nextStep = function (currentStep) {
    if (!validateStep(currentStep)) {
      return;
    }
    window.goToStep(currentStep + 1);
  };

  /* ---------- 2. IEEE toggle ---------- */

  function syncIeee() {
    if (!ieeeFields) return;
    var chosen = form.querySelector('input[name="is_ieee_member"]:checked');
    var isMember = !!chosen && chosen.value === 'True';
    ieeeFields.hidden = !isMember;

    var els = ieeeFields.querySelectorAll('input, select, textarea');
    for (var i = 0; i < els.length; i++) {
      els[i].disabled = !isMember;
      if (isMember) {
        els[i].required = true;
      } else {
        els[i].required = false;
      }
    }
  }

  var ieeeRadios = form.querySelectorAll('input[name="is_ieee_member"]');
  for (var i = 0; i < ieeeRadios.length; i++) {
    ieeeRadios[i].addEventListener('change', syncIeee);
  }
  syncIeee();

  /* ---------- 3. Bio word counter ---------- */

  function countWords(text) {
    var words = text.trim().split(/\s+/);
    return words.length === 1 && words[0] === '' ? 0 : words.length;
  }

  function syncCounter() {
    if (!bio || !counter) return;
    var n = countWords(bio.value);
    if (n > MAX_WORDS) {
      counter.textContent = n + ' / ' + MAX_WORDS + ' words - trim to ' + MAX_WORDS + ' to submit';
      counter.className = 'word-counter over';
      form.setAttribute('data-bio-over', 'true');
    } else {
      counter.textContent = n + ' / ' + MAX_WORDS + ' words';
      counter.className = 'word-counter' + (n > MAX_WORDS - 5 ? ' near' : '');
      form.removeAttribute('data-bio-over');
    }
  }

  if (bio) {
    bio.addEventListener('input', syncCounter);
    syncCounter();
  }

  /* ---------- 4. Photo pre-check ---------- */

  function showPhotoError(message) {
    if (photoError) {
      photoError.textContent = message;
      photoError.hidden = false;
    }
    if (typeof Swal !== 'undefined') {
      Swal.fire({
        icon: 'error',
        title: 'Invalid Photo',
        text: message,
        confirmButtonColor: '#00629B',
      });
    }
    if (photo) photo.value = '';
  }

  function syncPhoto() {
    if (!photo || !photoError) return;
    photoError.hidden = true;
    photoError.textContent = '';
    var f = photo.files && photo.files[0];
    if (!f) return;
    var typeOk = /^image\/(jpe?g|png)$/i.test(f.type);
    var nameOk = /\.(jpe?g|png)$/i.test(f.name);
    if (!(typeOk && nameOk)) {
      showPhotoError('Please upload a JPG or PNG image.');
    } else if (f.size > MAX_FILE_BYTES) {
      showPhotoError('Photo is too large (' + (f.size / 1048576).toFixed(1) + ' MB). Maximum is 10 MB.');
    }
  }

  if (photo) photo.addEventListener('change', syncPhoto);

  /* ---------- 5. Submit: guard, AJAX, confirmation, fallback ---------- */

  function setBusy(busy) {
    if (!submitBtn) return;
    submitBtn.disabled = busy;
    submitBtn.textContent = busy ? 'Submitting...' : 'Submit application';
  }

  function csrfToken() {
    var el = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return el ? el.value : '';
  }

  function nativeSubmit() {
    form.setAttribute('data-native-submit', 'true');
    form.submit();
  }

  function showConfirmation() {
    var box = document.getElementById('confirmation');
    form.hidden = true;
    var head = document.querySelector('.form-head');
    if (head) head.hidden = true;
    if (box) {
      box.hidden = false;
      box.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
      window.location.href = '/ambassador/thanks/';
    }
  }

  function findStepForField(fieldName) {
    var host = form.querySelector('[data-field="' + fieldName + '"]');
    if (!host) return 1;
    var sec = host.closest('section');
    if (sec && sec.id && sec.id.startsWith('step')) {
      var num = parseInt(sec.id.replace('step', ''), 10);
      if (!isNaN(num)) return num;
    }
    return 1;
  }

  function renderErrors(errors) {
    var lists = form.querySelectorAll('.errorlist');
    for (var i = 0; i < lists.length; i++) {
      if (lists[i].hasAttribute('data-server')) continue;
      lists[i].parentNode.removeChild(lists[i]);
    }
    var first = null;
    var firstField = null;
    for (var name in errors) {
      if (!Object.prototype.hasOwnProperty.call(errors, name)) continue;
      var host = form.querySelector('[data-field="' + name + '"]');
      if (!host) {
        if (name === '__all__') {
          host = form.querySelector('.submit-row') || form;
        } else {
          continue;
        }
      }
      var ul = document.createElement('ul');
      ul.className = 'errorlist';
      for (var j = 0; j < errors[name].length; j++) {
        var li = document.createElement('li');
        li.textContent = errors[name][j];
        ul.appendChild(li);
      }
      host.appendChild(ul);
      if (!first) {
        first = host;
        firstField = name;
      }
    }
    if (first && firstField) {
      var targetStep = findStepForField(firstField);
      window.goToStep(targetStep);
      first.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }

  form.addEventListener('submit', function (e) {
    if (form.getAttribute('data-native-submit') === 'true') return;

    // Validate agreement declarations
    var a1 = document.getElementById('id_agree_info_accurate');
    var a2 = document.getElementById('id_agree_media_usage');
    var a3 = document.getElementById('id_agree_points_ranking');
    var a4 = document.getElementById('id_agree_contact_consent');

    if ((a1 && !a1.checked) || (a2 && !a2.checked) || (a3 && !a3.checked) || (a4 && !a4.checked)) {
      e.preventDefault();
      if (typeof Swal !== 'undefined') {
        Swal.fire({
          icon: 'warning',
          title: 'Agreement Required',
          text: 'You must accept all four agreements to submit your application.',
          confirmButtonColor: '#00629B',
        });
      }
      return;
    }

    // Guard: bio over 50 words
    if (form.getAttribute('data-bio-over') === 'true') {
      e.preventDefault();
      if (typeof Swal !== 'undefined') {
        Swal.fire({
          icon: 'warning',
          title: 'Bio too long',
          text: 'The bio must be 50 words or fewer.',
          confirmButtonColor: '#00629B',
        });
      }
      if (bio) {
        window.goToStep(3);
        bio.focus();
      }
      return;
    }

    // AJAX path
    e.preventDefault();
    setBusy(true);

    if (typeof Swal !== 'undefined') {
      Swal.fire({
        title: "Submitting...",
        text: "Submitting your application. Please wait.",
        allowOutsideClick: false,
        didOpen: function () {
          Swal.showLoading();
        },
      });
    }

    fetch(form.action, {
      method: 'POST',
      body: new FormData(form),
      headers: { 'X-CSRFToken': csrfToken(), 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin'
    })
      .then(function (res) {
        return res.json().catch(function () { return null; }).then(function (data) {
          return { ok: res.ok, data: data };
        });
      })
      .then(function (r) {
        if (r.ok && r.data && r.data.success) {
          if (typeof Swal !== 'undefined') {
            Swal.fire({
              icon: "success",
              title: "Application Received!",
              text: "Thank you for applying to be a SPARC Ambassador!",
              confirmButtonColor: "#00629B",
            }).then(function () {
              showConfirmation();
            });
          } else {
            showConfirmation();
          }
        } else if (r.data && r.data.errors) {
          setBusy(false);
          renderErrors(r.data.errors);
          if (typeof Swal !== 'undefined') {
            var msg = r.data.message || "Please fill in all the required fields correctly!";
            Swal.fire({
              icon: "error",
              title: "Submission Incomplete",
              text: msg,
              confirmButtonColor: "#00629B",
            });
          }
        } else {
          nativeSubmit();
        }
      })
      .catch(function () {
        nativeSubmit();
      });
  });

  // Check if page loaded with server-rendered errors (non-AJAX postback)
  for (var s = 1; s <= 5; s++) {
    var stepSection = document.getElementById('step' + s);
    if (stepSection && stepSection.querySelector('.errorlist')) {
      window.goToStep(s);
      break;
    }
  }
})();
