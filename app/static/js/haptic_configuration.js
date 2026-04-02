import { bootWorkspace } from "./app.js";

const configUrl = "/api/haptics/configuration";

function byId(id) {
  return document.getElementById(id);
}

const state = {
  snapshot: null,
  selectedBackendSlug: null,
};

function setStatus(message, pillText = message) {
  byId("config-status-bar").textContent = message;
  byId("config-page-status").textContent = pillText;
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail || `Request failed: ${url}`);
  }
  return response.json();
}

function backendBySlug(slug) {
  return state.snapshot?.backends?.find((backend) => backend.slug === slug) ?? null;
}

function renderSelectedBackend() {
  const backend =
    backendBySlug(state.selectedBackendSlug) ?? state.snapshot?.backends?.[0] ?? null;

  if (!backend) {
    byId("selected-backend-title").textContent = "--";
    byId("selected-backend-vendor").textContent = "--";
    byId("selected-backend-availability").textContent = "--";
    byId("selected-backend-dependencies").textContent = "--";
    byId("selected-backend-driver").textContent = "--";
    byId("selected-backend-devices").textContent = "--";
    byId("selected-backend-detected-devices").textContent = "--";
    byId("selected-backend-bridge-probe").textContent = "--";
    byId("selected-backend-probe-summary").textContent = "--";
    byId("selected-backend-device-count").textContent = "--";
    byId("selected-backend-device-selector").textContent = "--";
    byId("selected-backend-probe-mode").textContent = "--";
    byId("selected-backend-capability-scope").textContent = "--";
    byId("selected-backend-probe-capabilities").textContent = "--";
    byId("selected-backend-normalized-features").textContent = "--";
    byId("selected-backend-verified-features").textContent = "--";
    byId("selected-backend-inferred-features").textContent = "--";
    byId("backend-evidence").innerHTML = "";
    return;
  }

  byId("selected-backend-title").textContent = backend.title;
  byId("selected-backend-vendor").textContent = backend.vendor;
  byId("selected-backend-availability").textContent = backend.availability;
  byId("selected-backend-dependencies").textContent = backend.dependency_state;
  byId("selected-backend-driver").textContent = backend.driver_state;
  byId("selected-backend-devices").textContent = backend.device_detection_state;
  byId("selected-backend-detected-devices").textContent =
    backend.detected_devices.length
      ? backend.detected_devices.join(" | ")
      : "No device identities reported.";
  byId("selected-backend-bridge-probe").textContent = backend.bridge_probe_state;
  byId("selected-backend-probe-summary").textContent =
    backend.bridge_probe_summary || "No bridge-probe summary recorded.";
  byId("selected-backend-device-count").textContent =
    backend.detected_device_count == null ? "0" : String(backend.detected_device_count);
  byId("selected-backend-device-selector").textContent =
    backend.configured_device_selector || "No preferred selector configured.";
  byId("selected-backend-probe-mode").textContent =
    backend.probe_enumeration_mode || "No probe mode reported.";
  byId("selected-backend-capability-scope").textContent =
    backend.probe_capability_scope || "No capability scope reported.";
  byId("selected-backend-probe-capabilities").textContent =
    backend.reported_capabilities.length
      ? backend.reported_capabilities.join(" | ")
      : "No runtime-reported capability channels yet.";
  byId("selected-backend-normalized-features").textContent =
    backend.normalized_features.length
      ? backend.normalized_features.join(" | ")
      : "No normalized runtime feature set reported.";
  byId("selected-backend-verified-features").textContent =
    backend.verified_features.length
      ? backend.verified_features.join(" | ")
      : "No bridge-verified runtime features reported.";
  byId("selected-backend-inferred-features").textContent =
    backend.inferred_features.length
      ? backend.inferred_features.join(" | ")
      : "No inferred feature set recorded.";

  const evidenceContainer = byId("backend-evidence");
  evidenceContainer.innerHTML = "";
  backend.evidence.forEach((item) => {
    const pill = document.createElement("span");
    pill.className = "evidence-pill";
    pill.textContent = item;
    evidenceContainer.appendChild(pill);
  });
  if (!backend.evidence.length) {
    const pill = document.createElement("span");
    pill.className = "evidence-pill";
    pill.textContent = "No diagnostics recorded.";
    evidenceContainer.appendChild(pill);
  }
}

