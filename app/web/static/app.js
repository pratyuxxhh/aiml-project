const state = {
  id: null,
  templates: [],
  recommended: [],
  template: "generic_table",
  dataset: null,
  previewOrientation: "portrait",
  columnAdjustEnabled: false,
};

const $ = (id) => document.getElementById(id);

async function loadTemplates() {
  const res = await fetch("/templates");
  const data = await res.json();
  state.templates = data.templates || [];
  renderTemplates();
}

function renderTemplates() {
  const root = $("templates");
  root.innerHTML = "";
  for (const tpl of state.templates) {
    const el = document.createElement("button");
    el.type = "button";
    el.className = "tpl" + (tpl.id === state.template ? " selected" : "");
    el.innerHTML = `<strong>${tpl.name}</strong><div>${tpl.description}</div>` +
      (state.recommended[0] === tpl.id ? `<div class="rec">Recommended</div>` : "");
    el.addEventListener("click", () => {
      state.template = tpl.id;
      renderTemplates();
      refreshPreview();
    });
    root.appendChild(el);
  }
}

function showError(el, message) {
  el.classList.add("error");
  el.textContent = message;
}

function showStatus(el, message) {
  el.classList.remove("error");
  el.textContent = message;
}

async function parseResponse(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error || `Request failed (${res.status})`);
  }
  return data;
}

function applyUpload(data) {
  state.id = data.id;
  state.dataset = data.dataset;
  state.recommended = data.analysis.recommended_templates || ["generic_table"];
  state.template = state.recommended[0] || "generic_table";
  $("title").value = "";
  $("subtitle").value = "";
  $("header-row").value = data.header_row;
  const sheet = $("sheet");
  sheet.innerHTML = "";
  for (const name of data.sheets) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = name;
    if (name === data.selected_sheet) opt.selected = true;
    sheet.appendChild(opt);
  }
  $("sheet-row").classList.toggle("hidden", data.sheets.length <= 1 && data.sheets[0] === "csv");
  if (data.sheets.length > 1) $("sheet-row").classList.remove("hidden");

  renderColumns(data);
  renderTemplates();
  const src = "deterministic rules";
  showStatus(
    $("upload-status"),
    `${data.filename}: ${data.dataset.row_count} rows, ${data.dataset.columns.length} columns. Classification: ${src}.`
  );
  refreshPreview();
}

function renderColumns(data) {
  const cols = data.dataset.columns;
  $("columns").innerHTML =
    "<p><strong>Columns</strong></p><table><thead><tr><th>Original</th><th>Normalized</th><th>Type</th><th>Semantic</th></tr></thead><tbody>" +
    cols.map((c) =>
      `<tr><td>${c.original_name}</td><td>${c.normalized_name}</td><td>${c.primitive_type}</td><td>${c.semantic_type}</td></tr>`
    ).join("") +
    "</tbody></table>";

  const sample = data.dataset.sample_rows || [];
  if (sample.length) {
    const keys = cols.map((c) => c.normalized_name);
    $("sample").innerHTML =
      "<p><strong>Sample rows</strong></p><table><thead><tr>" +
      cols.map((c) => `<th>${c.original_name}</th>`).join("") +
      "</tr></thead><tbody>" +
      sample.map((row) =>
        "<tr>" + keys.map((k) => `<td>${row[k] ?? ""}</td>`).join("") + "</tr>"
      ).join("") +
      "</tbody></table>";
  }

  const picks = $("column-picks");
  picks.innerHTML = "";
  for (const col of cols) {
    const li = document.createElement("li");
    const label = document.createElement("label");
    label.className = "check";
    const input = document.createElement("input");
    input.type = "checkbox";
    input.checked = true;
    input.dataset.col = col.normalized_name;
    label.appendChild(input);
    label.appendChild(document.createTextNode(` ${col.original_name}`));
    li.appendChild(label);
    picks.appendChild(li);
  }
}

function previewDataTable() {
  const root = $("preview");
  if (!root) return null;
  return root.querySelector("table.data-table") || root.querySelector(".doc table") || root.querySelector("table");
}

function readColumnWidths(table) {
  if (!table) return null;
  const headerRow = table.querySelector("thead tr") || table.querySelector("tr");
  if (!headerRow) return null;
  const headers = Array.from(headerRow.cells);
  if (!headers.length) return null;

  const raw = headers.map((cell) => {
    const fromData = Number(cell.dataset.colWidth);
    if (Number.isFinite(fromData) && fromData > 0) return fromData;
    const fromStyle = parseFloat(cell.style.width);
    if (Number.isFinite(fromStyle) && fromStyle > 0) return fromStyle;
    return null;
  });
  if (raw.some((value) => value == null)) return null;

  const total = raw.reduce((sum, value) => sum + value, 0) || 1;
  return raw.map((value) => (value / total) * 100);
}

