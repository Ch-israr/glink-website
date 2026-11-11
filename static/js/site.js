/* Glink public site JS.
 * - Refreshes sizes/FAQ from /api/content (server-rendered content stays as fallback).
 * - Builds the quote/contact form, stores the enquiry via /api/leads,
 *   then opens WhatsApp with the message pre-filled.
 * - Size picker on the Book page.
 */
(function () {
  var WA_LINK = "https://wa.me/971529231913";
  var WA_NUMBER = "+971 52 923 1913";
  var REFERRAL_SOURCES = [
    "Google Ads", "Facebook", "Instagram", "Movers", "Drive by Signboard DIP",
    "Friends or Family", "Employee Referrals", "Customer Referrals", "Others"
  ];

  function fmtPrice(v) {
    return "AED " + Number(v).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function sizeImage(sqft) {
    var map = { 50: "real-50sqft-unit-clean.jpg", 80: "real-80sqft-unit-clean.jpg", 100: "real-100sqft-unit-clean.jpg", 150: "real-150sqft-unit-clean.jpg", 180: "180sqft-corridor-2048.jpg" };
    return map[sqft] || "facility-interior-2048.jpg";
  }
  function sizeNote(sqft) {
    return sqft === 180
      ? "Corridor view — our 180 sqft units are the largest we offer."
      : "Our real " + sqft + " sqft unit at our Al Sajaa facility.";
  }

  function renderSizes(sizes) {
    var cards = sizes.map(function (s) {
      return '<article class="size-card" data-sqft="' + s.sqft + '">' +
        '<img src="/static/images/' + sizeImage(s.sqft) + '" alt="' + s.sqft + ' sqft storage unit" loading="lazy">' +
        '<div class="size-card-body"><h3>' + s.sqft + ' sq ft</h3>' +
        '<p class="size-label">' + esc(s.label || "") + '</p>' +
        '<p class="size-note">' + sizeNote(s.sqft) + '</p>' +
        '<p class="size-price">from ' + fmtPrice(s.price_monthly) + '<span>/month</span></p>' +
        '<p class="size-vat">incl. VAT</p>' +
        '<a class="btn btn-primary" href="/book?size=' + s.sqft + '">Book this size</a></div></article>';
    }).join("");
    document.querySelectorAll("[data-sizes]").forEach(function (el) { el.innerHTML = cards; });
    var rows = sizes.map(function (s) {
      return "<tr><td>" + s.sqft + " sq ft</td><td>" + esc(s.label || "") + "</td>" +
        "<td>from " + fmtPrice(s.price_monthly) + " / month</td>" +
        '<td><a class="btn btn-small" href="/book?size=' + s.sqft + '">Book</a></td></tr>';
    }).join("");
    document.querySelectorAll("[data-size-rows]").forEach(function (el) { el.innerHTML = rows; });
  }

  function renderFaq(faq) {
    var items = faq.map(function (f) {
      return '<details class="faq-item"><summary>' + esc(f.question) + "</summary><p>" + esc(f.answer) + "</p></details>";
    }).join("");
    document.querySelectorAll("[data-faq]").forEach(function (el) { el.innerHTML = items; });
  }

  function leadFormHtml(sizes) {
    var sizeOptions = '<option value="">Not sure yet</option>' + sizes.map(function (s) {
      return '<option value="' + s.sqft + '">' + s.sqft + " sq ft — from " + fmtPrice(s.price_monthly) + "/month</option>";
    }).join("");
    var refOptions = REFERRAL_SOURCES.map(function (r) {
      return '<option value="' + esc(r) + '">' + esc(r) + "</option>";
    }).join("");
    return '<form class="form lead-form" data-lead-form-el>' +
      '<div class="form-row">' +
      '<div class="form-field"><label for="first_name">First name *</label><input id="first_name" name="first_name" required></div>' +
      '<div class="form-field"><label for="last_name">Last name *</label><input id="last_name" name="last_name" required></div>' +
      "</div>" +
      '<div class="form-row">' +
      '<div class="form-field"><label for="phone">Phone *</label><input id="phone" name="phone" type="tel" required></div>' +
      '<div class="form-field"><label for="email">Email (optional)</label><input id="email" name="email" type="email"></div>' +
      "</div>" +
      '<div class="form-row">' +
      '<div class="form-field"><label for="company">Company (optional)</label><input id="company" name="company"></div>' +
      '<div class="form-field"><label for="size">Unit size</label><select id="size" name="size">' + sizeOptions + "</select></div>" +
      "</div>" +
      '<div class="form-field"><label for="referral_source">How did you hear about us?</label><select id="referral_source" name="referral_source">' + refOptions + "</select></div>" +
      '<div class="form-field"><label for="message">Tell us about your move or storage needs</label><textarea id="message" name="message" placeholder="What are you moving or storing, and where is it going?"></textarea></div>' +
      '<button class="btn btn-primary btn-block" type="submit">Submit</button>' +
      '<p class="form-note">Submitting saves your enquiry with us and opens WhatsApp with your message ready to send.</p>' +
      '<div class="form-success" data-success>Thank you — your enquiry was saved. WhatsApp should now open with your message ready to send. If it did not open, message us directly on WhatsApp at ' + WA_NUMBER + ".</div>" +
      "</form>";
  }

  function bindLeadForms() {
    document.querySelectorAll("[data-lead-form-el]").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var data = {
          first_name: form.first_name.value.trim(),
          last_name: form.last_name.value.trim(),
          phone: form.phone.value.trim(),
          email: form.email.value.trim(),
          company: form.company.value.trim(),
          size: form.size.value,
          message: form.message.value.trim(),
          referral_source: form.referral_source.value
        };
        fetch("/api/leads", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(data)
        }).then(function (r) { return r.json(); }).then(function () {
          var lines = ["Hello Glink, I would like a quote.",
            "Name: " + data.first_name + " " + data.last_name,
            "Phone: " + data.phone];
          if (data.company) lines.push("Company: " + data.company);
          if (data.size) lines.push("Unit size: " + data.size + " sq ft");
          if (data.message) lines.push("Details: " + data.message);
          if (data.referral_source) lines.push("Heard about you via: " + data.referral_source);
          window.open(WA_LINK + "?text=" + encodeURIComponent(lines.join("\n")), "_blank");
          var ok = form.querySelector("[data-success]");
          if (ok) ok.classList.add("show");
          form.querySelector('button[type="submit"]').disabled = true;
        }).catch(function () {
          // Still open WhatsApp even if the save failed, so the enquiry is not lost.
          window.open(WA_LINK, "_blank");
        });
      });
    });
  }

  function initPicker() {
    var picker = document.querySelector("[data-picker]");
    if (!picker) return;
    var params = new URLSearchParams(window.location.search);
    var preselect = params.get("size");
    function selectCard(card) {
      picker.querySelectorAll(".size-card").forEach(function (c) { c.classList.remove("selected"); });
      card.classList.add("selected");
      var sqft = card.getAttribute("data-sqft");
      document.querySelectorAll('select[name="size"]').forEach(function (sel) { sel.value = sqft; });
    }
    if (!picker.dataset.bound) {
      picker.dataset.bound = "1";
      picker.addEventListener("click", function (e) {
        var card = e.target.closest(".size-card");
        if (card) selectCard(card);
      });
    }
    if (preselect) {
      var target = picker.querySelector('[data-sqft="' + preselect + '"]');
      if (target) selectCard(target);
    }
  }

  function init() {
    var forms = document.querySelectorAll("[data-lead-form]");
    function buildForms(sizes) {
      forms.forEach(function (el) { el.innerHTML = leadFormHtml(sizes); });
      bindLeadForms();
      initPicker();
    }
    // Build forms immediately from the server-rendered size cards (fallback),
    // so the form works even if the API is unreachable.
    var fallback = [];
    document.querySelectorAll(".size-card").forEach(function (c) {
      var sqft = parseInt(c.getAttribute("data-sqft"), 10);
      var priceText = (c.querySelector(".size-price") || {}).textContent || "";
      var m = priceText.replace(/[^\d.]/g, "");
      fallback.push({ sqft: sqft, price_monthly: parseFloat(m) || 0, label: (c.querySelector(".size-label") || {}).textContent || "" });
    });
    if (forms.length) buildForms(fallback);
    fetch("/api/content").then(function (r) { return r.json(); }).then(function (content) {
      if (content.business) {
        WA_LINK = content.business.whatsapp_link || WA_LINK;
        WA_NUMBER = content.business.whatsapp_number || WA_NUMBER;
      }
      if (content.sizes && content.sizes.length) {
        renderSizes(content.sizes);
        buildForms(content.sizes);
      }
      if (content.faq && content.faq.length) renderFaq(content.faq);
    }).catch(function () { /* server-rendered content stays */ });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
