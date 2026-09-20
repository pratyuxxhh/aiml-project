const state = {
  id: null,
  templates: [],
  recommended: [],
  template: "generic_table",
  dataset: null,
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
    li.innerHTML = `<label class="check"><input type="checkbox" checked data-col="${col.normalized_name}" /> ${col.original_name}</label>`;
    picks.appendChild(li);
  }
}

function currentEdits() {
  const selected = [...document.querySelectorAll("#column-picks input:checked")].map(
    (el) => el.dataset.col
  );
  return {
    title: $("title").value || null,
    subtitle: $("subtitle").value || null,
    selected_columns: selected,
    show_summary: $("show-summary").checked,
    font_size: Number($("font-size").value),
    template: state.template,
  };
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

loadTemplates().catch((err) => showError($("upload-status"), err.message));