function renderBackendList() {
  const container = byId("backend-list");
  container.innerHTML = "";

  state.snapshot.backends.forEach((backend) => {
    const card = document.createElement("button");
    card.type = "button";
    card.className = "workspace-card backend-card";
    if (backend.slug === state.selectedBackendSlug) {
      card.classList.add("is-selected");
    }
    if (backend.active) {
      card.classList.add("backend-card-active");
    }

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = backend.title;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent = backend.summary;

    const meta = document.createElement("span");
    meta.className = "workspace-card-meta";
    meta.textContent =
      `${backend.vendor} | ${backend.backend_type} | ${backend.availability}`;

    const stateLine = document.createElement("span");
    stateLine.className = "workspace-card-path";
    stateLine.textContent =
      backend.active
        ? "Active runtime path"
        : backend.requested
          ? "Requested runtime target"
          : backend.install_hint;

    card.append(title, description, meta, stateLine);
    card.addEventListener("click", () => {
      state.selectedBackendSlug = backend.slug;
      byId("requested-backend").value = backend.slug;
      renderBackendList();
      renderSelectedBackend();
      setStatus(`Selected backend diagnostics for ${backend.title}.`, "Selected");
    });
    container.appendChild(card);
  });
}

function renderToolchainList() {
  const container = byId("toolchain-list");
  container.innerHTML = "";

  state.snapshot.toolchains.forEach((tool) => {
    const card = document.createElement("article");
    card.className = "workspace-card workspace-card-static";

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = tool.title;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent =
      tool.status === "ready"
        ? `${tool.status} | ${tool.detected_version || "version probe unavailable"}`
        : tool.install_hint;

    const meta = document.createElement("span");
    meta.className = "workspace-card-meta";
    meta.textContent = tool.detected_path || "No executable detected.";

    const evidence = document.createElement("span");
    evidence.className = "workspace-card-path";
    evidence.textContent = tool.evidence.join(" | ");

    card.append(title, description, meta, evidence);
    container.appendChild(card);
  });
}

function renderBridgeWorkspace() {
  const workspace = state.snapshot.bridge_workspace;
  byId("bridge-source-root").textContent = workspace.source_root;
  byId("bridge-build-root").textContent =
    `${workspace.build_root_pattern} | probe: ${workspace.probe_binary_name}`;
  byId("bridge-toolchain-summary").textContent =
    `${workspace.preferred_generator} | ${workspace.preferred_compiler} | toolchain ready: ${workspace.toolchain_ready}`;
  byId("bridge-configure-command").textContent = workspace.configure_command;
  byId("bridge-build-command").textContent = workspace.build_command;
  byId("bridge-probe-command").textContent = workspace.run_probe_command;
}

function renderSceneContractList() {
  const contract = state.snapshot.scene_contract;
  const container = byId("scene-contract-list");
  container.innerHTML = "";

  contract.mode_contracts.forEach((modeContract) => {
    const card = document.createElement("article");
    card.className = "workspace-card workspace-card-static";

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = `${modeContract.mode} | ${modeContract.route}`;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent = modeContract.bridge_goal;

    const primitives = document.createElement("span");
    primitives.className = "workspace-card-meta";
    primitives.textContent =
      `${modeContract.scene_primitives.length} bridge primitives | ${modeContract.scene_primitives.map((item) => item.slug).join(" | ")}`;

    const events = document.createElement("span");
    events.className = "workspace-card-body";
    events.textContent =
      `Return flow: launcher -> ${modeContract.return_contract.launcher_target} | home -> ${modeContract.return_contract.home_target}`;

    const telemetry = document.createElement("span");
    telemetry.className = "workspace-card-path";
    telemetry.textContent =
      modeContract.scene_primitives
        .map((item) => `${item.slug}: ${item.telemetry_fields.join(", ")}`)
        .join(" | ");

    card.append(title, description, primitives, events, telemetry);
    container.appendChild(card);
  });
}