function currentEdits() {
  const selected = [...document.querySelectorAll("#column-picks input:checked")].map(
    (el) => el.dataset.col
  );
  const table = previewDataTable();
  const headerCount = table
    ? (table.querySelector("thead tr") || table.querySelector("tr"))?.cells.length || 0
    : 0;
  const columnWidths = readColumnWidths(table);
  // Only keep widths when they match the columns currently selected for export.
  const widthsMatchSelection =
    columnWidths &&
    selected.length > 0 &&
    columnWidths.length === selected.length &&
    columnWidths.length === headerCount;
  return {
    title: $("title").value || null,
    subtitle: $("subtitle").value || null,
    selected_columns: selected,
    show_summary: $("show-summary").checked,
    font_size: Number($("font-size").value),
    orientation: state.previewOrientation,
    template: state.template,
    column_widths: widthsMatchSelection ? columnWidths : null,
  };
}

function applyPreviewOrientation(mode) {
  state.previewOrientation = mode === "landscape" ? "landscape" : "portrait";
  const preview = $("preview");
  const toggle = $("orientation-toggle");
  preview.classList.toggle("landscape", state.previewOrientation === "landscape");
  toggle.textContent = state.previewOrientation === "landscape" ? "Portrait view" : "Landscape view";

  const tables = preview.querySelectorAll("table.data-table, table");
  if (!tables.length) return;

  const seen = new Set();
  tables.forEach((table) => {
    if (seen.has(table)) return;
    seen.add(table);
    if (!table.__columnWidths || !table.__columnWidths.length) return;
    const factor = state.previewOrientation === "landscape" ? 1.5 : 1 / 1.5;
    const nextWidths = table.__columnWidths.map((value) => Math.max(30, value * factor));
    const total = nextWidths.reduce((sum, value) => sum + value, 0) || 1;
    const headers = table.querySelectorAll("thead th, tr:first-child th");
    headers.forEach((cell, index) => {
      const percent = (nextWidths[index] / total) * 100;
      cell.style.width = `${percent}%`;
      cell.dataset.colWidth = String(percent);
      cell.dataset.colWidthPx = String(nextWidths[index]);
    });

    Array.from(table.rows).forEach((row) => {
      Array.from(row.cells).forEach((cell, index) => {
        if (index < headers.length) {
          const percent = (nextWidths[index] / total) * 100;
          cell.style.width = `${percent}%`;
          cell.dataset.colWidth = String(percent);
          cell.dataset.colWidthPx = String(nextWidths[index]);
        }
      });
    });

    table.__columnWidths = nextWidths;
  });
}

function applyColumnWidths(table) {
  const rows = Array.from(table.rows);
  const headerCells = rows[0] ? Array.from(rows[0].cells) : [];
  if (!headerCells.length) return;

  const widths = headerCells.map((cell) => {
    const width = parseFloat(cell.dataset.colWidth || cell.style.width || getComputedStyle(cell).width);
    return Number.isFinite(width) ? width : 160;
  });

  const totalWidth = widths.reduce((sum, value) => sum + value, 0) || 1;
  const normalized = widths.map((value) => (value / totalWidth) * 100);

  headerCells.forEach((cell, index) => {
    cell.style.width = `${normalized[index]}%`;
    cell.dataset.colWidth = String(normalized[index]);
  });

  rows.forEach((row) => {
    Array.from(row.cells).forEach((cell, index) => {
      if (index < headerCells.length) {
        cell.style.width = `${normalized[index]}%`;
      }
    });
  });
}

