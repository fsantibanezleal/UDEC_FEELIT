import { bootWorkspace } from "./app.js";

const workspaceCatalogUrl = "/api/haptic-workspaces";
const createWorkspaceUrl = "/api/haptic-workspaces/create";
const registerWorkspaceUrl = "/api/haptic-workspaces/register";

function byId(id) {
  return document.getElementById(id);
}

const state = {
  workspaces: [],
  selectedSlug: null,
};

function setStatus(message, pillText = message) {
  byId("manager-status-bar").textContent = message;
  byId("manager-page-status").textContent = pillText;
}

function renderSelectedWorkspace(workspace) {
  if (!workspace) {
    byId("selected-workspace-title").textContent = "--";
    byId("selected-workspace-source").textContent = "--";
    byId("selected-workspace-models").textContent = "--";
    byId("selected-workspace-texts").textContent = "--";
    byId("selected-workspace-audio").textContent = "--";
    return;
  }

  byId("selected-workspace-title").textContent = workspace.title;
  byId("selected-workspace-source").textContent = workspace.registry_source;
  byId("selected-workspace-models").textContent = String(workspace.category_counts.models);
  byId("selected-workspace-texts").textContent = String(workspace.category_counts.texts);
  byId("selected-workspace-audio").textContent = String(workspace.category_counts.audio);
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
    path.textContent = workspace.workspace_file_path;

    button.append(title, description, meta, path);
    button.addEventListener("click", () => {
      state.selectedSlug = workspace.slug;
      renderWorkspaceList();
      renderSelectedWorkspace(workspace);
      setStatus(`Selected workspace ${workspace.title}.`, "Selected");
    });

    container.appendChild(button);
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
  state.selectedSlug = state.selectedSlug || payload.workspaces[0]?.slug || null;
  byId("workspace-count").textContent = String(payload.workspaces.length);
  byId("workspace-suffix").textContent = payload.workspace_suffix;
  byId("workspace-registry-path").textContent = payload.registry_file_path;
  renderWorkspaceList();
  renderSelectedWorkspace(
    state.workspaces.find((workspace) => workspace.slug === state.selectedSlug) ?? state.workspaces[0],
  );
  byId("manager-runtime-pill").textContent = "Registry ready";
  setStatus("Workspace registry loaded.", "Ready");
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
  byId("existing-workspace-path").value = response.workspace.workspace_file_path;
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
      byId("refresh-workspaces").addEventListener("click", () => {
        refreshCatalog().catch((error) => setStatus(error.message, "Refresh failed"));
      });

      await refreshCatalog();
    },
  );
});