function renderScenePrimitiveList() {
  const contract = state.snapshot.scene_contract;
  const container = byId("scene-primitive-list");
  container.innerHTML = "";

  contract.primitive_families.forEach((family) => {
    const card = document.createElement("article");
    card.className = "workspace-card workspace-card-static";

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = family.title;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent = family.summary;

    const channels = document.createElement("span");
    channels.className = "workspace-card-meta";
    channels.textContent =
      `Channels: ${family.canonical_force_channels.join(" | ")}`;

    const usage = document.createElement("span");
    usage.className = "workspace-card-path";
    usage.textContent =
      `Modes: ${family.used_by_modes.join(" | ")} | Safety: ${family.safety_constraints.join(", ")}`;

    card.append(title, description, channels, usage);
    container.appendChild(card);
  });
}

function renderSceneReadinessList() {
  const contract = state.snapshot.scene_contract;
  const container = byId("scene-readiness-list");
  container.innerHTML = "";

  contract.backend_readiness.forEach((backend) => {
    const card = document.createElement("article");
    card.className = "workspace-card workspace-card-static";

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = `${backend.title} | ${backend.current_maturity}`;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent = backend.next_milestone;

    const readiness = document.createElement("span");
    readiness.className = "workspace-card-meta";
    readiness.textContent =
      backend.ready_primitive_families.length
        ? `Ready families: ${backend.ready_primitive_families.join(" | ")}`
        : `Blocked families: ${backend.blocked_primitive_families.join(" | ")}`;

    const notes = document.createElement("span");
    notes.className = "workspace-card-path";
    notes.textContent = backend.notes.join(" | ");

    card.append(title, description, readiness, notes);
    container.appendChild(card);
  });
}

function renderContactRolloutList() {
  const rollout = state.snapshot.contact_rollout;
  const container = byId("contact-rollout-list");
  container.innerHTML = "";

  rollout.pilot_scenarios.forEach((scenario) => {
    const card = document.createElement("article");
    card.className = "workspace-card workspace-card-static";

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = `${scenario.backend_title} | ${scenario.readiness_state}`;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent = scenario.pilot_goal;

    const target = document.createElement("span");
    target.className = "workspace-card-meta";
    target.textContent =
      `${scenario.pilot_mode} | ${scenario.pilot_route} | ${scenario.pilot_primitive_slug}`;

    const requirements = document.createElement("span");
    requirements.className = "workspace-card-body";
    requirements.textContent =
      `Channels: ${scenario.required_force_channels.join(" | ")} | Scope: ${scenario.required_capability_scope} | Alignment: ${scenario.capability_alignment}`;

    const profile = document.createElement("span");
    profile.className = "workspace-card-meta";
    profile.textContent =
      `${scenario.pilot_profile.geometry_kind} | material ${scenario.material_preset_slug} | available features: ${scenario.available_runtime_features.join(" | ") || "none"}`;

    const readiness = document.createElement("span");
    readiness.className = "workspace-card-path";
    readiness.textContent =
      `${scenario.readiness_reason} Missing: ${scenario.missing_runtime_features.join(" | ") || "none"}. Next: ${scenario.next_engineering_step}`;

    card.append(title, description, target, requirements, profile, readiness);
    container.appendChild(card);
  });
}

