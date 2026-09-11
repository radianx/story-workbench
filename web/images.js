// ES module: owns image state; the host supplies project/API/editor operations.
export function initImages({
  getProject,
  api,
  action,
  showDialog,
  download,
  binary,
  applyCover,
  openSettings,
}) {
  const $ = (id) => document.getElementById(id);
  const thumbnails = new Map();
  let galleryRecords = [],
    thumbnailProject = null,
    viewing = null,
    viewerURL = null,
    fitWidth = 0,
    viewerRequest = 0;
  const viewer = $("image-viewer"),
    original = $("image-viewer-original");
  function imageRecord(id, projectId) {
    return (
      getProject()?.id === projectId &&
      (getProject().images?.find((image) => image.id === id) ||
        galleryRecords.find((image) => image.id === id))
    );
  }
  async function hydrateImages() {
    const projectId = getProject()?.id;
    if (thumbnailProject !== projectId) {
      for (const promise of thumbnails.values())
        promise.then((url) => url && URL.revokeObjectURL(url));
      thumbnails.clear();
      galleryRecords = [];
      thumbnailProject = projectId;
      if (viewer.open) viewer.close();
    }
    for (const button of document.querySelectorAll("[data-image]")) {
      const id = button.dataset.image;
      if (
        !imageRecord(id, button.dataset.imageProject) ||
        button.dataset.loading
      )
        continue;
      button.dataset.loading = "true";
      if (!thumbnails.has(id))
        thumbnails.set(
          id,
          binary(`/api/projects/${projectId}/images/${id}?thumbnail=1`)
            .then((blob) => URL.createObjectURL(blob))
            .catch(() => null),
        );
      const url = await thumbnails.get(id);
      if (!button.isConnected || getProject()?.id !== projectId) continue;
      if (url) button.querySelector("img").src = url;
      else
        button.querySelector("img").alt =
          "Vista previa no disponible. Abrir original.";
    }
  }
  function zoom() {
    const value = Number($("image-zoom").value);
    $("image-zoom-value").value = value + "%";
    const viewport = original.parentElement;
    // Keep the fit stable while zooming: scrollbars can change viewport size.
    if (!fitWidth)
      fitWidth = Math.min(
        original.naturalWidth,
        viewport.clientWidth - 24,
        ((viewport.clientHeight - 24) * original.naturalWidth) /
          original.naturalHeight,
      );
    original.style.width = Math.max(1, (fitWidth * value) / 100) + "px";
  }
  $("image-zoom").oninput = zoom;
  $("image-fit").onclick = () => {
    fitWidth = 0;
    $("image-zoom").value = "100";
    zoom();
  };
  $("image-viewer-close").onclick = () => viewer.close();
  viewer.addEventListener("close", () => {
    viewerRequest++;
    viewing = null;
    original.removeAttribute("src");
    original.hidden = true;
    if (viewerURL) URL.revokeObjectURL(viewerURL);
    viewerURL = null;
  });
  viewer.addEventListener("keydown", (event) => {
    if (
      !["+", "=", "-"].includes(event.key) ||
      event.target.tagName === "INPUT"
    )
      return;
    event.preventDefault();
    $("image-zoom").value =
      Number($("image-zoom").value) + (event.key === "-" ? -25 : 25);
    zoom();
  });
  window.addEventListener("resize", () => {
    fitWidth = 0;
    if (viewing) zoom();
  });
  document.addEventListener(
    "click",
    action(async (event) => {
      const button = event.target.closest("[data-image]");
      if (!button) return;
      const projectId = button.dataset.imageProject;
      const record = imageRecord(button.dataset.image, projectId);
      if (!record) return;
      const request = ++viewerRequest;
      $("image-viewer-title").textContent =
        "Imagen · " + record.width + " × " + record.height;
      $("image-viewer-status").textContent = "Cargando original…";
      $("image-viewer-download").disabled = true;
      showDialog(viewer);
      try {
        const blob = await binary(
          `/api/projects/${projectId}/images/${record.id}`,
        );
        if (request !== viewerRequest || !imageRecord(record.id, projectId))
          return;
        viewing = { blob, file: record.file };
        viewerURL = URL.createObjectURL(blob);
        original.onload = () => {
          fitWidth = 0;
          original.hidden = false;
          $("image-zoom").value = "100";
          zoom();
        };
        original.onerror = () => {
          $("image-viewer-status").textContent =
            "No se pudo mostrar el original. Podés descargarlo.";
        };
        original.src = viewerURL;
        $("image-viewer-download").disabled = false;
        $("image-viewer-status").textContent =
          record.provider === "codex"
            ? "Codex · ChatGPT · imagen provisional"
            : record.provider + " · experimental";
      } catch (error) {
        if (request === viewerRequest)
          $("image-viewer-status").textContent = error.message;
      }
    }),
  );
  $("image-viewer-download").onclick = action(async () => {
    if (viewing) await download(viewing.blob, viewing.file);
  });
  document.addEventListener("workbench:images-render", hydrateImages);
  hydrateImages();
  const defaults = {
    openai: "gpt-image-2.5-flare",
    gemini: "gemini-3.1-flash-image",
  };
  let project = null,
    job = null,
    storage = null,
    providers = {},
    timer = null;
  const sameProject = () => project && getProject()?.id === project;
  const status = (message) => {
    $("image-status").textContent = message;
  };
  function controls() {
    const running = ["generating", "cancelling"].includes(job?.status);
    $("image-generate").disabled = running;
    $("image-cancel").hidden = !running;
    $("image-progress").hidden = !running;
    $("image-save").hidden = job?.status !== "ready";
    $("image-download").hidden = job?.status !== "ready";
    $("image-preview").hidden = job?.status !== "ready";
    if (job?.status === "ready")
      $("image-preview").src = `data:${job.mime};base64,${job.data}`;
    else $("image-preview").removeAttribute("src");
  }
  function providerFields() {
    const provider = $("image-settings-provider").value;
    $("image-key").value = "";
    $("image-remember").disabled = !storage?.available;
    $("image-remember").checked = !!storage?.stored[provider];
    $("image-key-status").textContent = providers[provider]
      ? "Clave disponible del motor editorial o de voz."
      : "Ingresá una clave API para este proveedor.";
  }
  async function gallery() {
    const data = await api(`/api/projects/${project}`);
    if (!sameProject()) return;
    galleryRecords = data.images || [];
    const list = $("image-gallery");
    list.replaceChildren();
    for (const record of data.images || []) {
      const row = document.createElement("article");
      const title = document.createElement("p");
      title.textContent = record.prompt;
      const button = (label, handler) => {
        const element = document.createElement("button");
        element.className = "secondary";
        element.textContent = label;
        element.onclick = action(handler);
        row.append(element);
      };
      const preview = document.createElement("button");
      preview.className = "image-attachment";
      preview.dataset.image = record.id;
      preview.dataset.imageProject = project;
      preview.setAttribute("aria-label", "Ampliar imagen generada");
      const thumbnail = document.createElement("img");
      thumbnail.alt = "Imagen guardada; ampliar";
      thumbnail.width = 240;
      thumbnail.height = 180;
      preview.append(thumbnail);
      row.append(preview, title);
      const load = () => binary(`/api/projects/${project}/images/${record.id}`);
      button("Descargar imagen", async () =>
        download(await load(), record.file),
      );
      button("Usar como portada 3D", async () => {
        const id = project,
          blob = await load();
        if (!sameProject() || project !== id)
          throw Error("El proyecto cambió.");
        $("images-dialog").close();
        await applyCover(blob);
      });
      list.append(row);
    }
    $("image-gallery-empty").hidden = !!data.images?.length;
    hydrateImages();
  }
  async function open() {
    if (!getProject()) throw Error("Abrí un proyecto para crear imágenes.");
    if (project !== getProject().id) {
      project = getProject().id;
      job = null;
    }
    [providers, storage] = await Promise.all([
      api("/api/images/providers"),
      api("/api/engine-storage"),
    ]);
    $("image-provider").value = preference();
    $("image-model").value = defaults[preference()];
    controls();
    showDialog($("images-dialog"));
    await gallery();
    status(
      job?.status === "ready"
        ? "Imagen provisional lista. Guardala si querés conservarla."
        : "Solo se envía la descripción que escribas aquí.",
    );
    if (["generating", "cancelling"].includes(job?.status)) poll();
  }
  async function poll() {
    clearTimeout(timer);
    if (!job || !sameProject()) return;
    const target = job;
    try {
      const result = await api("/api/images/poll", { project, id: target.id });
      if (job !== target || !sameProject()) return;
      job = result;
      controls();
      status(
        {
          generating: "Generando imagen…",
          cancelling: "Descartando resultado al terminar…",
          ready:
            "Imagen provisional lista. Guardala en el proyecto o descargala.",
          cancelled: "Generación descartada.",
          failed: job.error,
        }[job.status],
      );
      if (["generating", "cancelling"].includes(job.status))
        timer = setTimeout(poll, 1500);
    } catch (error) {
      status(error.message);
    }
  }
  $("images-open").onclick = action(open);
  $("images-close").onclick = () => $("images-dialog").close();
  $("images-dialog").addEventListener("close", () => {
    $("image-key").value = "";
    clearTimeout(timer);
  });
  function preference() {
    try {
      return Object.hasOwn(defaults, localStorage.getItem("sw-image-provider"))
        ? localStorage.getItem("sw-image-provider")
        : "openai";
    } catch {
      return "openai";
    }
  }
  async function refreshSettings() {
    const fields = [
      "image-settings-provider",
      "image-key",
      "image-key-save",
      "image-key-forget",
    ];
    for (const id of fields) $(id).disabled = true;
    try {
      [providers, storage] = await Promise.all([
        api("/api/images/providers"),
        api("/api/engine-storage"),
      ]);
      $("image-settings-provider").value = preference();
      providerFields();
    } finally {
      for (const id of fields) $(id).disabled = false;
    }
  }
  document.addEventListener("workbench:settings-open", action(refreshSettings));
  $("settings-dialog").addEventListener("close", () => {
    $("image-key").value = "";
  });
  $("image-settings-provider").onchange = action(() => {
    localStorage.setItem(
      "sw-image-provider",
      $("image-settings-provider").value,
    );
    providerFields();
  });
  $("image-settings-open").onclick = () => {
    $("images-dialog").close();
    openSettings();
    $("settings-images").scrollIntoView({ block: "start" });
    $("image-settings-provider").focus();
  };
  $("image-provider").onchange = () => {
    $("image-model").value = defaults[$("image-provider").value];
  };
  $("image-key-forget").onclick = action(async () => {
    await api("/api/engine/key", {
      provider: $("image-settings-provider").value,
      key: "",
    });
    await refreshSettings();
    $("image-settings-status").textContent =
      "Clave API compartida retirada. Una clave de voz se administra desde Voz y lectura.";
  });
  $("image-key-save").onclick = action(async () => {
    const provider = $("image-settings-provider").value,
      key = $("image-key").value.trim();
    if (!key) throw Error("Ingresá una clave API.");
    await api("/api/engine/key", {
      provider,
      key,
      remember: $("image-remember").checked,
    });
    [providers, storage] = await Promise.all([
      api("/api/images/providers"),
      api("/api/engine-storage"),
    ]);
    providerFields();
    $("image-settings-status").textContent =
      "Clave preparada. El motor editorial del proyecto conserva su selección.";
  });
  $("image-form").onsubmit = action(async (event) => {
    event.preventDefault();
    if (!sameProject())
      throw Error("El proyecto cambió. Abrí de nuevo Imágenes.");
    const id = project;
    job = await api("/api/images/start", {
      project,
      provider: $("image-provider").value,
      model: $("image-model").value.trim(),
      prompt: $("image-prompt").value,
      shape: $("image-shape").value,
      consent: $("image-consent").checked,
    });
    if (id !== project || !sameProject()) return;
    controls();
    status("Generando imagen…");
    poll();
  });
  $("image-cancel").onclick = action(async () => {
    await api("/api/images/cancel", { project, id: job.id });
    await poll();
  });
  $("image-save").onclick = action(async () => {
    if (!sameProject()) throw Error("El proyecto cambió.");
    await api("/api/images/save", { project, id: job.id });
    await gallery();
    status(
      "Imagen guardada. No cambia el manuscrito ni la portada automáticamente.",
    );
  });
  $("image-download").onclick = action(async () => {
    const bytes = Uint8Array.from(atob(job.data), (c) => c.charCodeAt(0));
    await download(
      new Blob([bytes], { type: job.mime }),
      job.id + (job.mime === "image/png" ? ".png" : ".jpg"),
    );
  });
  return { open };
}
