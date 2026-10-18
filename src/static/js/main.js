(function () {
  "use strict";

  // ---------- Toasts (Django messages) ----------
  function initToasts() {
    const container = document.querySelector(".toast-container");
    const messages = document.querySelectorAll("[data-toast-message]");
    if (!container) return;

    messages.forEach(function (el) {
      const type = el.getAttribute("data-toast-message") || "info";
      const text = el.textContent.trim();

      const toast = document.createElement("div");
      toast.className = "app-toast " + type;
      toast.innerHTML =
        '<span class="toast-dot"></span>' +
        '<span class="toast-body"></span>' +
        '<button class="toast-close" aria-label="Close">&times;</button>';
      toast.querySelector(".toast-body").textContent = text;

      let timer;
      const close = function () {
        if (toast.classList.contains("is-leaving")) return;
        toast.classList.add("is-leaving");
        clearTimeout(timer);
        setTimeout(function () {
          toast.remove();
        }, 300);
      };

      toast.querySelector(".toast-close").addEventListener("click", close);
      container.appendChild(toast);
      timer = setTimeout(close, 5000);
      el.remove();
    });
  }

  // ---------- Scroll reveal ----------
  function initReveal() {
    const els = document.querySelectorAll("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (el) {
        el.classList.add("is-visible");
      });
      return;
    }

    const io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );

    els.forEach(function (el) {
      io.observe(el);
    });
  }

  // ---------- Sending spinner ----------
  function initSendingSpinner() {
    document.querySelectorAll("form").forEach(function (form) {
      form.addEventListener("submit", function () {
        const btn = form.querySelector("[data-submit-btn]");
        if (!btn) return;
        if (!form.checkValidity()) return;

        btn.disabled = true;
        const spinner = document.createElement("span");
        spinner.className = "spinner-border spinner-border-sm me-2";
        spinner.setAttribute("role", "status");
        btn.prepend(spinner);

        const label = btn.querySelector("[data-submit-label]");
        if (label) label.textContent = "Sending…";
      });
    });
  }

  // ---------- Dropzones ----------
  function initDropzones() {
    document.querySelectorAll(".dropzone").forEach(function (dz) {
      const input = dz.querySelector('input[type="file"]');
      if (!input) return;
      const fileEl = dz.querySelector(".dz-file");

      const setFiles = function (files) {
        if (files && files.length) {
          const names = Array.prototype.map
            .call(files, function (f) {
              return f.name;
            })
            .join(", ");
          if (fileEl) fileEl.textContent = names;
          dz.classList.add("has-file");
        }
      };

      input.addEventListener("change", function () {
        setFiles(input.files);
      });

      ["dragenter", "dragover"].forEach(function (ev) {
        dz.addEventListener(ev, function () {
          dz.classList.add("is-dragover");
        });
      });
      ["dragleave", "drop"].forEach(function (ev) {
        dz.addEventListener(ev, function () {
          dz.classList.remove("is-dragover");
        });
      });
      dz.addEventListener("drop", function (e) {
        if (e.dataTransfer && e.dataTransfer.files.length) {
          e.preventDefault();
          input.files = e.dataTransfer.files;
          setFiles(input.files);
          input.dispatchEvent(new Event("change", { bubbles: true }));
        }
      });
    });
  }

  // ---------- Recipient file parsing (email page) ----------
  function initRecipientParser() {
    const fileInput = document.getElementById("csv");
    const emailKeySelect = document.getElementById("email_key");
    if (!fileInput || !emailKeySelect) return;

    const parseWorkbook = function (data) {
      const wb = XLSX.read(data, { type: "array" });
      const sheet = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(sheet, {
        header: 1,
        defval: "",
      });
      if (!rows || !rows.length) return null;

      const columns = rows[0].map(String);
      const dataRows = rows
        .slice(1)
        .filter(function (r) {
          return r.some(function (c) {
            return String(c).trim() !== "";
          });
        });
      return { columns: columns, rowCount: dataRows.length };
    };

    const populateColumns = function (columns) {
      emailKeySelect.innerHTML = "";
      columns.forEach(function (col) {
        const opt = document.createElement("option");
        opt.value = col;
        opt.textContent = col;
        emailKeySelect.appendChild(opt);
      });

      const hint = document.getElementById("email_key_hint");
      if (hint) {
        hint.textContent = columns.length
          ? columns.length + " column(s) detected"
          : "No columns detected";
      }
    };

    const setupSlider = function (count) {
      const slider = document.getElementById("slider-range");
      const startEl = document.getElementById("start");
      const stopEl = document.getElementById("stop");
      const countEl = document.getElementById("recipient-count");
      if (!slider || !startEl || !stopEl) return;

      if (count < 1) {
        slider.innerHTML = "";
        if (countEl) countEl.textContent = "0";
        return;
      }

      const updateCount = function () {
        const s = parseInt(startEl.value, 10) || 1;
        const t = parseInt(stopEl.value, 10) || count;
        if (countEl) countEl.textContent = Math.max(0, t - s + 1);
      };

      $(slider).slider({
        range: true,
        min: 1,
        max: count,
        values: [1, count],
        slide: function (event, ui) {
          startEl.value = ui.values[0];
          stopEl.value = ui.values[1];
          updateCount();
        },
      });

      startEl.value = 1;
      stopEl.value = count;
      updateCount();
    };

    const readFile = function (file) {
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function () {
        let result = null;
        try {
          result = parseWorkbook(reader.result);
        } catch (err) {
          console.error("Failed to parse file", err);
        }
        if (!result) {
          populateColumns([]);
          setupSlider(0);
          return;
        }
        populateColumns(result.columns);
        setupSlider(result.rowCount);
      };
      reader.readAsArrayBuffer(file);
    };

    fileInput.addEventListener("change", function () {
      readFile(fileInput.files[0]);
    });
  }

  // ---------- Bootstrap active scrollspy (help page) ----------
  function initHelpScrollspy() {
    const sidebar = document.querySelector(".help-sidebar");
    if (!sidebar) return;

    const links = sidebar.querySelectorAll(".nav-link");
    const sections = Array.prototype.map
      .call(links, function (link) {
        return document.querySelector(link.getAttribute("href"));
      })
      .filter(Boolean);

    if (!("IntersectionObserver" in window) || !sections.length) return;

    const setActive = function (id) {
      links.forEach(function (link) {
        link.classList.toggle(
          "active",
          link.getAttribute("href") === "#" + id
        );
      });
    };

    const io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            setActive(entry.target.id);
          }
        });
      },
      { rootMargin: "-40% 0px -55% 0px" }
    );

    sections.forEach(function (section) {
      io.observe(section);
    });
  }

  // ---------- Init ----------
  document.addEventListener("DOMContentLoaded", function () {
    initToasts();
    initReveal();
    initSendingSpinner();
    initDropzones();
    initRecipientParser();
    initHelpScrollspy();
  });
})();
