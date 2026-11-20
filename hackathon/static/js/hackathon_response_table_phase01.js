document.addEventListener("DOMContentLoaded", function () {
  // 1. Initialize Particles Background
  if (typeof particlesJS === "function" && document.getElementById("particles-js")) {
    particlesJS("particles-js", {
      particles: {
        number: { value: 40 },
        color: { value: "#fff" },
        size: { value: 3 },
        move: { speed: 1 },
      },
    });
  }

  const root = document.getElementById("hackathonResponseRoot");
  if (!root) return;

  const saveSelectedUrl = root.dataset.saveSelectedUrl;
  const sendPhase02EmailUrl = root.dataset.sendPhase02EmailUrl;
  const csrfToken = root.dataset.csrfToken;
  const searchInput = document.getElementById("tableSearch");
  const selectAllBtn = document.getElementById("selectAllBtn");
  const saveBtn = document.getElementById("saveBtn");
  const sendMailBtn = document.getElementById("sendMailBtn");

  // 2. Deep Cross-Member Live Search Filter
  if (searchInput) {
    searchInput.addEventListener("input", function () {
      const query = this.value.toLowerCase().trim();
      document.querySelectorAll("tbody tr.data-row").forEach((row) => {
        const haystack = (row.dataset.search || row.innerText || "")
          .replace(/\s+/g, " ")
          .toLowerCase();
        row.style.display = haystack.includes(query) ? "" : "none";
      });
    });
  }

  // 3. Row Click Navigation (Ignoring Checkbox Clicks)
  document.querySelectorAll("tbody tr.data-row").forEach((row) => {
    row.addEventListener("click", function (e) {
      if (e.target.closest("input") || e.target.closest("label") || e.target.closest("button")) {
        return;
      }
      const href = row.dataset.href;
      if (href) {
        window.location.href = href;
      }
    });
  });

  // 4. Select All / Deselect All (Scoped to Currently Visible Rows)
  if (selectAllBtn) {
    selectAllBtn.addEventListener("click", function () {
      const visibleCheckboxes = [
        ...document.querySelectorAll("tbody tr.data-row"),
      ]
        .filter((row) => row.style.display !== "none")
        .map((row) => row.querySelector(".phase2Check:not(:disabled)"))
        .filter(Boolean);

      if (!visibleCheckboxes.length) return;

      const allChecked = visibleCheckboxes.every((cb) => cb.checked);
      visibleCheckboxes.forEach((cb) => {
        cb.checked = !allChecked;
      });
    });
  }

  // 5. Save Selections Bulk Endpoint
  if (saveBtn && saveSelectedUrl) {
    saveBtn.addEventListener("click", async function () {
      const selectedIds = [
        ...document.querySelectorAll(".phase2Check:checked:not(:disabled)"),
      ].map((cb) => parseInt(cb.dataset.id, 10));

      if (selectedIds.length === 0) {
        const proceed = confirm(
          "No teams are currently checked. Save and mark all teams as Not Selected?"
        );
        if (!proceed) return;
      }

      saveBtn.disabled = true;
      const originalText = saveBtn.textContent;
      saveBtn.textContent = "Saving...";

      try {
        const response = await fetch(saveSelectedUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({ selected_ids: selectedIds }),
        });

        const data = await response.json();
        if (response.ok && data.status === "success") {
          alert(data.message || "Team selections updated successfully!");
          window.location.reload();
        } else {
          alert(data.message || "Failed to save team selections.");
        }
      } catch (err) {
        console.error("Error saving team selections:", err);
        alert("Network error while saving team selections.");
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
      }
    });
  }

  // 6. Send Phase-2 Email Action
  if (sendMailBtn && sendPhase02EmailUrl) {
    sendMailBtn.addEventListener("click", async function () {
      if (
        !confirm(
          "Phase-2 invitation emails will be sent to the Team Leaders of all selected teams now. Are you sure?"
        )
      ) {
        return;
      }

      sendMailBtn.disabled = true;
      const originalText = sendMailBtn.textContent;
      sendMailBtn.textContent = "Sending...";

      try {
        const response = await fetch(sendPhase02EmailUrl, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
        });

        const data = await response.json();
        if (response.ok && data.status === "success") {
          alert(data.message || "Successfully emailed to selected team leaders!");
          window.location.reload();
        } else {
          alert(data.message || "Failed to send Phase-2 emails.");
        }
      } catch (err) {
        console.error("Error sending Phase-2 emails:", err);
        alert("Network error while sending Phase-2 emails.");
      } finally {
        sendMailBtn.disabled = false;
        sendMailBtn.textContent = originalText;
      }
    });
  }
});
