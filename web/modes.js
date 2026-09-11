"use strict";
const purposeNames = {
  novel: "Historia / libro",
  translation: "Traducción literaria",
  rpg: "Mundo para rol · extra",
};
function hasPurposeInterview() {
  return currentRuns().some(
    (r) =>
      r.mode === "interview" &&
      (r.purpose || "novel") === (state.purpose || "novel"),
  );
}
function updateWizardPurpose() {
  const purpose = $("wizard-purpose").value,
    extra = purpose !== "novel";
  document.querySelector("[name=start-workflow][value=writing]").disabled =
    extra;
  if (extra)
    document.querySelector("[name=start-workflow][value=guided]").checked =
      true;
  const translation = purpose === "translation";
  $("wizard-story").hidden = translation;
  $("wizard-translation").hidden = $("wizard-translation").disabled =
    !translation;
  $("wizard-material-optional").textContent = translation
    ? "(requerida)"
    : "(opcional)";
  $("wizard-purpose-hint").textContent = translation
    ? "Partimos de una obra existente y de los idiomas que elijas. La entrevista continúa con intención, voz y matices."
    : purpose === "rpg"
      ? "Una ayuda extra para preparar mundo, PNJ, facciones y reglas propias. El director conserva el criterio; no se juega una partida aquí."
      : "";
  $("wizard-guided-note").hidden =
    document.querySelector("[name=start-workflow]:checked").value !== "guided";
  $("wizard-create").textContent = $("wizard-guided-note").hidden
    ? "Crear proyecto"
    : "Crear e iniciar entrevista";
}
$("wizard-purpose").onchange = action(async () => {
  updateWizardPurpose();
  if (
    $("wizard-purpose").value === "translation" &&
    wizardSelected().length &&
    !$("wizard-from").value
  )
    await detectWizardLanguage();
});
function applyPurpose() {
  const purpose = state.purpose || "novel",
    rpg = purpose === "rpg",
    translation = purpose === "translation";
  $("purpose").value = purpose;
  $("translation-open").hidden = !translation;
  $("book-open").hidden = rpg;
  $("plan-open").hidden = rpg;
  $("book-progress").hidden = rpg;
  document.querySelector(".skill-check").hidden = rpg;
  $("export").textContent = rpg ? "Exportar dossier ↓" : "Exportar proyecto ↓";
  $("purpose-banner").hidden = purpose === "novel";
  $("purpose-banner").innerHTML = translation
    ? '<strong>Traducción con criterio del autor</strong><p>Primero el encargo; después los matices, el borrador y tu revisión.</p><button class="secondary" data-translation-setup>Preparar encargo</button><button class="context-link" data-help="translation">Cómo funciona</button>'
    : rpg
      ? '<strong>Mundo para rol · modo extra</strong><p>Prepará situaciones abiertas, PNJ, lugares y reglas del mundo para tu mesa.</p><button class="secondary" data-rpg-starter>Preparar un mundo inicial</button><button class="context-link" data-help="rpg">Ayuda de rol</button>'
      : "";
  if (purpose !== "novel") {
    $("assistant-title").textContent = translation
      ? "Conservemos la intención"
      : "Construyamos tu mundo";
    $("assistant-eyebrow").textContent = purposeNames[purpose].toUpperCase();
  }
  document.querySelector("#mode option[value=translate]").hidden = !translation;
  document.querySelector("#mode option[value=draft]").disabled = translation;
  document.querySelector("#mode option[value=draft]").textContent = rpg
    ? "Preparar material de rol"
    : "Redactar borrador";
  if (translation && $("mode").value === "draft") $("mode").value = "translate";
  setTaskMode();
}
$("purpose").onchange = action(async () => {
  if (dirty) {
    $("purpose").value = state.purpose;
    throw new Error("Guardá el documento antes de cambiar el objetivo.");
  }
  const project = state.id;
  state = await api("/api/project/purpose", {
    project,
    purpose: $("purpose").value,
  });
  applyWorkflow();
  savePromptDraft();
  renderDocuments();
  renderAssistant();
  if (state.workflow === "guided" && !hasPurposeInterview())
    await beginInterview();
});
function renderTranslationNext() {
  const last = currentRuns().at(-1),
    config = state.translation_config,
    source = state.documents.find(
      (d) => d.id === config?.source && d.selected && !d.translation,
    );
  $("translation-next").hidden =
    state.purpose !== "translation" ||
    !!busy() ||
    last?.mode !== "interview" ||
    last.status !== "completed" ||
    !source?.content?.trim() ||
    !config.source_language ||
    !config.target_language;
}
$("translation-next-start").onclick = action(prepareTranslation);
function prepareTranslation() {
  $("mode").value = "translate";
  setTaskMode();
  showPanel("conversation");
  if (!$("prompt").value.trim())
    $("prompt").value =
      "Continuemos la traducción de la unidad del encargo. Consultá un matiz relevante si falta mi criterio; conservá la intención y las decisiones aprobadas.";
  savePromptDraft();
  $("prompt").focus();
}
function translationDraft(run, kind, fallback = "") {
  return (
    sessionStorage.getItem(`sw-translation-${state.id}-${run}-${kind}`) ??
    fallback
  );
}
function translationHTML(run) {
  if (run.status !== "completed" || !run.translation_result) return "";
  const result = run.translation_result,
    id = run.id,
    context = run.translation_context;
  const label = `${context.config.source_language} → ${context.config.target_language}`;
  if (result.question)
    return `<section class="translation-card"><strong>${escapeHTML(label)} · Matiz para decidir</strong><blockquote>${escapeHTML(result.quote)}</blockquote><p>${escapeHTML(result.question)}</p>${run.translation_answer ? `<p class="criterion-saved">Tu criterio: ${escapeHTML(run.translation_answer)}</p><button class="secondary" data-translation-continue>Continuar con IA</button>` : `<div class="nuance-options">${result.options.map((option, i) => `<button class="secondary" data-nuance="${id}" data-option="${i}"><strong>${escapeHTML(option.wording)}</strong><span>${escapeHTML(option.effect)}</span></button>`).join("")}</div><label>Tu criterio (podés escribir otra alternativa)<textarea data-criterion="${id}" maxlength="4000" rows="3">${escapeHTML(translationDraft(id, "criterion"))}</textarea></label><button class="primary" data-translation-answer="${id}">Registrar mi criterio</button><p>Registrar guarda tu decisión. Continuar con IA inicia otro turno con ella.</p>`}</section>`;
  const saved = state.documents.find(
    (d) => d.source_run === id && d.translation,
  );
  return `<section class="translation-card"><strong>${escapeHTML(label)} · Borrador por revisar</strong>${saved ? `<p>Guardada como copia separada · ${saved.translation_status === "reviewed" ? "revisada" : "requiere otra revisión"}.</p><button class="secondary" data-open-translation="${saved.id}">Abrir traducción guardada</button>` : `<p>Compará intención, subtexto, registro y voz. Podés corregir el borrador antes de aprobar. Detectar matices con IA no garantiza que no falten otros.</p><div class="translation-pair"><label>Original congelado<textarea readonly rows="10">${escapeHTML(context.original)}</textarea></label><label>Traducción editable<textarea data-translation-text="${id}" rows="10">${escapeHTML(translationDraft(id, "text", result.draft))}</textarea></label></div><button class="primary" data-translation-accept="${id}">Revisé y apruebo esta traducción</button>`}</section>`;
}
function rememberTranslationFocus() {
  const el = document.activeElement,
    key = el?.dataset.translationText
      ? "translation-text"
      : el?.dataset.criterion
        ? "criterion"
        : null;
  if (!key) return () => {};
  const id = el.getAttribute("data-" + key),
    start = el.selectionStart,
    end = el.selectionEnd;
  return () => {
    const target = document.querySelector(`[data-${key}="${id}"]`);
    if (target) {
      target.focus({ preventScroll: true });
      target.setSelectionRange(start, end);
    }
  };
}
$("runs").addEventListener("input", (event) => {
  const el = event.target,
    id = el.dataset.criterion || el.dataset.translationText;
  if (!id) return;
  try {
    sessionStorage.setItem(
      `sw-translation-${state.id}-${id}-${el.dataset.criterion ? "criterion" : "text"}`,
      el.value,
    );
  } catch {
    notice(
      "No se pudo conservar esta revisión en la ventana. Copiala antes de salir.",
      true,
    );
  }
});
$("runs").addEventListener(
  "click",
  action(async (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    const project = state.id;
    if (button.dataset.nuance) {
      const run = state.runs.find((r) => r.id === button.dataset.nuance),
        option = run.translation_result.options[Number(button.dataset.option)];
      const input = document.querySelector(`[data-criterion="${run.id}"]`);
      input.value = option.wording + " — " + option.effect;
      input.dispatchEvent(new Event("input", { bubbles: true }));
      input.focus();
    }
    if (button.dataset.translationAnswer) {
      const run = button.dataset.translationAnswer,
        answer = document.querySelector(`[data-criterion="${run}"]`).value;
      const incoming = await api("/api/translation/answer", {
        project,
        run,
        answer,
      });
      if (state.id !== project) return;
      state = incoming;
      lastRuns = "";
      renderAssistant();
      notice("Criterio registrado. Continuá cuando quieras.");
    }
    if (button.hasAttribute("data-translation-continue")) {
      prepareTranslation();
      $("send").click();
    }
    if (button.dataset.translationAccept) {
      if (dirty)
        throw new Error(
          "Guardá el documento abierto antes de aprobar otra copia.",
        );
      const run = button.dataset.translationAccept,
        text = document.querySelector(`[data-translation-text="${run}"]`).value;
      await api("/api/translation/accept", { project, run, text });
      if (state.id !== project) return;
      const incoming = await api(`/api/projects/${project}`);
      if (state.id !== project) return;
      state = incoming;
      renderDocuments();
      lastRuns = "";
      renderAssistant();
      notice(
        "Traducción aprobada como copia independiente. El original se conserva.",
      );
    }
    if (button.dataset.openTranslation) {
      showMaterial();
      openDocument(button.dataset.openTranslation);
    }
  }),
);
function renderTranslationDocuments() {
  const docs = state.documents.filter((d) => d.translation),
    locale = state.translation_config?.target_language;
  $("translation-status").textContent =
    `${docs.filter((d) => d.translation_status === "reviewed" && d.translation.target_language === locale).length} copias revisadas para ${locale || "el idioma por definir"}. Cada unidad requiere tu aprobación.`;
  $("translation-documents").innerHTML = docs
    .map((doc) => {
      const original = state.documents.find(
        (d) => d.id === doc.translation.source,
      );
      return `<details class="translation-card"><summary>${escapeHTML(doc.name)} · ${doc.translation_status === "reviewed" ? "Revisada" : "Por revisar: cambió texto o encargo"}</summary><div class="translation-pair"><label>Original actual<textarea readonly rows="9">${escapeHTML(original?.content || "Fuente no disponible")}</textarea></label><label>Traducción guardada<textarea readonly rows="9">${escapeHTML(doc.content)}</textarea></label></div><button class="secondary" data-translation-edit="${doc.id}">Editar traducción</button><button class="primary" data-translation-review="${doc.id}" data-hash="${doc.hash}" data-source-hash="${original?.hash || ""}">Comparé ambas versiones y apruebo</button></details>`;
    })
    .join("");
}
function openTranslation() {
  const config = state.translation_config || {};
  $("translation-form").dataset.dirty = "false";
  $("translation-source").innerHTML = state.documents
    .filter((d) => !d.translation && d.role !== "traducción")
    .map((d) => `<option value="${d.id}">${escapeHTML(d.name)}</option>`)
    .join("");
  if (config.source) $("translation-source").value = config.source;
  for (const [id, key] of [
    ["from", "source_language"],
    ["to", "target_language"],
    ["intent", "intent"],
    ["glossary", "glossary"],
  ])
    $("translation-" + id).value = config[key] || "";
  renderTranslationDocuments();
  showDialog($("translation-dialog"));
}
$("translation-open").onclick = openTranslation;
$("translation-form").oninput = () =>
  ($("translation-form").dataset.dirty = "true");