function renderPilotCommandList() {
  const contract = state.snapshot.pilot_command_contract;
  const container = byId("pilot-command-list");
  container.innerHTML = "";

  contract.commands.forEach((command) => {
    const acknowledgement = command.acknowledgement || {
      state: "not-run",
      summary: "No acknowledgement data recorded yet.",
      accepted: false,
    };
    const card = document.createElement("article");
    card.className = "workspace-card workspace-card-static";

    const title = document.createElement("strong");
    title.className = "workspace-card-title";
    title.textContent = `${command.backend_slug} | ${command.command_slug}`;

    const description = document.createElement("span");
    description.className = "workspace-card-body";
    description.textContent =
      `${command.transport.mode} | ${command.force_model.model_slug} | readiness ${command.readiness_state}`;

    const geometry = document.createElement("span");
    geometry.className = "workspace-card-meta";
    geometry.textContent =
      `${command.pilot_mode} | ${command.primitive_slug} | ${command.geometry_profile.geometry_kind} | material ${command.material_preset_slug}`;

    const envelope = document.createElement("span");
    envelope.className = "workspace-card-body";
    envelope.textContent =
      `Force channels: ${command.force_model.channels.join(" | ")} | Max force ${command.safety_envelope.max_force_n} N`;

    const acknowledgementLine = document.createElement("span");
    acknowledgementLine.className = "workspace-card-meta";
    acknowledgementLine.textContent =
      `Ack: ${acknowledgement.state} | accepted ${acknowledgement.accepted ? "yes" : "no"}`;

    const notes = document.createElement("span");
    notes.className = "workspace-card-path";
    notes.textContent =
      `Missing features: ${command.missing_runtime_features.join(" | ") || "none"} | ${acknowledgement.summary}`;

    const nextStep = document.createElement("span");
    nextStep.className = "workspace-card-path";
    nextStep.textContent = `Next: ${command.next_engineering_step}`;

    card.append(title, description, geometry, envelope, acknowledgementLine, notes, nextStep);
    container.appendChild(card);
  });
}

function applyFormValues(snapshot) {
  byId("requested-backend").innerHTML = "";
  snapshot.backends.forEach((backend) => {
    const option = document.createElement("option");
    option.value = backend.slug;
    option.textContent = backend.title;
    byId("requested-backend").appendChild(option);
  });
  byId("requested-backend").value = snapshot.requested_backend;
  byId("sdk-openhaptics").value =
    snapshot.backends.find((item) => item.slug === "openhaptics-touch")?.configured_sdk_root ||
    snapshot.backends.find((item) => item.slug === "openhaptics-touch")?.detected_sdk_root ||
    "";
  byId("sdk-forcedimension").value =
    snapshot.backends.find((item) => item.slug === "forcedimension-dhd")?.configured_sdk_root ||
    snapshot.backends.find((item) => item.slug === "forcedimension-dhd")?.detected_sdk_root ||
    "";
  byId("sdk-chai3d").value =
    snapshot.backends.find((item) => item.slug === "chai3d-bridge")?.configured_sdk_root ||
    snapshot.backends.find((item) => item.slug === "chai3d-bridge")?.detected_sdk_root ||
    "";
  byId("bridge-openhaptics").value =
    snapshot.backends.find((item) => item.slug === "openhaptics-touch")?.configured_bridge_path ||
    snapshot.backends.find((item) => item.slug === "openhaptics-touch")?.detected_bridge_path ||
    "";
  byId("bridge-forcedimension").value =
    snapshot.backends.find((item) => item.slug === "forcedimension-dhd")?.configured_bridge_path ||
    snapshot.backends.find((item) => item.slug === "forcedimension-dhd")?.detected_bridge_path ||
    "";
  byId("bridge-chai3d").value =
    snapshot.backends.find((item) => item.slug === "chai3d-bridge")?.configured_bridge_path ||
    snapshot.backends.find((item) => item.slug === "chai3d-bridge")?.detected_bridge_path ||
    "";
  byId("selector-openhaptics").value =
    snapshot.backends.find((item) => item.slug === "openhaptics-touch")?.configured_device_selector ||
    "";
  byId("selector-forcedimension").value =
    snapshot.backends.find((item) => item.slug === "forcedimension-dhd")?.configured_device_selector ||
    "";
  byId("selector-chai3d").value =
    snapshot.backends.find((item) => item.slug === "chai3d-bridge")?.configured_device_selector ||
    "";
}

