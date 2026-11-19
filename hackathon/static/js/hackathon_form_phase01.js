document.addEventListener("DOMContentLoaded", function () {
  // 1. Initialize Particles Background (matching landingpage.html & response_table.html)
  if (typeof particlesJS === "function" && document.getElementById("particles-js")) {
    particlesJS("particles-js", {
      particles: {
        number: { value: 40, density: { enable: true, value_area: 800 } },
        color: { value: "#ffffff" },
        shape: { type: "circle" },
        opacity: { value: 0.9, random: true },
        size: { value: 3, random: true },
        line_linked: { enable: false },
        move: { enable: true, speed: 1, random: true, out_mode: "out" },
      },
      interactivity: {
        detect_on: "canvas",
        events: { onhover: { enable: false }, onclick: { enable: false }, resize: true },
      },
      retina_detect: true,
    });
  }

  const root = document.getElementById("hackathonFormRoot");
  if (!root) return;

  const submitUrl = root.dataset.submitUrl;
  const togglePublishUrl = root.dataset.togglePublishUrl;
  const csrfToken = root.dataset.csrfToken;

  // 2. Staff Independent Publish / Unpublish Toggle
  const publishToggleBtn = document.getElementById("publishToggleBtn");
  const publishToggleText = document.getElementById("publishToggleText");

  if (publishToggleBtn && togglePublishUrl) {
    publishToggleBtn.addEventListener("click", async function () {
      publishToggleBtn.disabled = true;
      try {
        const res = await fetch(togglePublishUrl, {
          method: "POST",
          headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/json",
          },
        });
        const data = await res.json();
        if (res.ok && data.success) {
          const live = Boolean(data.is_published);
          publishToggleBtn.classList.toggle("is-live", live);
          publishToggleBtn.classList.toggle("is-closed", !live);
          publishToggleText.textContent = live
            ? "Form Published (Click to Close)"
            : "Form Unpublished (Click to Open)";
        } else {
          alert(data.message || "Failed to update Hackathon publish status.");
        }
      } catch (err) {
        console.error("Error toggling publish state:", err);
        alert("Network error while toggling Hackathon form status.");
      } finally {
        publishToggleBtn.disabled = false;
      }
    });
  }

  // Exit early if the form is not rendered (public closed state)
  const form = document.getElementById("hackathonPhase01Form");
  if (!form) return;

  const teamSizeSelect = document.getElementById("team_size");
  const member3Card = document.getElementById("member-card-3");
  const leaderEmailInput = document.getElementById("leader_email");
  const leaderPhoneInput = document.getElementById("leader_phone");
  const member1EmailInput = document.getElementById("member_1_email");
  const member1PhoneInput = document.getElementById("member_1_phone_number");
  const globalErrorBanner = document.getElementById("globalErrorBanner");
  const successPanel = document.getElementById("successPanel");
  const successMessageText = document.getElementById("successMessageText");
  const submitBtn = document.getElementById("submitHackathonBtn");
  const registerAnotherBtn = document.getElementById("registerAnotherBtn");

  // 3. Synchronize Section 1 Leader Contact into Member 1 Card
  function syncLeaderContact() {
    if (member1EmailInput && leaderEmailInput) {
      member1EmailInput.value = leaderEmailInput.value.trim();
    }
    if (member1PhoneInput && leaderPhoneInput) {
      member1PhoneInput.value = leaderPhoneInput.value.trim();
    }
  }

  leaderEmailInput.addEventListener("input", syncLeaderContact);
  leaderPhoneInput.addEventListener("input", syncLeaderContact);
  syncLeaderContact();

  // 4. Conditional Section 3 IEEE Fields Per Member
  function updateIeeeSection(memberIndex) {
    const selectedRadio = form.querySelector(
      `input[name="member_${memberIndex}_is_ieee"]:checked`
    );
    const isIeee = selectedRadio && selectedRadio.value === "yes";
    const ieeeBox = document.getElementById(`member_${memberIndex}_ieee_section`);
    if (!ieeeBox) return;

    const card = document.getElementById(`member-card-${memberIndex}`);
    const cardVisible = card && !card.classList.contains("hidden-section");

    ieeeBox.classList.toggle("hidden-section", !isIeee);

    ieeeBox.querySelectorAll("[data-ieee-required='true']").forEach((el) => {
      el.required = Boolean(isIeee && cardVisible);
    });

    if (!isIeee) {
      ieeeBox.querySelectorAll("input, select").forEach((el) => {
        el.value = "";
        el.classList.remove("has-error");
      });
      ieeeBox.querySelectorAll(".field-error").forEach((errEl) => {
        errEl.textContent = "";
        errEl.classList.remove("is-visible");
      });
    }
  }

  form.querySelectorAll(".ieee-toggle").forEach((radio) => {
    radio.addEventListener("change", function () {
      updateIeeeSection(this.dataset.memberIndex);
    });
  });

  // 5. Dynamic 2 vs. 3 Member Switcher
  function updateMember3Visibility() {
    const showMember3 = teamSizeSelect.value === "3";
    member3Card.classList.toggle("hidden-section", !showMember3);

    member3Card.querySelectorAll("[data-required='true']").forEach((el) => {
      el.required = showMember3;
    });

    updateIeeeSection("3");
  }

  teamSizeSelect.addEventListener("change", updateMember3Visibility);
  updateMember3Visibility();

  // 6. Error Display Helpers
  function clearAllErrors() {
    globalErrorBanner.textContent = "";
    globalErrorBanner.classList.add("hidden-section");

    form.querySelectorAll(".has-error").forEach((el) => {
      el.classList.remove("has-error");
    });

    form.querySelectorAll(".field-error").forEach((el) => {
      el.textContent = "";
      el.classList.remove("is-visible");
    });
  }

  function showFieldError(fieldKey, message) {
    const errorEl = form.querySelector(`[data-error-for="${fieldKey}"]`);
    if (errorEl) {
      errorEl.textContent = Array.isArray(message) ? message.join(" ") : message;
      errorEl.classList.add("is-visible");
    }

    const inputEl = document.getElementById(fieldKey);
    if (inputEl) {
      inputEl.classList.add("has-error");
    }
  }

  function showGlobalError(message) {
    globalErrorBanner.textContent = message;
    globalErrorBanner.classList.remove("hidden-section");
  }

  function scrollToFirstError() {
    const firstVisible = form.querySelector(".field-error.is-visible");
    if (firstVisible) {
      firstVisible.scrollIntoView({ behavior: "smooth", block: "center" });
    } else if (!globalErrorBanner.classList.contains("hidden-section")) {
      globalErrorBanner.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }

  // 7. Build Structured JSON Payload & Run Client-Side Validation
  function normalizePhone(raw) {
    return (raw || "").replace(/[\s\-]+/g, "").trim();
  }

  function buildAndValidatePayload() {
    const errors = {};
    const teamNameRegex = /^[A-Za-z0-9]+_[A-Za-z0-9]+$/;
    const phoneRegex = /^01[0-9]{9}$/;
    const ieeeRegex = /^\d{8}$/;

    const teamName = document.getElementById("team_name").value.trim();
    const teamSize = parseInt(teamSizeSelect.value, 10);
    const uniDistRadio = form.querySelector('input[name="university_distribution"]:checked');
    const uniDistribution = uniDistRadio ? uniDistRadio.value : "";
    const leaderEmail = leaderEmailInput.value.trim();
    const leaderPhone = normalizePhone(leaderPhoneInput.value);
    const leaderSignature = document.getElementById("leader_signature").value.trim();

    if (!teamName) {
      errors.team_name = "Team name is required.";
    } else if (!teamNameRegex.test(teamName)) {
      errors.team_name =
        "Use InstitutionShortName_UniqueName (letters/numbers with exactly one underscore).";
    }

    if (teamSize !== 2 && teamSize !== 3) {
      errors.team_size = "Please select either 2 or 3 team members.";
    }

    if (!uniDistribution) {
      errors.university_distribution = "Please select your university distribution.";
    }

    if (!leaderEmail || !leaderEmailInput.checkValidity()) {
      errors.leader_email = "Enter a valid Team Leader email address.";
    }

    if (!phoneRegex.test(leaderPhone)) {
      errors.leader_phone = "Phone number must be 11 digits starting with 01.";
    }

    const memberCount = teamSize === 3 ? 3 : 2;
    const members = [];
    const seenEmails = new Set();
    const seenStudentIds = new Set();

    for (let idx = 1; idx <= memberCount; idx++) {
      const card = document.getElementById(`member-card-${idx}`);
      const getVal = (field) => {
        const el = card.querySelector(`[data-field="${field}"]`);
        return el ? el.value.trim() : "";
      };

      const fullName = getVal("full_name");
      const email = idx === 1 ? leaderEmail : getVal("email");
      const phone = idx === 1 ? leaderPhone : normalizePhone(getVal("phone_number"));
      const university = getVal("university");
      const department = getVal("department");
      const academicYear = getVal("academic_year");
      const studentId = getVal("student_id");
      const gender = getVal("gender");

      const ieeeRadio = form.querySelector(`input[name="member_${idx}_is_ieee"]:checked`);
      const isIeee = Boolean(ieeeRadio && ieeeRadio.value === "yes");
      const ieeeNo = isIeee ? getVal("ieee_membership_no") : "";
      const ieeeGrade = isIeee ? getVal("ieee_membership_grade") : "";
      const ieeeBranch = isIeee ? getVal("ieee_student_branch") : "";
      const ieeePosition = isIeee ? getVal("ieee_volunteer_position") : "";

      if (!fullName) errors[`member_${idx}_full_name`] = "Full name is required.";

      if (idx > 1) {
        const emailEl = document.getElementById(`member_${idx}_email`);
        if (!email || (emailEl && !emailEl.checkValidity())) {
          errors[`member_${idx}_email`] = "Enter a valid email address.";
        }
        if (!phoneRegex.test(phone)) {
          errors[`member_${idx}_phone_number`] = "Phone number must be 11 digits starting with 01.";
        }
      }

      if (email) {
        if (seenEmails.has(email.toLowerCase())) {
          errors[`member_${idx}_email`] = "Duplicate email within the same team is not allowed.";
        } else {
          seenEmails.add(email.toLowerCase());
        }
      }

      if (!university) errors[`member_${idx}_university`] = "University is required.";
      if (!department) errors[`member_${idx}_department`] = "Department is required.";
      if (!academicYear) errors[`member_${idx}_academic_year`] = "Current year is required.";

      if (!studentId) {
        errors[`member_${idx}_student_id`] = "Student ID is required.";
      } else if (seenStudentIds.has(studentId.toLowerCase())) {
        errors[`member_${idx}_student_id`] = "Duplicate Student ID within the same team is not allowed.";
      } else {
        seenStudentIds.add(studentId.toLowerCase());
      }

      if (isIeee) {
        if (!ieeeRegex.test(ieeeNo)) {
          errors[`member_${idx}_ieee_membership_no`] = "IEEE membership number must be exactly 8 digits.";
        }
        if (!ieeeGrade) {
          errors[`member_${idx}_ieee_membership_grade`] = "Select an IEEE membership grade.";
        }
        if (!ieeeBranch) {
          errors[`member_${idx}_ieee_student_branch`] = "IEEE Student Branch is required.";
        }
      }

      members.push({
        full_name: fullName,
        email: email,
        phone_number: phone,
        university: university,
        department: department,
        academic_year: academicYear,
        student_id: studentId,
        gender: gender,
        is_ieee_member: isIeee,
        ieee_membership_no: ieeeNo,
        ieee_membership_grade: ieeeGrade,
        ieee_student_branch: ieeeBranch,
        ieee_volunteer_position: ieeePosition,
      });
    }

    const agreements = {};
    let allAgreed = true;
    form.querySelectorAll(".agreement-checkbox").forEach((cb) => {
      agreements[cb.dataset.agreementKey] = cb.checked;
      if (!cb.checked) allAgreed = false;
    });

    if (!allAgreed) {
      errors.__all__ = "You must confirm all 7 declarations before submitting.";
    }

    if (!leaderSignature) {
      errors.leader_signature = "Team Leader's typed signature is required.";
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
      payload: {
        team_name: teamName,
        team_size: teamSize,
        university_distribution: uniDistribution,
        leader_email: leaderEmail,
        leader_phone: leaderPhone,
        leader_signature: leaderSignature,
        agreements,
        members,
      },
    };
  }

  // 8. Form Submit Handler
  form.addEventListener("submit", async function (e) {
    e.preventDefault();
    clearAllErrors();
    syncLeaderContact();

    const { isValid, errors, payload } = buildAndValidatePayload();

    if (!isValid) {
      Object.entries(errors).forEach(([key, msg]) => showFieldError(key, msg));
      showGlobalError("Please fix the highlighted fields below before submitting.");
      scrollToFirstError();
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting Team Registration...";

    try {
      const response = await fetch(submitUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(payload),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        form.classList.add("hidden-section");
        successMessageText.textContent = data.message;
        successPanel.classList.remove("hidden-section");
        successPanel.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        if (data.errors && typeof data.errors === "object") {
          Object.entries(data.errors).forEach(([key, msgs]) => showFieldError(key, msgs));
        }
        showGlobalError(data.message || "Registration failed. Please check your entries.");
        scrollToFirstError();
      }
    } catch (err) {
      console.error("Submission error:", err);
      showGlobalError("Network error while submitting your registration. Please try again.");
      scrollToFirstError();
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit Team Registration";
    }
  });

  if (registerAnotherBtn) {
    registerAnotherBtn.addEventListener("click", function () {
      form.reset();
      clearAllErrors();
      syncLeaderContact();
      updateMember3Visibility();
      updateIeeeSection("1");
      updateIeeeSection("2");
      updateIeeeSection("3");
      successPanel.classList.add("hidden-section");
      form.classList.remove("hidden-section");
    });
  }
});