function checkTranslationEdits() {
  if ($("translation-form").dataset.dirty === "true")
    throw new Error("Guardá primero los cambios del encargo.");
}
function closeTranslation(event) {
  if (
    $("translation-form").dataset.dirty === "true" &&
    !confirm("¿Cerrar sin guardar los cambios del encargo?")
  ) {
    event?.preventDefault();
    return;
  }
  $("translation-dialog").close();
}
$("translation-close").onclick = closeTranslation;
$("translation-dialog").oncancel = closeTranslation;
$("translation-form").onsubmit = action(async (event) => {
  event.preventDefault();
  if (dirty) throw new Error("Guardá primero los cambios del original.");
  const project = state.id,
    config = {
      source: $("translation-source").value,
      source_language: $("translation-from").value.trim(),
      target_language: $("translation-to").value.trim(),
      intent: $("translation-intent").value,
      glossary: $("translation-glossary").value,
    };
  state = await api("/api/translation/config", { project, config });
  $("translation-form").dataset.dirty = "false";
  renderTranslationDocuments();
  renderAssistant();
  notice(
    "Encargo guardado. Marcá el original en las fuentes antes de traducir.",
  );
});
$("translation-start").onclick = action(() => {
  checkTranslationEdits();
  if (!state.translation_config) throw new Error("Guardá el encargo primero.");
  $("translation-dialog").close();
  prepareTranslation();
  $("send").click();
});
for (const format of ["md", "docx", "pdf"])
  $("translation-" + format).onclick = action(async () => {
    checkTranslationEdits();
    if (dirty) throw new Error("Guardá y revisá el texto antes de exportar.");
    await download(
      await api(`/api/projects/${state.id}/translation.${format}`),
      "traduccion." + format,
    );
  });
