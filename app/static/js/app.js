(() => {
  "use strict";

  const healthUrl = "/api/health";
  const metaUrl = "/api/meta";

  function updateRuntimeSlot(name, value) {
    document.querySelectorAll(`[data-runtime="${name}"]`).forEach((element) => {
      element.textContent = value;
    });
  }

  function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add("modal-visible");
    }
  }

  function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove("modal-visible");
    }
  }

  function bindModals() {
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

  async function loadShell() {
    bindModals();
    const [health, meta] = await Promise.all([fetchJson(healthUrl), fetchJson(metaUrl)]);

    updateRuntimeSlot("api-status", health.status);
    updateRuntimeSlot("version", `v${meta.version}`);
    updateRuntimeSlot("port", String(meta.public_port));
    updateRuntimeSlot("haptics-mode", health.haptics.mode);
    updateRuntimeSlot("backend", health.haptics.backend);

    return { health, meta };
  }

  window.FeelITShell = {
    loadShell,
  };
})();