function wireResizableTables() {
  const scope = document.querySelectorAll("#preview table, #sample table, #columns table");
  scope.forEach((table) => {
    if (table.dataset.resizable === "true") return;
    table.dataset.resizable = "true";
    table.style.width = "100%";
    table.style.tableLayout = "fixed";

    const headerRow = table.querySelector("thead tr, tr:first-child");
    if (!headerRow) return;

    const headers = Array.from(headerRow.cells);
    if (!headers.length) return;

    const setWidths = (nextWidths) => {
      const total = nextWidths.reduce((sum, width) => sum + width, 0) || 1;
      table.__columnWidths = nextWidths.slice();
      headers.forEach((cell, index) => {
        const percent = (nextWidths[index] / total) * 100;
        cell.style.width = `${percent}%`;
        cell.dataset.colWidth = String(percent);
        cell.dataset.colWidthPx = String(nextWidths[index]);
      });

      Array.from(table.rows).forEach((row) => {
        Array.from(row.cells).forEach((cell, cellIndex) => {
          if (cellIndex < headers.length) {
            const percent = (nextWidths[cellIndex] / total) * 100;
            cell.style.width = `${percent}%`;
            cell.dataset.colWidth = String(percent);
            cell.dataset.colWidthPx = String(nextWidths[cellIndex]);
          }
        });
      });
    };

    let currentWidths = headers.map((cell) => {
      const width = parseFloat(cell.dataset.colWidthPx || cell.dataset.colWidth || cell.style.width || getComputedStyle(cell).width);
      return Number.isFinite(width) ? width : table.clientWidth / headers.length;
    });

    headers.forEach((cell, index) => {
      cell.style.position = "relative";
      // A divider belongs to the boundary between this column and the next one.
      // There is no boundary after the final column.
      if (index === headers.length - 1) return;
      if (cell.querySelector(".col-resizer")) return;
      const resizer = document.createElement("span");
      resizer.className = "col-resizer";
      resizer.style.display = state.columnAdjustEnabled ? "block" : "none";
      resizer.setAttribute("aria-hidden", "true");
      cell.appendChild(resizer);

      resizer.addEventListener("pointerdown", (event) => {
        if (!state.columnAdjustEnabled) return;
        event.preventDefault();
        event.stopPropagation();

        const startX = event.clientX;
        const startWidths = (table.__columnWidths || currentWidths).slice();
        const total = startWidths.reduce((sum, value) => sum + value, 0) || 1;
        const minWidth = 30;

        const updateWidths = (clientX) => {
          const delta = clientX - startX;
          const leftWidth = Math.max(
            minWidth,
            Math.min(startWidths[index] + delta, startWidths[index] + startWidths[index + 1] - minWidth)
          );
          const next = startWidths.slice();
          next[index] = leftWidth;
          next[index + 1] = startWidths[index] + startWidths[index + 1] - leftWidth;
          currentWidths = next;
          setWidths(next);
        };

        const onPointerMove = (moveEvent) => {
          updateWidths(moveEvent.clientX);
        };

        const onPointerUp = () => {
          window.removeEventListener("pointermove", onPointerMove);
          window.removeEventListener("pointerup", onPointerUp);
          window.removeEventListener("pointercancel", onPointerUp);
          resizer.releasePointerCapture?.(event.pointerId);
          resizer.classList.remove("dragging");
          document.body.style.cursor = "";
          document.body.style.userSelect = "";
        };

        if (startWidths.length <= 1) return;
        resizer.setPointerCapture?.(event.pointerId);
        resizer.classList.add("dragging");
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        window.addEventListener("pointermove", onPointerMove);
        window.addEventListener("pointerup", onPointerUp);
        window.addEventListener("pointercancel", onPointerUp);
      });
    });

    setWidths(currentWidths);
  });
}

function setColumnAdjustEnabled(enabled) {
  state.columnAdjustEnabled = enabled;
  const btn = $("toggle-column-adjust");
  if (btn) btn.textContent = enabled ? "Disable column adjust" : "Enable column adjust";
  document.querySelectorAll(".col-resizer").forEach((el) => {
    el.style.display = enabled ? "block" : "none";
  });
}

async function refreshPreview() {
  if (!state.id) return;
  const res = await fetch("/documents/preview", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      dataset_id: state.id,
      template: state.template,
      edits: currentEdits(),
    }),
  });
  const data = await parseResponse(res);
  $("preview").innerHTML = data.html;
  wireResizableTables();
  applyPreviewOrientation(state.previewOrientation);
  if (!$("title").value && data.spec.title) {
    $("title").placeholder = data.spec.title;
  }
}

$("upload-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = $("file").files[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  showStatus($("upload-status"), "Parsing…");
  try {
    const res = await fetch("/upload", { method: "POST", body: form });
    applyUpload(await parseResponse(res));
  } catch (err) {
    showError($("upload-status"), err.message);
  }
});

$("reprocess").addEventListener("click", async () => {
  if (!state.id) return;
  const form = new FormData();
  form.append("sheet", $("sheet").value);
  form.append("header_row", $("header-row").value);
  try {
    const res = await fetch(`/upload/${state.id}/reprocess`, { method: "POST", body: form });
    applyUpload(await parseResponse(res));
  } catch (err) {
    showError($("upload-status"), err.message);
  }
});

$("orientation-toggle").addEventListener("click", () => {
  const next = state.previewOrientation === "landscape" ? "portrait" : "landscape";
  applyPreviewOrientation(next);
  if (state.id) {
    refreshPreview().catch((err) => {
      $("preview").innerHTML = `<p class="error">${err.message}</p>`;
    });
  }
});

$("toggle-column-adjust").addEventListener("click", () => {
  setColumnAdjustEnabled(!state.columnAdjustEnabled);
  if (state.id) {
    wireResizableTables();
  }
});

$("preview-btn").addEventListener("click", () => {
  refreshPreview().catch((err) => {
    $("preview").innerHTML = `<p class="error">${err.message}</p>`;
  });
});

$("export-btn").addEventListener("click", async () => {
  if (!state.id) return;
  try {
    const res = await fetch("/documents/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dataset_id: state.id,
        template: state.template,
        edits: currentEdits(),
      }),
    });
    const data = await parseResponse(res);
    window.location = `/files/${data.id}`;
  } catch (err) {
    showError($("upload-status"), err.message);
  }
});

applyPreviewOrientation("portrait");
setColumnAdjustEnabled(false);
wireResizableTables();
loadTemplates().catch((err) => showError($("upload-status"), err.message));
