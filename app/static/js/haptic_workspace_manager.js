import { bootWorkspace } from "./app.js";

const workspaceCatalogUrl = "/api/haptic-workspaces";
const createWorkspaceUrl = "/api/haptic-workspaces/create";
const registerWorkspaceUrl = "/api/haptic-workspaces/register";

function byId(id) {
  return document.getElementById(id);
}

const state = {
  workspaces: [],
  invalidWorkspaces: [],
  selectedSlug: null,
  descriptorPreview: null,
};

function setStatus(message, pillText = message) {
  byId("manager-status-bar").textContent = message;
  byId("manager-page-status").textContent = pillText;
}

function selectedWorkspace() {
  return state.workspaces.find((workspace) => workspace.slug === state.selectedSlug) ?? null;
}

function formatPreviewItems(items = []) {
  if (!items.length) {
    return "None.";
  }
  return items.map((item) => `${item.title || item.slug} (${item.source_kind || "unknown"})`).join(", ");
}

function renderDescriptorEditPreview() {
  const container = byId("descriptor-edit-preview-body");
  const workspace = selectedWorkspace();
  container.innerHTML = "";

  if (!workspace || !state.descriptorPreview?.can_edit) {
    const message = document.createElement("p");
    message.className = "panel-text";
    message.textContent = "Select one user-registered workspace to preview descriptor edits.";
    container.appendChild(message);
    return;
  }

  const refreshLibraries = byId("edit-refresh-libraries").checked;
  const rootsChanged =
    byId("edit-content-root-path").value.trim() !== state.descriptorPreview.content_root.path ||
    byId("edit-file-browser-root-path").value.trim() !== state.descriptorPreview.file_browser_root.path;

  const summary = document.createElement("div");
  summary.className = "status-stack";
  summary.innerHTML = `
    <div class="status-card">
      <span class="status-label">Pending title</span>
      <span class="status-value">${byId("edit-workspace-title").value.trim() || "--"}</span>
    </div>
    <div class="status-card">
      <span class="status-label">Pending content root</span>
      <span class="status-value">${byId("edit-content-root-path").value.trim() || "--"}</span>
    </div>
    <div class="status-card">
      <span class="status-label">Pending file-browser root</span>
      <span class="status-value">${byId("edit-file-browser-root-path").value.trim() || "--"}</span>
    </div>
    <div class="status-card">
      <span class="status-label">Library rewrite</span>
      <span class="status-value">${refreshLibraries || rootsChanged ? "Libraries will be rebuilt from disk." : "Existing descriptor libraries will be preserved."}</span>
    </div>
  `;
  container.appendChild(summary);
}

function syncDescriptorEditor(workspace, preview) {
  const editable = Boolean(workspace && preview?.can_edit);
  byId("edit-workspace-title").disabled = !editable;
  byId("edit-workspace-description").disabled = !editable;
  byId("edit-content-root-path").disabled = !editable;
  byId("edit-file-browser-root-path").disabled = !editable;
  byId("edit-refresh-libraries").disabled = !editable;
  byId("save-workspace-descriptor").disabled = !editable;

  if (!workspace || !preview) {
    byId("edit-workspace-title").value = "";
    byId("edit-workspace-description").value = "";
    byId("edit-content-root-path").value = "";
    byId("edit-file-browser-root-path").value = "";
    byId("edit-refresh-libraries").checked = false;
    byId("descriptor-editor-note").textContent =
      "Select one user-registered workspace to review or edit its descriptor.";
    renderDescriptorEditPreview();
    return;
  }

  byId("edit-workspace-title").value = preview.title || "";
  byId("edit-workspace-description").value = preview.description || "";
  byId("edit-content-root-path").value = preview.content_root.path || "";
  byId("edit-file-browser-root-path").value = preview.file_browser_root.path || "";
  byId("edit-refresh-libraries").checked = false;
  byId("descriptor-editor-note").textContent = preview.can_edit
    ? "Edit descriptor metadata and roots here. Root changes automatically force a library rebuild on save."
    : "The bundled demo workspace can be previewed but not edited from the manager.";
  renderDescriptorEditPreview();
}