$("translation-documents").onclick = action(async (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  checkTranslationEdits();
  if (button.dataset.translationEdit) {
    $("translation-dialog").close();
    showMaterial();
    openDocument(button.dataset.translationEdit);
  }
  if (button.dataset.translationReview) {
    if (dirty) throw new Error("Guardá primero el texto del editor.");
    state = await api("/api/translation/review", {
      project: state.id,
      document: button.dataset.translationReview,
      hash: button.dataset.hash,
      source_hash: button.dataset.sourceHash,
    });
    renderTranslationDocuments();
    renderDocuments();
    renderAssistant();
    notice("Revisión humana registrada para ambas versiones.");
  }
});
document.addEventListener("click", (event) => {
  if (event.target.closest("[data-translation-setup]")) openTranslation();
  if (event.target.closest("[data-rpg-starter]")) {
    showPanel("conversation");
    $("mode").value = "draft";
    setTaskMode();
    $("prompt").value =
      "Ayudame a preparar rápido un mundo inicial para mi mesa: premisa, lugar de partida, tres PNJ, dos facciones, reglas del mundo y tres ganchos abiertos. Si falta una decisión esencial sobre sistema, tono o límites, preguntame de a una. Todo lo que no aprobé es provisional; no decidas lo que harán los jugadores.";
    savePromptDraft();
    $("prompt").focus();
  }
});
Object.assign(templates, {
  rpg_world: {
    role: "plan",
    text: "## Experiencia de mesa, tono y límites\n\nPor acordar con el director y el grupo.\n\n## Sistema y edición o reglas propias\n\nPor definir; no asumir reglas oficiales.\n\n## Premisa, escala y lugar inicial\n\nPor definir.\n\n## Qué saben los personajes jugadores\n\nPor definir.\n\n## Secretos del director y conflictos abiertos\n\nProvisional.",
  },
  rpg_npc: {
    role: "plan",
    text: "## Deseo, miedo y recurso\n\nPor definir.\n\n## Voz y comportamiento reconocible\n\nPor definir.\n\n## Qué ofrece o necesita del grupo\n\nPor definir.\n\n## Información pública / secreto del director\n\nSeparar.\n\n## Reacciones posibles, sin decidir por jugadores\n\nProvisional.",
  },
  rpg_faction: {
    role: "plan",
    text: "## Objetivo, recursos y método\n\nPor definir.\n\n## Líderes, aliados y rivales\n\nPor definir.\n\n## Qué pasaría si nadie interviene\n\nProvisional.\n\n## Oferta al grupo y costo de aceptarla\n\nProvisional.",
  },
  rpg_place: {
    role: "plan",
    text: "## Función en la mesa y tres detalles sensoriales\n\nPor definir.\n\n## Habitantes, recursos y accesos\n\nPor definir.\n\n## Conflicto visible y secreto\n\nSeparar.\n\n## Conexiones a otros lugares\n\nProvisional.",
  },
  rpg_rules: {
    role: "plan",
    text: "## Regla del mundo y por qué importa\n\nProvisional.\n\n## Límites, costo y excepciones\n\nPor definir.\n\n## Consecuencias en la vida cotidiana\n\nPor definir.\n\n## Mecánica casera propuesta\n\nOpcional; revisar con el grupo. No es una regla oficial.\n\n## Sistema / edición / fuente autorizada\n\nSi corresponde.",
  },
  rpg_hooks: {
    role: "plan",
    text: "## Situación inicial abierta\n\nPor definir.\n\n## Actores, objetivos y presión\n\nPor definir.\n\n## Tres formas posibles de implicarse\n\nOpciones, no acciones obligatorias.\n\n## Consecuencias posibles de actuar o ignorarlo\n\nProvisional.\n\n## Información pública / secretos del director\n\nSeparar.",
  },
});

