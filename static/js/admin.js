/* Glink admin panel JS. */
(function () {
  function msg(text, ok) {
    var el = document.getElementById("admin-msg");
    el.innerHTML = '<p class="' + (ok ? "success-msg" : "error") + '">' + text + "</p>";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  var state = { sizes: [], faq: [], business: {}, me: null };

  function canEdit() {
    return state.me && state.me.role === "admin";
  }
  function canViewLeads() {
    return state.me && (state.me.role === "admin" || state.me.role === "sales" || state.me.role === "accounts");
  }
  // Read-only roles see the same dashboard but cannot change anything:
  // save/add buttons are hidden and every editor input is disabled.
  function applyReadOnly() {
    if (canEdit()) return;
    document.querySelectorAll(".admin-actions").forEach(function (el) { el.style.display = "none"; });
    document.querySelectorAll("#sizes-editor input, #faq-editor input, #faq-editor textarea, #business-editor input").forEach(function (el) { el.disabled = true; });
    document.querySelectorAll("[data-remove-size], [data-remove-faq]").forEach(function (el) { el.style.display = "none"; });
  }
  function applyRole() {
    if (!state.me) return;
    if (state.me.role !== "admin") {
      var usersBtn = document.querySelector('.tab-btn[data-tab="users"]');
      if (usersBtn) usersBtn.style.display = "none";
    }
    if (!canViewLeads()) {
      var leadsBtn = document.querySelector('.tab-btn[data-tab="leads"]');
      if (leadsBtn) leadsBtn.style.display = "none";
    }
    applyReadOnly();
  }

  function setStat(id, value) {
    var el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function renderSizes() {
    document.getElementById("sizes-editor").innerHTML = state.sizes.map(function (s, i) {
      return '<div class="size-row">' +
        '<div class="mini-field"><label>Size (sq ft)</label>' +
        '<input type="number" min="1" value="' + s.sqft + '" data-i="' + i + '" data-f="sqft" aria-label="Size in sqft"></div>' +
        '<div class="mini-field"><label>Price (AED / month)</label>' +
        '<input type="number" min="0" step="0.01" value="' + s.price_monthly + '" data-i="' + i + '" data-f="price_monthly" aria-label="Monthly price AED"></div>' +
        '<div class="mini-field"><label>Label</label>' +
        '<input type="text" value="' + esc(s.label || "") + '" data-i="' + i + '" data-f="label" placeholder="e.g. Studio" aria-label="Label"></div>' +
        '<button class="btn btn-danger btn-small" type="button" data-remove-size="' + i + '">Remove</button></div>';
    }).join("");
    setStat("stat-sizes", state.sizes.length);
    applyReadOnly();
  }
  function renderFaq() {
    document.getElementById("faq-editor").innerHTML = state.faq.map(function (f, i) {
      return '<div class="faq-edit-card">' +
        '<div class="faq-edit-head"><strong>Question ' + (i + 1) + '</strong>' +
        '<button class="btn btn-danger btn-small" type="button" data-remove-faq="' + i + '">Remove</button></div>' +
        '<div class="form-field"><label>Question</label><input type="text" value="' + esc(f.question) + '" data-i="' + i + '" data-f="question"></div>' +
        '<div class="form-field"><label>Answer</label><textarea data-i="' + i + '" data-f="answer">' + esc(f.answer) + "</textarea></div>" +
        "</div>";
    }).join("");
    setStat("stat-faq", state.faq.length);
    applyReadOnly();
  }
  function renderBusiness() {
    var b = state.business;
    var fields = [
      ["business_name", "Business name", ""],
      ["whatsapp_number", "WhatsApp number (shown on the site)", ""],
      ["whatsapp_link", "WhatsApp link (wa.me/...)", "wide"],
      ["address", "Address", "wide"],
      ["price_per_sqft", "Price per sqft (AED)", ""],
      ["storage_location", "Storage location (shown on the site)", ""]
    ];
    document.getElementById("business-editor").innerHTML = fields.map(function (f) {
      return '<div class="form-field' + (f[2] ? " " + f[2] : "") + '"><label>' + f[1] + '</label><input type="text" data-bkey="' + f[0] + '" value="' + esc(b[f[0]] || "") + '"></div>';
    }).join("");
    applyReadOnly();
  }
  function renderLeads(leads) {
    var el = document.getElementById("leads-list");
    setStat("stat-leads", leads.length);
    setStat("leads-count", leads.length);
    if (!leads.length) { el.innerHTML = '<p class="form-note">No enquiries yet.</p>'; return; }
    el.innerHTML = leads.map(function (l) {
      var contact = [esc(l.phone), l.email ? esc(l.email) : "", l.company ? esc(l.company) : ""].filter(Boolean).join(" · ");
      var details = [(l.size ? "Size: " + esc(l.size) + " sq ft" : ""),
        (l.referral_source ? "Via: " + esc(l.referral_source) : "")].filter(Boolean).join(" · ");
      return '<div class="lead-row">' +
        '<div class="lead-head"><strong>' + esc(l.first_name) + " " + esc(l.last_name) + "</strong>" +
        '<span class="meta">#' + l.id + " · " + esc(l.created_at) + " UTC</span></div>" +
        (contact ? '<p class="lead-contact">' + contact + "</p>" : "") +
        (details ? "<p>" + details + "</p>" : "") +
        (l.message ? '<p class="lead-msg">' + esc(l.message) + "</p>" : "") +
        (canEdit()
          ? '<div class="lead-foot"><button class="btn btn-danger btn-small" type="button" data-delete-lead="' + l.id + '">Delete</button></div>'
          : "") +
        "</div>";
    }).join("");
  }
  function renderUsers(users) {
    var el = document.getElementById("users-list");
    if (!users.length) { el.innerHTML = '<p class="form-note">No users yet.</p>'; return; }
    el.innerHTML = users.map(function (u) {
      var meta = (u.builtin ? "Main admin · password lives in Render settings" : "Added " + esc(u.created_at || "")) + (u.active ? "" : " · Deactivated");
      var actions = "";
      if (!u.builtin) {
        actions = '<div class="user-actions">' +
          '<button class="btn btn-small" type="button" data-reset-user="' + u.id + '">Reset password</button>' +
          '<button class="btn btn-small" type="button" data-toggle-user="' + u.id + '" data-active="' + (u.active ? 0 : 1) + '">' + (u.active ? "Deactivate" : "Activate") + "</button>" +
          '<button class="btn btn-danger btn-small" type="button" data-delete-user="' + u.id + '">Remove</button></div>';
      }
      return '<div class="user-row' + (u.active ? "" : " inactive") + '">' +
        '<div class="user-id"><strong>' + esc(u.username) + '</strong> <span class="role-badge">' + esc(u.role) + "</span>" +
        '<div class="meta">' + meta + "</div></div>" + actions + "</div>";
    }).join("");
  }

  function loadContent() {
    fetch("/api/content").then(function (r) { return r.json(); }).then(function (c) {
      state.sizes = c.sizes || [];
      state.faq = c.faq || [];
      state.business = c.business || {};
      renderSizes(); renderFaq(); renderBusiness();
    });
  }
  function loadLeads() {
    fetch("/admin/api/leads").then(function (r) { return r.json(); }).then(function (d) {
      renderLeads(d.leads || []);
    }).catch(function () {
      document.getElementById("leads-list").innerHTML = '<p class="error">Could not load enquiries.</p>';
    });
  }
  function loadUsers() {
    fetch("/admin/api/users").then(function (r) { return r.json(); }).then(function (d) {
      if (d.ok) renderUsers(d.users || []);
      else document.getElementById("users-list").innerHTML = '<p class="error">' + esc(d.error || "Could not load users.") + "</p>";
    }).catch(function () {
      document.getElementById("users-list").innerHTML = '<p class="error">Could not load users.</p>';
    });
  }

  function collectSizes() {
    var rows = [];
    document.querySelectorAll("#sizes-editor [data-f]").forEach(function (input) {
      var i = parseInt(input.getAttribute("data-i"), 10);
      rows[i] = rows[i] || {};
      rows[i][input.getAttribute("data-f")] = input.value;
    });
    return rows.filter(Boolean);
  }
  function collectFaq() {
    var rows = [];
    document.querySelectorAll("#faq-editor [data-f]").forEach(function (input) {
      var i = parseInt(input.getAttribute("data-i"), 10);
      rows[i] = rows[i] || {};
      rows[i][input.getAttribute("data-f")] = input.value;
    });
    return rows.filter(Boolean);
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Tabs
    document.querySelectorAll(".tab-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".tab-btn").forEach(function (b) { b.classList.remove("active"); });
        document.querySelectorAll(".tab-panel").forEach(function (p) { p.classList.remove("active"); });
        btn.classList.add("active");
        document.getElementById("tab-" + btn.getAttribute("data-tab")).classList.add("active");
        if (btn.getAttribute("data-tab") === "leads") loadLeads();
        if (btn.getAttribute("data-tab") === "users") loadUsers();
      });
    });

    // Who is signed in? The role decides which tabs and buttons are shown.
    // Fail closed: if the check fails, treat the session as read-only viewer.
    fetch("/admin/api/me").then(function (r) { return r.json(); }).then(function (d) {
      if (d.ok && d.user) state.me = d.user;
      else state.me = { username: "", role: "viewer" };
      applyRole();
      loadContent();
      if (canViewLeads()) loadLeads();
    }).catch(function () {
      state.me = { username: "", role: "viewer" };
      applyRole();
      loadContent();
    });

    document.getElementById("add-size").addEventListener("click", function () {
      state.sizes.push({ sqft: 200, price_monthly: 0, label: "" });
      renderSizes();
    });
    document.getElementById("add-faq").addEventListener("click", function () {
      state.faq.push({ question: "", answer: "" });
      renderFaq();
    });
    document.getElementById("sizes-editor").addEventListener("click", function (e) {
      var i = e.target.getAttribute("data-remove-size");
      if (i !== null) { state.sizes.splice(parseInt(i, 10), 1); renderSizes(); }
    });
    document.getElementById("faq-editor").addEventListener("click", function (e) {
      var i = e.target.getAttribute("data-remove-faq");
      if (i !== null) { state.faq.splice(parseInt(i, 10), 1); renderFaq(); }
    });
    document.getElementById("save-sizes").addEventListener("click", function () {
      fetch("/admin/api/sizes", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sizes: collectSizes() })
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.ok) { state.sizes = d.sizes; renderSizes(); msg("Sizes saved — the live site now shows the new prices.", true); }
        else msg(d.error || "Could not save sizes.", false);
      });
    });
    document.getElementById("save-faq").addEventListener("click", function () {
      fetch("/admin/api/faq", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ faq: collectFaq() })
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.ok) { state.faq = d.faq; renderFaq(); msg("FAQ saved.", true); }
        else msg(d.error || "Could not save FAQ.", false);
      });
    });
    document.getElementById("save-business").addEventListener("click", function () {
      var values = {};
      document.querySelectorAll("#business-editor [data-bkey]").forEach(function (input) {
        values[input.getAttribute("data-bkey")] = input.value;
      });
      fetch("/admin/api/business", {
        method: "PUT", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ business: values })
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.ok) { state.business = d.business; renderBusiness(); msg("Business info saved.", true); }
        else msg(d.error || "Could not save business info.", false);
      });
    });
    document.getElementById("leads-list").addEventListener("click", function (e) {
      var id = e.target.getAttribute("data-delete-lead");
      if (id === null) return;
      if (!window.confirm("Delete this enquiry?")) return;
      fetch("/admin/api/leads/" + id, { method: "DELETE" }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.ok) loadLeads();
        else msg(d.error || "Could not delete the enquiry.", false);
      });
    });
    document.getElementById("add-user").addEventListener("click", function () {
      fetch("/admin/api/users", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: document.getElementById("new-username").value,
          password: document.getElementById("new-password").value,
          role: document.getElementById("new-role").value
        })
      }).then(function (r) { return r.json(); }).then(function (d) {
        if (d.ok) {
          renderUsers(d.users);
          msg("User added — they can sign in on the admin login page now.", true);
          document.getElementById("new-username").value = "";
          document.getElementById("new-password").value = "";
        } else msg(d.error || "Could not add user.", false);
      });
    });
    document.getElementById("users-list").addEventListener("click", function (e) {
      var resetId = e.target.getAttribute("data-reset-user");
      var toggleId = e.target.getAttribute("data-toggle-user");
      var deleteId = e.target.getAttribute("data-delete-user");
      if (resetId !== null) {
        var pw = window.prompt("New password for this user (min 8 characters):");
        if (pw === null) return;
        fetch("/admin/api/users/" + resetId + "/reset-password", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ password: pw })
        }).then(function (r) { return r.json(); }).then(function (d) {
          if (d.ok) msg("Password reset — their old sessions are signed out.", true);
          else msg(d.error || "Could not reset the password.", false);
        });
        return;
      }
      if (toggleId !== null) {
        var active = e.target.getAttribute("data-active") === "1";
        fetch("/admin/api/users/" + toggleId + "/active", {
          method: "POST", headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ active: active })
        }).then(function (r) { return r.json(); }).then(function (d) {
          if (d.ok) { renderUsers(d.users); msg(active ? "User activated." : "User deactivated — they are signed out.", true); }
          else msg(d.error || "Could not change the user.", false);
        });
        return;
      }
      if (deleteId !== null) {
        if (!window.confirm("Remove this user? They will be signed out immediately.")) return;
        fetch("/admin/api/users/" + deleteId, { method: "DELETE" }).then(function (r) { return r.json(); }).then(function (d) {
          if (d.ok) { renderUsers(d.users); msg("User removed.", true); }
          else msg(d.error || "Could not remove the user.", false);
        });
      }
    });
  });
})();