function renderSelectedWorkspacePreview(preview) {
  const container = byId("selected-workspace-preview");
  container.innerHTML = "";

  if (!preview) {
    const message = document.createElement("p");
    message.className = "panel-text";
    message.textContent = "Select one workspace to inspect its current descriptor state.";
    container.appendChild(message);
    return;
  }

  const current = preview.libraries.categories;
  const rescan = preview.rescan_preview.categories;
  const summary = document.createElement("div");
  summary.className = "status-stack";
  summary.innerHTML = `
    <div class="status-card">
      <span class="status-label">Slug</span>
      <span class="status-value">${preview.slug}</span>
    </div>
    <div class="status-card">
      <span class="status-label">Descriptor file</span>
      <span class="status-value">${preview.workspace_file_label}</span>
    </div>
    <div class="status-card">
      <span class="status-label">Content root</span>
      <span class="status-value">${preview.content_root.path}</span>
    </div>
    <div class="status-card">
      <span class="status-label">File-browser root</span>
      <span class="status-value">${preview.file_browser_root.path}</span>
    </div>
  `;
  container.appendChild(summary);

  ["models", "texts", "audio"].forEach((category) => {
    const card = document.createElement("div");
    card.className = "status-card";
    card.innerHTML = `
      <span class="status-label">${category}</span>
      <span class="status-value">Current ${current[category].count} | Rescan ${rescan[category].rescanned_count} | Delta ${rescan[category].delta >= 0 ? "+" : ""}${rescan[category].delta}</span>
      <span class="workspace-card-body">Current preview: ${formatPreviewItems(current[category].items)}</span>
      <span class="workspace-card-body">Would add: ${formatPreviewItems(rescan[category].added_preview)}</span>
      <span class="workspace-card-body">Would remove: ${formatPreviewItems(rescan[category].removed_preview)}</span>
    `;
    container.appendChild(card);
  });
}

async function loadDescriptorPreview(slug) {
  const preview = await fetchJson(`/api/haptic-workspaces/${slug}/descriptor`);
  state.descriptorPreview = preview;
  syncDescriptorEditor(selectedWorkspace(), preview);
  renderSelectedWorkspacePreview(preview);
}

function syncSelectedWorkspaceActions(workspace) {
  const canManage = Boolean(workspace?.can_unregister);
  byId("rescan-workspace").disabled = !workspace?.can_rescan;
  byId("unregister-workspace").disabled = !canManage;

  if (!workspace) {
    byId("selected-workspace-action-note").textContent =
      "Select one registry-backed workspace to manage its lifecycle.";
    return;
  }

  byId("selected-workspace-action-note").textContent = canManage
    ? "Rescan rebuilds the library lists from the current workspace root. Unregister removes the descriptor reference from the local registry only."
    : "The bundled demo workspace is built into FeelIT and cannot be unregistered from the local registry.";
}

function renderSelectedWorkspace(workspace) {
  if (!workspace) {
    byId("selected-workspace-title").textContent = "--";
    byId("selected-workspace-source").textContent = "--";
    byId("selected-workspace-file").textContent = "--";
    byId("selected-workspace-models").textContent = "--";
    byId("selected-workspace-texts").textContent = "--";
    byId("selected-workspace-audio").textContent = "--";
    state.descriptorPreview = null;
    syncSelectedWorkspaceActions(null);
    syncDescriptorEditor(null, null);
    renderSelectedWorkspacePreview(null);
    return;
  }

  byId("selected-workspace-title").textContent = workspace.title;
  byId("selected-workspace-source").textContent = workspace.registry_source;
  byId("selected-workspace-file").textContent = workspace.workspace_file_label;
  byId("selected-workspace-models").textContent = String(workspace.category_counts.models);
  byId("selected-workspace-texts").textContent = String(workspace.category_counts.texts);
  byId("selected-workspace-audio").textContent = String(workspace.category_counts.audio);
  syncSelectedWorkspaceActions(workspace);
}

function renderWorkspaceList() {
  const container = byId("workspace-list");
  container.innerHTML = "";

  state.workspaces.forEach((workspace) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "workspace-card";
    if (workspace.slug === state.selectedSlug) {
      button.classList.add("is-selected");
    }

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = workspace.title;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent = workspace.description || "No description recorded.";

    const meta = document.createElement("span");
    meta.className = "workspace-card-meta";
    meta.textContent =
      `${workspace.registry_source} | models ${workspace.category_counts.models} | texts ${workspace.category_counts.texts} | audio ${workspace.category_counts.audio}`;

    const path = document.createElement("span");
    path.className = "workspace-card-path";
    path.textContent = workspace.workspace_file_label;

    button.append(title, description, meta, path);
    button.addEventListener("click", () => {
      state.selectedSlug = workspace.slug;
      renderWorkspaceList();
      renderSelectedWorkspace(workspace);
      setStatus(`Selected workspace ${workspace.title}.`, "Selected");
      loadDescriptorPreview(workspace.slug).catch((error) => setStatus(error.message, "Preview failed"));
    });

    container.appendChild(button);
  });
}

