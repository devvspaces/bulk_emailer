(function () {
  "use strict";

  function el(id) {
    return document.getElementById(id);
  }

  // ---------- Toasts (Django messages) ----------
  function initToasts() {
    const container = document.querySelector(".toast-container");
    const messages = document.querySelectorAll("[data-toast-message]");
    if (!container) return;

    messages.forEach(function (msg) {
      const type = msg.getAttribute("data-toast-message") || "info";
      const text = msg.textContent.trim();

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
      msg.remove();
    });
  }

  // ---------- Scroll reveal ----------
  function initReveal() {
    const els = document.querySelectorAll("[data-reveal]");
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (target) {
        target.classList.add("is-visible");
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

    els.forEach(function (target) {
      io.observe(target);
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

  // ---------- CSV parsing ----------
  function parseCsvText(text) {
    const result = { headers: [], rows: [], lines: [] };
    if (typeof text !== "string") return result;
    text = text.replace(/^\uFEFF/, "");

    const raw = [];
    let cells = [];
    let field = "";
    let inQuotes = false;
    let line = 1;

    const endField = function () {
      cells.push(field);
      field = "";
    };
    const endRow = function () {
      raw.push({ cells: cells, line: line });
      cells = [];
      line += 1;
    };

    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      if (inQuotes) {
        if (ch === '"') {
          if (text[i + 1] === '"') {
            field += '"';
            i += 1;
          } else {
            inQuotes = false;
          }
        } else {
          field += ch;
        }
      } else if (ch === '"') {
        inQuotes = true;
      } else if (ch === ",") {
        endField();
      } else if (ch === "\n") {
        endField();
        endRow();
      } else if (ch === "\r") {
        if (text[i + 1] === "\n") i += 1;
        endField();
        endRow();
      } else {
        field += ch;
      }
    }

    if (inQuotes || field !== "" || cells.length) {
      endField();
      endRow();
    }

    const kept = raw.filter(function (r) {
      return r.cells.some(function (c) {
        return String(c).trim() !== "";
      });
    });

    if (!kept.length) return result;

    result.headers = kept[0].cells.map(function (c) {
      return c.trim();
    });
    kept.slice(1).forEach(function (r) {
      result.rows.push(r.cells);
      result.lines.push(r.line);
    });
    return result;
  }

  function rowsToParsed(rows) {
    const result = { headers: [], rows: [], lines: [] };
    if (!rows || !rows.length) return result;
    result.headers = rows[0].map(function (c) {
      return String(c).trim();
    });
    let line = 2;
    rows.slice(1).forEach(function (r) {
      if (r.some(function (c) { return String(c).trim() !== ""; })) {
        result.rows.push(r.map(function (c) { return String(c); }));
        result.lines.push(line);
      }
      line += 1;
    });
    return result;
  }

  function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function isValidPhone(value) {
    return /^\+?[0-9\s\-().]{7,}$/.test(value);
  }

  // ---------- Validation ----------
  function validateRecipients(parsed, recipientColumn, kind) {
    const errors = [];
    const warnings = [];
    const headers = parsed.headers;
    const rows = parsed.rows;
    const lines = parsed.lines;

    if (!headers.length) {
      errors.push({ line: 0, message: "No header row found." });
      return { errors: errors, warnings: warnings, stats: { rows: 0, cols: 0 } };
    }

    headers.forEach(function (h, i) {
      if (!h) {
        errors.push({
          line: 1,
          message: "Column " + (i + 1) + " has an empty header.",
        });
      }
    });

    const seen = {};
    headers.forEach(function (h, i) {
      const key = h.toLowerCase();
      if (h && seen[key] !== undefined) {
        errors.push({
          line: 1,
          message:
            'Duplicate header "' + h + '" (columns ' + (seen[key] + 1) +
            " and " + (i + 1) + ").",
        });
      } else if (h) {
        seen[key] = i;
      }
    });

    const colIndex = headers.findIndex(function (h) {
      return h.toLowerCase() === recipientColumn.toLowerCase();
    });
    if (colIndex === -1) {
      errors.push({
        line: 1,
        message: 'Required "' + recipientColumn + '" column not found.',
      });
      return {
        errors: errors,
        warnings: warnings,
        stats: { rows: rows.length, cols: headers.length },
      };
    }

    if (!rows.length) {
      errors.push({ line: 0, message: "No data rows found below the header." });
    }

    let emptyRecipients = 0;
    rows.forEach(function (row, idx) {
      const line = lines[idx] || idx + 2;

      if (row.length !== headers.length) {
        errors.push({
          line: line,
          message:
            "Expected " + headers.length + " columns but found " + row.length + ".",
        });
      }

      const value = (row[colIndex] || "").trim();
      if (!value) {
        emptyRecipients += 1;
        warnings.push({
          line: line,
          message: "Empty " + recipientColumn + " value.",
        });
      } else if (kind === "email" && !isValidEmail(value)) {
        warnings.push({
          line: line,
          message: '"' + value + '" is not a valid email address.',
        });
      } else if (kind === "phone" && !isValidPhone(value)) {
        warnings.push({
          line: line,
          message: '"' + value + '" is not a valid phone number.',
        });
      }
    });

    if (rows.length && emptyRecipients === rows.length) {
      errors.push({
        line: 0,
        message: "No valid " + recipientColumn + " values found.",
      });
    }

    return {
      errors: errors,
      warnings: warnings,
      stats: { rows: rows.length, cols: headers.length },
    };
  }

  // ---------- Renderers ----------
  function renderIssues(container, issues) {
    if (!container) return;
    container.innerHTML = "";

    const errors = issues.errors;
    const warnings = issues.warnings;
    const stats = issues.stats;

    const list = document.createElement("div");
    list.className = "issue-list";

    if (!errors.length && !warnings.length) {
      const ok = document.createElement("div");
      ok.className = "issue-ok";
      ok.textContent =
        "No issues detected — " + stats.rows + " row(s), " + stats.cols + " column(s).";
      list.appendChild(ok);
      container.appendChild(list);
      return;
    }

    const summary = document.createElement("div");
    summary.className = "issue-summary";
    summary.textContent =
      stats.rows + " row(s), " + stats.cols + " column(s) · " +
      errors.length + " error(s) · " + warnings.length + " warning(s)";
    list.appendChild(summary);

    const addItems = function (items, cls, label) {
      if (!items.length) return;
      const head = document.createElement("div");
      head.className = "issue-group-title " + cls;
      head.textContent = label + " (" + items.length + ")";
      list.appendChild(head);

      items.forEach(function (item) {
        const div = document.createElement("div");
        div.className = "issue-item " + cls;
        const loc = document.createElement("span");
        loc.className = "issue-line";
        loc.textContent = item.line ? "Line " + item.line : "";
        const msg = document.createElement("span");
        msg.className = "issue-msg";
        msg.textContent = item.message;
        div.appendChild(loc);
        div.appendChild(msg);
        list.appendChild(div);
      });
    };

    addItems(errors, "error", "Errors");
    addItems(warnings, "warning", "Warnings");

    container.appendChild(list);
  }

  function renderPreview(container, parsed, issues) {
    if (!container) return;
    container.innerHTML = "";

    const headers = parsed.headers;
    const rows = parsed.rows;
    const lines = parsed.lines;
    if (!headers.length) return;

    const lineIssues = {};
    issues.errors.forEach(function (e) {
      if (e.line) lineIssues[e.line] = "error";
    });
    issues.warnings.forEach(function (w) {
      if (w.line && !lineIssues[w.line]) lineIssues[w.line] = "warning";
    });

    const maxRows = 50;
    const shown = Math.min(rows.length, maxRows);

    const table = document.createElement("table");
    table.className = "csv-preview table table-sm mb-0";

    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    const thIdx = document.createElement("th");
    thIdx.className = "idx";
    thIdx.textContent = "#";
    trh.appendChild(thIdx);
    headers.forEach(function (h) {
      const th = document.createElement("th");
      th.textContent = h;
      trh.appendChild(th);
    });
    thead.appendChild(trh);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (let r = 0; r < shown; r++) {
      const tr = document.createElement("tr");
      const line = lines[r];
      if (lineIssues[line]) tr.className = "row-" + lineIssues[line];

      const tdIdx = document.createElement("td");
      tdIdx.className = "idx";
      tdIdx.textContent = line;
      tr.appendChild(tdIdx);

      headers.forEach(function (h, c) {
        const td = document.createElement("td");
        td.textContent = rows[r][c] !== undefined ? rows[r][c] : "";
        tr.appendChild(td);
      });
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    container.appendChild(table);

    if (rows.length > shown) {
      const caption = document.createElement("div");
      caption.className = "preview-caption";
      caption.textContent =
        "Showing " + shown + " of " + rows.length + " rows";
      container.appendChild(caption);
    }
  }

  // ---------- Paste -> File ----------
  function textToFile(text, name) {
    return new File([text], name, { type: "text/csv" });
  }

  function attachFileToInput(input, file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
  }

  // ---------- CSV upload / paste orchestration ----------
  function initCsvUpload() {
    const source = document.querySelector(".csv-source");
    if (!source) return;

    const fileInput = el("csv");
    const pasteTextarea = el("csv-paste");
    const previewEl = el("csv-preview");
    const issuesEl = el("csv-issues");
    const feedback = source.querySelector(".csv-feedback");
    const emailKeySelect = el("email_key");
    const startEl = el("start");
    const stopEl = el("stop");
    const sliderEl = el("slider-range");
    const countEl = el("recipient-count");
    const form = source.closest("form");
    const sendBtn = form ? form.querySelector("[data-submit-btn]") : null;
    const blockNote = source.querySelector(".csv-block-note");

    const recipientKind = emailKeySelect ? "email" : "phone";

    let currentMode = "upload";
    let currentParsed = { headers: [], rows: [], lines: [] };
    let currentIssues = { errors: [], warnings: [], stats: { rows: 0, cols: 0 } };

    const modeBtns = source.querySelectorAll(".mode-btn");
    const panels = {
      upload: source.querySelector('[data-mode-panel="upload"]'),
      paste: source.querySelector('[data-mode-panel="paste"]'),
    };

    const updateSendState = function () {
      const blocked =
        currentParsed.headers.length > 0 && currentIssues.errors.length > 0;
      if (sendBtn) sendBtn.disabled = blocked;
      if (blockNote) {
        blockNote.hidden = !blocked;
        if (blocked) {
          const n = currentIssues.errors.length;
          blockNote.textContent =
            "Fix " + n + " error" + (n === 1 ? "" : "s") + " above to continue.";
        }
      }
    };

    const setMode = function (mode) {
      currentMode = mode;
      modeBtns.forEach(function (b) {
        b.classList.toggle("is-active", b.getAttribute("data-mode") === mode);
      });
      if (panels.upload) panels.upload.hidden = mode !== "upload";
      if (panels.paste) panels.paste.hidden = mode !== "paste";
      if (fileInput) fileInput.required = mode === "upload";
    };

    const getRecipientColumn = function () {
      return emailKeySelect ? emailKeySelect.value : "phone";
    };

    const applyRecipientColumn = function () {
      if (!currentParsed.headers.length) return;
      currentIssues = validateRecipients(
        currentParsed,
        getRecipientColumn(),
        recipientKind
      );
      renderIssues(issuesEl, currentIssues);
      renderPreview(previewEl, currentParsed, currentIssues);
      if (feedback) feedback.hidden = false;
      updateSendState();
    };

    const populateColumns = function (headers) {
      if (!emailKeySelect) return;
      emailKeySelect.innerHTML = "";
      headers.forEach(function (h) {
        const o = document.createElement("option");
        o.value = h;
        o.textContent = h;
        emailKeySelect.appendChild(o);
      });
      const idx = headers.findIndex(function (h) {
        return /email/i.test(h);
      });
      emailKeySelect.selectedIndex = idx >= 0 ? idx : 0;

      const hint = el("email_key_hint");
      if (hint) {
        hint.textContent = headers.length
          ? headers.length + " column(s) detected"
          : "No columns detected";
      }
    };

    const setupSlider = function (count) {
      if (!sliderEl || !startEl || !stopEl) return;

      if (count < 1) {
        sliderEl.innerHTML = "";
        if (countEl) countEl.textContent = "0";
        return;
      }

      const updateCount = function () {
        const s = parseInt(startEl.value, 10) || 1;
        const t = parseInt(stopEl.value, 10) || count;
        if (countEl) countEl.textContent = Math.max(0, t - s + 1);
      };

      if (window.jQuery && window.jQuery.fn.slider) {
        window.jQuery(sliderEl).slider({
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
      }

      startEl.value = 1;
      stopEl.value = count;
      updateCount();
    };

    const processParsed = function (parsed) {
      currentParsed = parsed;

      if (!parsed.headers.length) {
        if (emailKeySelect) emailKeySelect.innerHTML = "";
        setupSlider(0);
        currentIssues = {
          errors: [{ line: 0, message: "No data found. Paste CSV or upload a file." }],
          warnings: [],
          stats: { rows: 0, cols: 0 },
        };
        renderIssues(issuesEl, currentIssues);
        if (previewEl) previewEl.innerHTML = "";
        if (feedback) feedback.hidden = false;
        updateSendState();
        return;
      }

      populateColumns(parsed.headers);
      setupSlider(parsed.rows.length);
      applyRecipientColumn();
    };

    const processText = function (text) {
      processParsed(parseCsvText(text));
    };

    const readFile = function (file) {
      if (!file) return;
      const name = file.name.toLowerCase();

      if (name.endsWith(".gz")) {
        currentParsed = { headers: [], rows: [], lines: [] };
        currentIssues = {
          errors: [],
          warnings: [
            {
              line: 0,
              message: "Preview and checks are unavailable for .gz files — sending still works.",
            },
          ],
          stats: { rows: 0, cols: 0 },
        };
        renderIssues(issuesEl, currentIssues);
        if (previewEl) previewEl.innerHTML = "";
        if (feedback) feedback.hidden = false;
        if (emailKeySelect) emailKeySelect.innerHTML = "";
        setupSlider(0);
        updateSendState();
        return;
      }

      if (name.endsWith(".csv") || name.endsWith(".txt")) {
        const reader = new FileReader();
        reader.onload = function () {
          processText(String(reader.result || ""));
        };
        reader.readAsText(file);
        return;
      }

      const reader = new FileReader();
      reader.onload = function () {
        let parsed = { headers: [], rows: [], lines: [] };
        try {
          const wb = XLSX.read(reader.result, { type: "array" });
          const sheet = wb.Sheets[wb.SheetNames[0]];
          const rows = XLSX.utils.sheet_to_json(sheet, {
            header: 1,
            defval: "",
            raw: false,
          });
          parsed = rowsToParsed(rows);
        } catch (err) {
          console.error("Failed to parse file", err);
        }
        processParsed(parsed);
      };
      reader.readAsArrayBuffer(file);
    };

    modeBtns.forEach(function (b) {
      b.addEventListener("click", function () {
        setMode(b.getAttribute("data-mode"));
        if (currentMode === "upload") {
          if (fileInput && fileInput.files.length) readFile(fileInput.files[0]);
        } else if (pasteTextarea) {
          processText(pasteTextarea.value);
        }
      });
    });

    if (fileInput) {
      fileInput.addEventListener("change", function () {
        if (currentMode === "upload" && fileInput.files.length) {
          readFile(fileInput.files[0]);
        }
      });
    }

    if (pasteTextarea) {
      let timer;
      pasteTextarea.addEventListener("input", function () {
        clearTimeout(timer);
        timer = setTimeout(function () {
          if (currentMode === "paste") processText(pasteTextarea.value);
        }, 250);
      });
    }

    if (emailKeySelect) {
      emailKeySelect.addEventListener("change", function () {
        applyRecipientColumn();
      });
    }

    if (form) {
      form.addEventListener("submit", function (e) {
        if (currentMode === "paste") {
          const text = pasteTextarea ? pasteTextarea.value : "";
          const parsed = parseCsvText(text);
          if (!parsed.headers.length) {
            e.preventDefault();
            e.stopImmediatePropagation();
            if (feedback) feedback.hidden = false;
            if (issuesEl) issuesEl.scrollIntoView({ behavior: "smooth", block: "center" });
            return;
          }
          attachFileToInput(fileInput, textToFile(text, "pasted.csv"));
        } else if (!fileInput.files || !fileInput.files.length) {
          e.preventDefault();
          e.stopImmediatePropagation();
          currentIssues = {
            errors: [{ line: 0, message: "Please upload a recipient list." }],
            warnings: [],
            stats: { rows: 0, cols: 0 },
          };
          renderIssues(issuesEl, currentIssues);
          if (feedback) feedback.hidden = false;
          if (issuesEl) issuesEl.scrollIntoView({ behavior: "smooth", block: "center" });
          return;
        }

        if (currentParsed.headers.length && currentIssues.errors.length) {
          e.preventDefault();
          e.stopImmediatePropagation();
          if (feedback) feedback.hidden = false;
          if (issuesEl) issuesEl.scrollIntoView({ behavior: "smooth", block: "center" });
        }
      });
    }

    setMode("upload");
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
    initCsvUpload();
    initSendingSpinner();
    initDropzones();
    initHelpScrollspy();
  });
})();