function renderSnapshot(snapshot) {
  state.snapshot = snapshot;
  state.selectedBackendSlug =
    state.selectedBackendSlug ||
    snapshot.requested_backend ||
    snapshot.backends[0]?.slug ||
    null;

  byId("config-requested-backend").textContent = snapshot.requested_backend;
  byId("config-active-backend").textContent = snapshot.active_backend_title;
  byId("config-file-label").textContent = snapshot.config_file_label;
  byId("config-servo-target").textContent = `${snapshot.contact_design.servo_loop_target_hz} Hz`;
  byId("config-visual-target").textContent = `${snapshot.contact_design.visual_loop_target_hz} Hz`;
  byId("config-backend-count").textContent = String(snapshot.backends.length);
  byId("collision-summary").textContent = snapshot.contact_design.collision_strategy.summary;
  byId("material-rendering-summary").textContent =
    `${snapshot.material_rendering.length} material profiles mapped to explicit haptic rendering strategies.`;
  byId("scene-contract-summary").textContent =
    `${snapshot.scene_contract.mode_contracts.length} routed mode contracts | ${snapshot.scene_contract.primitive_families.length} primitive families | ${snapshot.scene_contract.event_contract.length} event transitions | ${snapshot.scene_contract.backend_readiness.length} backend readiness rows.`;
  byId("contact-rollout-summary").textContent =
    `${snapshot.contact_rollout.pilot_scenarios.length} backend-specific pilot scenarios now connect runtime readiness to one bounded contact milestone each.`;
  byId("pilot-command-summary").textContent =
    `${snapshot.pilot_command_contract.commands.length} dry-run pilot command payloads are now available, and each one now records whether the current bridge boundary can already acknowledge it.`;
  byId("config-runtime-pill").textContent = "Runtime mapped";
  applyFormValues(snapshot);
  renderBackendList();
  renderSelectedBackend();
  renderToolchainList();
  renderBridgeWorkspace();
  renderSceneContractList();
  renderScenePrimitiveList();
  renderSceneReadinessList();
  renderContactRolloutList();
  renderPilotCommandList();
  setStatus(snapshot.selection_summary, "Ready");
}

async function refreshConfiguration() {
  const snapshot = await fetchJson(configUrl);
  renderSnapshot(snapshot);
}

async function saveConfiguration() {
  const payload = {
    requested_backend: byId("requested-backend").value,
    sdk_roots: {
      openhaptics: byId("sdk-openhaptics").value,
      forcedimension: byId("sdk-forcedimension").value,
      chai3d: byId("sdk-chai3d").value,
    },
    bridge_paths: {
      openhaptics: byId("bridge-openhaptics").value,
      forcedimension: byId("bridge-forcedimension").value,
      chai3d: byId("bridge-chai3d").value,
    },
    device_selectors: {
      openhaptics: byId("selector-openhaptics").value,
      forcedimension: byId("selector-forcedimension").value,
      chai3d: byId("selector-chai3d").value,
    },
  };
  const snapshot = await fetchJson(configUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  renderSnapshot(snapshot);
  setStatus(`Saved haptic runtime selection for ${snapshot.requested_backend}.`, "Saved");
}

document.addEventListener("DOMContentLoaded", () => {
  bootWorkspace(
    {
      title: "Haptic Configuration startup failed",
      runtimePillId: "config-runtime-pill",
      runtimePillText: "Runtime error",
      pageStatusId: "config-page-status",
      pageStatusText: "Boot failed",
      stageStatusId: "config-status-bar",
      summaryIds: [
        "config-requested-backend",
        "config-active-backend",
        "config-file-label",
        "config-servo-target",
        "config-visual-target",
      ],
    },
    async () => {
      byId("refresh-haptic-config").addEventListener("click", () => {
        refreshConfiguration().catch((error) => setStatus(error.message, "Refresh failed"));
      });
      byId("apply-haptic-config").addEventListener("click", () => {
        saveConfiguration().catch((error) => setStatus(error.message, "Save failed"));
      });
      byId("requested-backend").addEventListener("change", (event) => {
        state.selectedBackendSlug = event.target.value;
        renderBackendList();
        renderSelectedBackend();
      });

      await refreshConfiguration();
    },
  );
});
