const healthUrl = "/api/health";
const metaUrl = "/api/meta";

function byId(id) {
  return document.getElementById(id);
}

function updateRuntimeSlot(name, value) {
  document.querySelectorAll(`[data-runtime="${name}"]`).forEach((element) => {
    element.textContent = value;
  });
}

function openModal(modalId) {
  const modal = byId(modalId);
  if (modal) {
    modal.classList.add("modal-visible");
  }
}

function closeModal(modalId) {
  const modal = byId(modalId);
  if (modal) {
    modal.classList.remove("modal-visible");
  }
}

let modalsBound = false;

export function bindModals() {
  if (modalsBound) {
    return;
  }
  modalsBound = true;

  document.querySelectorAll("[data-open-modal]").forEach((button) => {
    button.addEventListener("click", () => {
      openModal(button.getAttribute("data-open-modal"));
    });
  });

  document.querySelectorAll("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", () => {
      closeModal(button.getAttribute("data-close-modal"));
    });
  });

  document.querySelectorAll(".modal").forEach((modal) => {
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        modal.classList.remove("modal-visible");
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      document.querySelectorAll(".modal.modal-visible").forEach((modal) => {
        modal.classList.remove("modal-visible");
      });
    }
  });
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  return response.json();
}

function formatErrorMessage(error) {
  const fallback = "Workspace bootstrap failed.";
  if (!error) {
    return fallback;
  }
  if (typeof error === "string") {
    return error;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

function resolveStageElement(stageSelector) {
  if (!stageSelector) {
    return null;
  }

  const target = document.querySelector(stageSelector);
  if (!target) {
    return null;
  }

  if (target.classList.contains("workspace-stage")) {
    return target;
  }

  return target.closest(".workspace-stage");
}

export function clearStageBootError(stageSelector) {
  const stage = resolveStageElement(stageSelector);
  stage?.querySelector(".stage-error-overlay")?.remove();
}

export function showStageBootError(stageSelector, title, message) {
  const stage = resolveStageElement(stageSelector);
  if (!stage) {
    return;
  }

  clearStageBootError(stageSelector);

  const overlay = document.createElement("div");
  overlay.className = "stage-error-overlay";

  const heading = document.createElement("strong");
  heading.className = "stage-error-title";
  heading.textContent = title;

  const body = document.createElement("p");
  body.className = "stage-error-body";
  body.textContent = message;

  overlay.appendChild(heading);
  overlay.appendChild(body);
  stage.appendChild(overlay);
}

function setElementText(id, text) {
  const element = byId(id);
  if (element) {
    element.textContent = text;
  }
}

export async function loadShell() {
  bindModals();
  const [health, meta] = await Promise.all([fetchJson(healthUrl), fetchJson(metaUrl)]);

  updateRuntimeSlot("api-status", health.status);
  updateRuntimeSlot("version", `v${meta.version}`);
  updateRuntimeSlot("port", String(meta.public_port));
  updateRuntimeSlot("haptics-mode", health.haptics.mode);
  updateRuntimeSlot("backend", health.haptics.backend);

  return { health, meta };
}

export function reportWorkspaceBootError(options, error) {
  const title = options.title ?? "Workspace startup failed";
  const message = formatErrorMessage(error);
  const stageMessage = `Unable to initialize this workspace: ${message}`;
  const pageStatusText = options.pageStatusText ?? "Boot failed";
  const pillText = options.runtimePillText ?? "Runtime error";

  console.error(`[${title}] ${message}`, error);

  updateRuntimeSlot("api-status", "error");
  updateRuntimeSlot("backend", "error");
  updateRuntimeSlot("haptics-mode", "unavailable");
  document.querySelectorAll('[data-runtime="version"]').forEach((element) => {
    if (element.textContent.trim() === "v--" || element.textContent.trim() === "Loading") {
      element.textContent = "Error";
    }
  });

  if (options.runtimePillId) {
    const pill = byId(options.runtimePillId);
    if (pill) {
      pill.textContent = pillText;
      pill.classList.remove("status-pill-cyan", "status-pill-green", "status-pill-purple");
      pill.classList.add("status-pill-danger");
    }
  }

  if (options.pageStatusId) {
    setElementText(options.pageStatusId, pageStatusText);
  }
  if (options.stageStatusId) {
    setElementText(options.stageStatusId, stageMessage);
  }
  if (options.summaryIds) {
    options.summaryIds.forEach((id) => setElementText(id, message));
  }

  showStageBootError(options.stageSelector, title, message);
}

export async function bootWorkspace(options, callback) {
  try {
    const shell = await loadShell();
    await callback(shell);
    clearStageBootError(options.stageSelector);
  } catch (error) {
    reportWorkspaceBootError(options, error);
  }
}

window.FeelITShell = {
  bindModals,
  bootWorkspace,
  loadShell,
  reportWorkspaceBootError,
};