// El material del wizard vive solo en esta ventana hasta crear el proyecto.
let wizardDocuments = [],
  wizardFolder = null,
  wizardMaterialEpoch = 0,
  wizardLoading = false;
function clearWizardMaterial(keepFile = false) {
  wizardMaterialEpoch++;
  wizardLoading = false;
  wizardDocuments = [];
  wizardFolder = null;
  if (!keepFile) $("wizard-file").value = "";
  $("wizard-file-list").replaceChildren();
  $("wizard-files-status").textContent = "";
  $("wizard-original").replaceChildren();
  $("wizard-material-clear").hidden = true;
  $("wizard-from").value = "";
  $("wizard-detection").textContent =
    "Podés elegir de la lista o escribir cualquier idioma y variante.";
}
function wizardSelected() {
  return wizardFolder
    ? wizardFolder.files.filter((f) => f.selected)
    : wizardDocuments;
}
function renderWizardMaterial() {
  const files = wizardSelected(),
    previous = $("wizard-original").selectedOptions[0]?.textContent;
  $("wizard-original").replaceChildren(
    ...files.map((f, i) => new Option(f.name, String(i))),
  );
  const index = files.findIndex((f) => f.name === previous);
  if (index >= 0) $("wizard-original").value = String(index);
  else $("wizard-from").value = "";
  $("wizard-files-status").textContent =
    `${files.length} archivos elegidos. ${wizardFolder ? `${wizardFolder.skipped} archivos no compatibles u ocultos omitidos.` : ""} Las copias no se seleccionan para IA, salvo la primera unidad del original de traducción.`;
  $("wizard-material-clear").hidden = !wizardFolder && !wizardDocuments.length;
}
async function detectWizardLanguage() {
  const source = wizardSelected()[Number($("wizard-original").value)];
  if (!source) throw new Error("Elegí el original primero.");
  const epoch = ++wizardMaterialEpoch,
    previous = $("wizard-from").value;
  $("wizard-detection").textContent =
    "Buscando indicios del idioma en el original…";
  const result = await api(
    "/api/translation/detect",
    wizardFolder
      ? { path: wizardFolder.path, file: source.name }
      : { text: source.content },
  );
  if (epoch !== wizardMaterialEpoch || !$("project-wizard").open) return;
  if ($("wizard-from").value !== previous) return;
  if (result.language) {
    $("wizard-from").value = result.language;
    $("wizard-detection").textContent =
      `Idioma sugerido: ${result.language}. Confirmalo o corregilo; la variante la decide el autor.`;
  } else
    $("wizard-detection").textContent =
      "No hay indicios suficientes o el texto mezcla idiomas. Elegí el idioma original y su variante.";
}
$("wizard-file").onchange = action(async (event) => {
  const file = event.target.files[0];
  clearWizardMaterial(true);
  if (!file) return;
  const epoch = wizardMaterialEpoch;
  wizardLoading = true;
  try {
    const imported = await importBookFile(file);
    if (epoch !== wizardMaterialEpoch) return;
    wizardDocuments = imported.documents;
    renderWizardMaterial();
    if (imported.warnings.length) notice(imported.warnings.join(" "));
  } finally {
    if (epoch === wizardMaterialEpoch) wizardLoading = false;
  }
  if ($("wizard-purpose").value === "translation") await detectWizardLanguage();
});
$("wizard-material-clear").onclick = () => clearWizardMaterial();
$("wizard-detect").onclick = action(detectWizardLanguage);
$("wizard-original").onchange = action(async () => {
  wizardMaterialEpoch++;
  $("wizard-from").value = "";
  if ($("wizard-purpose").value === "translation") await detectWizardLanguage();
});
$("wizard-folder-scan").onclick = action(async () => {
  clearWizardMaterial();
  const epoch = wizardMaterialEpoch;
  wizardLoading = true;
  try {
    const folder = await api("/api/import/preview", {
      path: $("wizard-folder-path").value.trim(),
    });
    if (epoch !== wizardMaterialEpoch || !$("project-wizard").open) return;
    folder.files.sort(
      (a, b) =>
        (a.role === "manuscrito" ? 0 : 1) - (b.role === "manuscrito" ? 0 : 1) ||
        a.name.localeCompare(b.name),
    );
    wizardFolder = folder;
    for (const file of folder.files) {
      file.selected = file.size > 0 && file.size <= 1000000;
      const label = document.createElement("label");
      label.className = "check-row";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = file.selected;
      checkbox.disabled = !file.selected;
      const text = document.createElement("span");
      text.textContent = `${file.name} · ${Math.ceil(file.size / 1000)} KB${checkbox.disabled ? " · vacío o supera 1 MB" : ""}`;
      checkbox.onchange = () => {
        file.selected = checkbox.checked;
        wizardMaterialEpoch++;
        renderWizardMaterial();
        $("wizard-detection").textContent =
          "Cambió la selección. Podés volver a detectar el idioma del original.";
      };
      label.append(checkbox, text);
      $("wizard-file-list").append(label);
    }
    renderWizardMaterial();
  } finally {
    if (epoch === wizardMaterialEpoch) wizardLoading = false;
  }
});
$("wizard-folder-pick").hidden = !window.storyDesktop;
$("wizard-folder-pick").onclick = action(async () => {
  const result = await api("/api/desktop/folder", {});
  if (result.path) {
    $("wizard-folder-path").value = result.path;
    await $("wizard-folder-scan").onclick();
  }
});
function wizardPayload() {
  if (wizardLoading)
    throw new Error("Esperá a que termine de cargar el material.");
  const purpose = $("wizard-purpose").value,
    files = wizardSelected();
  if (files.length > 100) throw new Error("Elegí hasta 100 archivos.");
  if (wizardFolder && !files.length)
    throw new Error("Elegí al menos un archivo de la carpeta.");
  const setup = {
    title: $("project-name").value.trim(),
    purpose,
    workflow: document.querySelector("[name=start-workflow]:checked").value,
    initial_idea:
      purpose === "translation" ? "" : $("project-idea").value.trim(),
  };
  if (wizardFolder)
    setup.import_folder = {
      path: wizardFolder.path,
      files: files.map((f) => f.name),
    };
  else setup.documents = wizardDocuments;
  if (purpose === "translation") {
    if (!files.length)
      throw new Error("Importá una obra existente para traducir.");
    setup.translation = {
      source: Number($("wizard-original").value),
      source_language: $("wizard-from").value.trim(),
      target_language: $("wizard-to").value.trim(),
    };
  }
  return setup;
}