function renderInvalidWorkspaceList() {
  const container = byId("invalid-workspace-list");
  container.innerHTML = "";

  if (state.invalidWorkspaces.length === 0) {
    const message = document.createElement("p");
    message.className = "panel-text";
    message.textContent = "No invalid registered workspace descriptors were detected.";
    container.appendChild(message);
    return;
  }

  state.invalidWorkspaces.forEach((workspace) => {
    const card = document.createElement("article");
    card.className = "workspace-card workspace-card-invalid";

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = workspace.error_code === "missing_file" ? "Missing workspace file" : "Invalid workspace descriptor";

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent = workspace.error;

    const meta = document.createElement("span");
    meta.className = "workspace-card-meta";
    meta.textContent = workspace.registry_source;

    const path = document.createElement("span");
    path.className = "workspace-card-path";
    path.textContent = workspace.workspace_file_label;

    if (workspace.repair_preview) {
      const preview = document.createElement("div");
      preview.className = "workspace-card-preview";
      preview.innerHTML = `
        <span class="status-label">Repair preview</span>
        <span class="workspace-card-body">Would normalize to slug <strong>${workspace.repair_preview.slug}</strong> and title <strong>${workspace.repair_preview.title}</strong>.</span>
        <span class="workspace-card-body">Content root: ${workspace.repair_preview.content_root.path}</span>
        <span class="workspace-card-body">File-browser root: ${workspace.repair_preview.file_browser_root.path}</span>
        <span class="workspace-card-body">Resulting counts: models ${workspace.repair_preview.libraries.categories.models.count} | texts ${workspace.repair_preview.libraries.categories.texts.count} | audio ${workspace.repair_preview.libraries.categories.audio.count}</span>
      `;
      card.appendChild(preview);
    }

    const actions = document.createElement("div");
    actions.className = "workspace-card-actions";

    if (workspace.can_repair) {
      const repairButton = document.createElement("button");
      repairButton.type = "button";
      repairButton.className = "btn btn-secondary";
      repairButton.textContent = "Repair + Rescan";
      repairButton.addEventListener("click", () => {
        repairInvalidWorkspace(workspace).catch((error) => setStatus(error.message, "Repair failed"));
      });
      actions.appendChild(repairButton);
    }

    if (workspace.can_unregister) {
      const forgetButton = document.createElement("button");
      forgetButton.type = "button";
      forgetButton.className = "btn btn-danger";
      forgetButton.textContent = "Forget Entry";
      forgetButton.addEventListener("click", () => {
        unregisterWorkspaceByRegistryKey(workspace.registry_key, workspace.workspace_file_label, "Forgot").catch(
          (error) => setStatus(error.message, "Forget failed"),
        );
      });
      actions.appendChild(forgetButton);
    }

    card.append(title, description, meta, path, actions);
    container.appendChild(card);
  });
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed: ${url}`);
  }
  return response.json();
}

async function refreshCatalog() {
  const payload = await fetchJson(workspaceCatalogUrl);
  state.workspaces = payload.workspaces;
  state.invalidWorkspaces = payload.invalid_workspaces || [];
  state.selectedSlug = state.selectedSlug || payload.workspaces[0]?.slug || null;
  byId("workspace-count").textContent = String(payload.workspaces.length);
  byId("invalid-workspace-count").textContent = String(state.invalidWorkspaces.length);
  byId("workspace-suffix").textContent = payload.workspace_suffix;
  byId("workspace-registry-path").textContent = payload.registry_file_label;
  renderWorkspaceList();
  renderInvalidWorkspaceList();
  renderSelectedWorkspace(
    state.workspaces.find((workspace) => workspace.slug === state.selectedSlug) ?? state.workspaces[0],
  );
  if (state.selectedSlug) {
    await loadDescriptorPreview(state.selectedSlug);
  } else {
    state.descriptorPreview = null;
    syncDescriptorEditor(null, null);
    renderSelectedWorkspacePreview(null);
  }
  byId("manager-runtime-pill").textContent = "Registry ready";
  setStatus(
    state.invalidWorkspaces.length > 0
      ? `Workspace registry loaded with ${state.invalidWorkspaces.length} invalid descriptor(s).`
      : "Workspace registry loaded.",
    state.invalidWorkspaces.length > 0 ? "Warning" : "Ready",
  );
}

async function createWorkspace() {
  const payload = {
    title: byId("workspace-title").value.trim(),
    slug: byId("workspace-slug").value.trim() || null,
    description: byId("workspace-description").value.trim(),
    root_path: byId("workspace-root-path").value.trim(),
    auto_populate: byId("workspace-auto-populate").checked,
  };
  const response = await fetchJson(createWorkspaceUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  setStatus(`Created workspace ${response.workspace.title}.`, "Created");
  await refreshCatalog();
}

async function registerWorkspace() {
  const payload = {
    workspace_file_path: byId("existing-workspace-path").value.trim(),
  };
  const response = await fetchJson(registerWorkspaceUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  setStatus(`Registered workspace ${response.workspace.title}.`, "Registered");
  await refreshCatalog();
}

async function unregisterWorkspaceByRegistryKey(registryKey, workspaceLabel, pillText = "Unregistered") {
  await fetchJson(`/api/haptic-workspaces/${registryKey}`, {
    method: "DELETE",
  });
  setStatus(`${workspaceLabel} was removed from the local registry.`, pillText);
  await refreshCatalog();
}

async function rescanSelectedWorkspace() {
  const workspace = selectedWorkspace();
  if (!workspace?.can_rescan) {
    return;
  }
  const response = await fetchJson(`/api/haptic-workspaces/${workspace.slug}/rescan`, {
    method: "POST",
  });
  setStatus(`Rescanned workspace ${response.workspace.title}.`, "Rescanned");
  await refreshCatalog();
}

async function unregisterSelectedWorkspace() {
  const workspace = selectedWorkspace();
  if (!workspace?.can_unregister) {
    return;
  }
  await unregisterWorkspaceByRegistryKey(workspace.registry_key, workspace.title);
}

async function repairInvalidWorkspace(workspace) {
  const response = await fetchJson(`/api/haptic-workspaces/invalid/${workspace.registry_key}/repair`, {
    method: "POST",
  });
  setStatus(`Repaired workspace ${response.workspace.title}.`, "Repaired");
  await refreshCatalog();
}

async function saveSelectedWorkspaceDescriptor() {
  const workspace = selectedWorkspace();
  if (!workspace || !state.descriptorPreview?.can_edit) {
    return;
  }
  const response = await fetchJson(`/api/haptic-workspaces/${workspace.slug}/descriptor`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: byId("edit-workspace-title").value.trim(),
      description: byId("edit-workspace-description").value.trim(),
      content_root_path: byId("edit-content-root-path").value.trim(),
      file_browser_root_path: byId("edit-file-browser-root-path").value.trim(),
      refresh_libraries: byId("edit-refresh-libraries").checked,
    }),
  });
  setStatus(`Updated descriptor for ${response.workspace.title}.`, "Updated");
  await refreshCatalog();
}

document.addEventListener("DOMContentLoaded", () => {
  bootWorkspace(
    {
      title: "Haptic Workspace Manager startup failed",
      runtimePillId: "manager-runtime-pill",
      runtimePillText: "Runtime error",
      pageStatusId: "manager-page-status",
      pageStatusText: "Boot failed",
      stageStatusId: "manager-status-bar",
      summaryIds: [
        "selected-workspace-title",
        "selected-workspace-source",
        "selected-workspace-models",
        "selected-workspace-texts",
        "selected-workspace-audio",
      ],
    },
    async () => {
      byId("create-workspace").addEventListener("click", () => {
        createWorkspace().catch((error) => setStatus(error.message, "Create failed"));
      });
      byId("register-workspace").addEventListener("click", () => {
        registerWorkspace().catch((error) => setStatus(error.message, "Register failed"));
      });
      byId("rescan-workspace").addEventListener("click", () => {
        rescanSelectedWorkspace().catch((error) => setStatus(error.message, "Rescan failed"));
      });
      byId("unregister-workspace").addEventListener("click", () => {
        unregisterSelectedWorkspace().catch((error) => setStatus(error.message, "Unregister failed"));
      });
      byId("save-workspace-descriptor").addEventListener("click", () => {
        saveSelectedWorkspaceDescriptor().catch((error) => setStatus(error.message, "Save failed"));
      });
      [
        "edit-workspace-title",
        "edit-workspace-description",
        "edit-content-root-path",
        "edit-file-browser-root-path",
        "edit-refresh-libraries",
      ].forEach((id) => {
        byId(id).addEventListener("input", renderDescriptorEditPreview);
        byId(id).addEventListener("change", renderDescriptorEditPreview);
      });
      byId("refresh-workspaces").addEventListener("click", () => {
        refreshCatalog().catch((error) => setStatus(error.message, "Refresh failed"));
      });

      await refreshCatalog();
    },
  );
});
