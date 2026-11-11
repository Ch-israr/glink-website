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

  var state = { sizes: [], faq: [], business: {} };

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
        '<div class="lead-foot"><button class="btn btn-danger btn-small" type="button" data-delete-lead="' + l.id + '">Delete</button></div>' +
        "</div>";
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
      });
    });

    loadContent();
    loadLeads();

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
  });
})();
