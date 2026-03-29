import {
  THREE,
  attachPointerEmulation,
  createLabelSprite,
  createWorkspaceScene,
} from "./three_scene_common.js";

const previewUrl = "/api/braille/preview";

const state = {
  cells: [],
  columns: 8,
  rowsPerPage: 4,
  currentPage: 0,
  selectedCellId: null,
  hoveredTargetId: null,
  interactiveGroups: new Map(),
  targetById: new Map(),
  pointerController: null,
  lastStatusKey: "",
};

function byId(id) {
  return document.getElementById(id);
}

function setStatus(message, key = message) {
  if (state.lastStatusKey === key) {
    return;
  }
  state.lastStatusKey = key;
  byId("reader-status-bar").textContent = message;
  byId("reader-page-status").textContent = message;
}

function buildDot(active) {
  const dot = document.createElement("span");
  dot.className = active ? "braille-dot is-active" : "braille-dot";
  return dot;
}

function applyScale(scale) {
  const board = byId("braille-board");
  board.classList.remove(
    "braille-scale-compact",
    "braille-scale-standard",
    "braille-scale-large",
  );
  board.classList.add(`braille-scale-${scale}`);
  byId("reader-scale-label").textContent = scale[0].toUpperCase() + scale.slice(1);
}

function getPageCount() {
  const maxRow = state.cells.length ? Math.max(...state.cells.map((cell) => cell.row)) + 1 : 0;
  return Math.max(1, Math.ceil(maxRow / state.rowsPerPage));
}

function getPageCells() {
  const rowStart = state.currentPage * state.rowsPerPage;
  const rowEnd = rowStart + state.rowsPerPage;
  return state.cells
    .filter((cell) => cell.row >= rowStart && cell.row < rowEnd)
    .map((cell) => ({
      ...cell,
      localRow: cell.row - rowStart,
      cellId: `${cell.row}-${cell.column}`,
    }));
}

function updateSummary(pageCells) {
  const totalRows = state.cells.length ? Math.max(...state.cells.map((cell) => cell.row)) + 1 : 0;
  byId("preview-cell-count").textContent = String(pageCells.length);
  byId("preview-row-count").textContent = String(
    pageCells.length ? Math.max(...pageCells.map((cell) => cell.localRow)) + 1 : 0,
  );
  byId("summary-characters").textContent = String(state.cells.length);
  byId("summary-columns").textContent = String(state.columns);
  byId("summary-rows").textContent = String(totalRows);
  byId("page-indicator").textContent = `${state.currentPage + 1} / ${getPageCount()}`;
}

function updateSelectedCell(cell) {
  if (!cell) {
    return;
  }
  byId("selected-source").textContent = cell.source || "space";
  byId("selected-normalized").textContent = cell.normalized || "space";
  byId("selected-mask").textContent = String(cell.mask);
  byId("selected-position").textContent = `r${cell.row} c${cell.column}`;
  byId("summary-unicode").textContent = cell.unicode_cell;
}

function render2DBoard(sceneApi, pageCells) {
  const board = byId("braille-board");
  board.innerHTML = "";
  const rows = new Map();

  for (const cell of pageCells) {
    if (!rows.has(cell.localRow)) {
      const row = document.createElement("div");
      row.className = "braille-row";
      rows.set(cell.localRow, row);
      board.appendChild(row);
    }

    const button = document.createElement("button");
    button.type = "button";
    button.className = "braille-cell-button";
    button.dataset.cellId = cell.cellId;

    const matrix = document.createElement("span");
    matrix.className = "braille-cell-matrix";
    cell.dots.forEach((active) => matrix.appendChild(buildDot(active)));

    const caption = document.createElement("span");
    caption.className = "braille-caption";
    caption.textContent = `${cell.source} ${cell.unicode_cell}`;

    button.appendChild(matrix);
    button.appendChild(caption);
    button.addEventListener("click", () => {
      state.selectedCellId = cell.cellId;
      state.hoveredTargetId = cell.cellId;
      focusSelectedCell(sceneApi, pageCells);
    });

    rows.get(cell.localRow).appendChild(button);
  }
}

function createBrailleCellGroup(cell) {
  const cellGroup = new THREE.Group();
  const x = (cell.column - (state.columns - 1) / 2) * 0.34;
  const z = (cell.localRow - ((state.rowsPerPage - 1) / 2)) * 0.48 - 0.18;
  cellGroup.position.set(x, 0.121, z);

  const cellBase = new THREE.Mesh(
    new THREE.BoxGeometry(0.22, 0.025, 0.3),
    new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.84, metalness: 0.04 }),
  );
  cellBase.position.y = 0.012;
  cellBase.userData.kind = "cell-base";
  cellGroup.add(cellBase);

  const offsets = [
    [-0.045, 0.06],
    [0.045, 0.06],
    [-0.045, 0],
    [0.045, 0],
    [-0.045, -0.06],
    [0.045, -0.06],
  ];

  cell.dots.forEach((active, index) => {
    if (!active) {
      return;
    }
    const dot = new THREE.Mesh(
      new THREE.SphereGeometry(0.032, 18, 14, 0, Math.PI * 2, 0, Math.PI / 2),
      new THREE.MeshStandardMaterial({
        color: 0xf2cc60,
        roughness: 0.35,
        metalness: 0.02,
        emissive: 0x4a2d00,
      }),
    );
    dot.rotation.x = Math.PI;
    dot.position.set(offsets[index][0], 0.05, offsets[index][1]);
    dot.userData.kind = "active-dot";
    cellGroup.add(dot);
  });

  return {
    group: cellGroup,
    target: {
      id: cell.cellId,
      type: "cell",
      title: `Cell ${cell.row + 1}:${cell.column + 1}`,
      position: new THREE.Vector3(x, 0.2, z),
      radius: 0.16,
      cell,
    },
  };
}

function buildGuideRail(length, thickness, depth, color) {
  return new THREE.Mesh(
    new THREE.BoxGeometry(length, thickness, depth),
    new THREE.MeshStandardMaterial({
      color,
      roughness: 0.82,
      metalness: 0.05,
      emissive: 0x09111c,
    }),
  );
}

function buildOrientationMarker() {
  const group = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.CylinderGeometry(0.08, 0.08, 0.05, 24),
    new THREE.MeshStandardMaterial({
      color: 0x0f1724,
      roughness: 0.86,
      metalness: 0.04,
    }),
  );
  base.position.y = 0.025;
  group.add(base);

  const wedge = new THREE.Mesh(
    new THREE.ConeGeometry(0.07, 0.14, 3),
    new THREE.MeshStandardMaterial({
      color: 0xf2cc60,
      roughness: 0.32,
      metalness: 0.04,
      emissive: 0x4a2d00,
    }),
  );
  wedge.rotation.y = -Math.PI / 2;
  wedge.position.y = 0.11;
  group.add(wedge);

  return group;
}

function buildPageBridge(pageText, boardDepth) {
  const bridge = new THREE.Group();

  const pillarLeft = new THREE.Mesh(
    new THREE.BoxGeometry(0.06, 0.26, 0.06),
    new THREE.MeshStandardMaterial({ color: 0x0f1724, roughness: 0.9, metalness: 0.05 }),
  );
  pillarLeft.position.set(-0.45, 0.13, -boardDepth / 2 + 0.15);
  bridge.add(pillarLeft);

  const pillarRight = pillarLeft.clone();
  pillarRight.position.x = 0.45;
  bridge.add(pillarRight);

  const header = new THREE.Mesh(
    new THREE.BoxGeometry(1.04, 0.05, 0.08),
    new THREE.MeshStandardMaterial({
      color: 0x1a2940,
      roughness: 0.78,
      metalness: 0.08,
      emissive: 0x0a1420,
    }),
  );
  header.position.set(0, 0.26, -boardDepth / 2 + 0.15);
  bridge.add(header);

  const label = createLabelSprite(pageText, {
    background: "rgba(13,17,23,0.8)",
    fontSize: 18,
  });
  label.position.set(0, 0.33, -boardDepth / 2 + 0.15);
  bridge.add(label);

  return bridge;
}

function buildTactileControlMesh(kind, active) {
  const group = new THREE.Group();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(0.44, 0.06, 0.3),
    new THREE.MeshStandardMaterial({
      color: active ? 0x20324a : 0x1a1f28,
      roughness: 0.8,
      metalness: 0.08,
    }),
  );
  base.position.y = 0.03;
  base.userData.kind = "control-base";
  group.add(base);

  if (kind === "previous") {
    [-0.1, 0, 0.1].forEach((offset) => {
      const ridge = new THREE.Mesh(
        new THREE.CylinderGeometry(0.028, 0.028, 0.2, 18),
        new THREE.MeshStandardMaterial({
          color: active ? 0x7ee787 : 0x4b5563,
          roughness: 0.35,
          metalness: 0.04,
          emissive: 0x16301a,
        }),
      );
      ridge.rotation.z = Math.PI / 2;
      ridge.position.set(offset, 0.09, 0);
      ridge.userData.kind = "control-ridge";
      group.add(ridge);
    });
  } else {
    const dome = new THREE.Mesh(
      new THREE.SphereGeometry(0.072, 20, 16),
      new THREE.MeshStandardMaterial({
        color: active ? 0x58a6ff : 0x4b5563,
        roughness: 0.32,
        metalness: 0.05,
        emissive: 0x14263d,
      }),
    );
    dome.scale.set(1, 0.72, 1);
    dome.position.set(0, 0.1, 0);
    dome.userData.kind = "control-ridge";
    group.add(dome);

    const arrow = new THREE.Mesh(
      new THREE.ConeGeometry(0.055, 0.14, 3),
      new THREE.MeshStandardMaterial({
        color: active ? 0x79c0ff : 0x52525b,
        roughness: 0.38,
        metalness: 0.05,
        emissive: 0x14263d,
      }),
    );
    arrow.rotation.z = -Math.PI / 2;
    arrow.position.set(0.14, 0.1, 0);
    arrow.userData.kind = "control-ridge";
    group.add(arrow);
  }

  return group;
}

function createSceneControls(sceneApi) {
  const controlZ = ((state.rowsPerPage - 1) / 2) * 0.48 + 0.5;
  return [
    {
      id: "control-previous",
      type: "control",
      title: "Previous page tactile control",
      kind: "previous",
      active: state.currentPage > 0,
      position: new THREE.Vector3(-0.62, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        if (state.currentPage <= 0) {
          setStatus("Previous page tactile control is disabled.", "control-prev-disabled");
          return;
        }
        state.currentPage -= 1;
        state.selectedCellId = null;
        renderCurrentPage(sceneApi);
        setStatus("Moved to previous Braille page.", "page-prev");
      },
    },
    {
      id: "control-next",
      type: "control",
      title: "Next page tactile control",
      kind: "next",
      active: state.currentPage < getPageCount() - 1,
      position: new THREE.Vector3(0.62, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        if (state.currentPage >= getPageCount() - 1) {
          setStatus("Next page tactile control is disabled.", "control-next-disabled");
          return;
        }
        state.currentPage += 1;
        state.selectedCellId = null;
        renderCurrentPage(sceneApi);
        setStatus("Moved to next Braille page.", "page-next");
      },
    },
  ];
}

function refreshInteractiveVisuals() {
  state.interactiveGroups.forEach((group, targetId) => {
    const target = state.targetById.get(targetId);
    const isHovered = targetId === state.hoveredTargetId;
    const isSelectedCell = target.type === "cell" && targetId === state.selectedCellId;

    group.traverse((node) => {
      if (!node.isMesh) {
        return;
      }

      if (target.type === "cell") {
        if (node.userData.kind === "active-dot") {
          node.material.emissive.setHex(isHovered || isSelectedCell ? 0x1f6feb : 0x4a2d00);
        }
        if (node.userData.kind === "cell-base") {
          node.material.color.setHex(isHovered || isSelectedCell ? 0x1c2b3f : 0x111827);
        }
        return;
      }

      if (node.userData.kind === "control-base") {
        node.material.color.setHex(
          !target.active
            ? 0x1a1f28
            : isHovered
              ? 0x1f3855
              : 0x20324a,
        );
      }
      if (node.userData.kind === "control-ridge") {
        node.material.emissive.setHex(isHovered && target.active ? 0x1f6feb : 0x14263d);
      }
    });
  });
}

function focusSelectedCell(sceneApi, pageCells) {
  document.querySelectorAll(".braille-cell-button").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.cellId === state.selectedCellId);
  });

  const selected = pageCells.find((cell) => cell.cellId === state.selectedCellId);
  if (!selected) {
    refreshInteractiveVisuals();
    return;
  }

  const x = (selected.column - (state.columns - 1) / 2) * 0.34;
  const z = (selected.localRow - ((state.rowsPerPage - 1) / 2)) * 0.48 - 0.18;
  state.pointerController?.setPosition(new THREE.Vector3(x, 0.22, z));
  updateSelectedCell(selected);
  refreshInteractiveVisuals();
}

function updatePointerTarget(sceneApi, position, pageCells) {
  let nearestTarget = null;
  let nearestDistance = Number.POSITIVE_INFINITY;

  state.targetById.forEach((target) => {
    const distance = target.position.distanceTo(position);
    if (distance <= target.radius && distance < nearestDistance) {
      nearestTarget = target;
      nearestDistance = distance;
    }
  });

  const nextHoveredId = nearestTarget?.id ?? null;
  if (state.hoveredTargetId !== nextHoveredId) {
    state.hoveredTargetId = nextHoveredId;
    refreshInteractiveVisuals();
  }

  if (!nearestTarget) {
    sceneApi.setPointerState("idle");
    setStatus("Pointer moving over the reading surface.", "pointer-surface");
    return;
  }

  sceneApi.setPointerState("focus");
  if (nearestTarget.type === "cell") {
    state.selectedCellId = nearestTarget.id;
    updateSelectedCell(nearestTarget.cell);
    document.querySelectorAll(".braille-cell-button").forEach((button) => {
      button.classList.toggle("is-selected", button.dataset.cellId === nearestTarget.id);
    });
    setStatus(
      `Pointer over Braille cell ${nearestTarget.cell.row + 1}:${nearestTarget.cell.column + 1}.`,
      nearestTarget.id,
    );
    refreshInteractiveVisuals();
    return;
  }

  setStatus(nearestTarget.title, nearestTarget.id);
}

function activatePointerTarget(sceneApi, pageCells) {
  const target = state.targetById.get(state.hoveredTargetId);
  if (!target) {
    setStatus("No tactile target is currently under the pointer.", "no-target");
    return;
  }

  sceneApi.setPointerState("active");
  window.setTimeout(() => {
    updatePointerTarget(sceneApi, state.pointerController.position, getPageCells());
  }, 180);

  if (target.type === "control") {
    target.action?.();
    return;
  }

  setStatus(
    `Selected Braille cell ${target.cell.row + 1}:${target.cell.column + 1}.`,
    `activate-${target.id}`,
  );
}

function createBrailleWorld(sceneApi, pageCells) {
  sceneApi.clearWorld();
  state.interactiveGroups.clear();
  state.targetById.clear();

  const boardWidth = Math.max(2.4, state.columns * 0.34 + 0.8);
  const boardDepth = Math.max(1.9, state.rowsPerPage * 0.48 + 1.15);
  sceneApi.setBoundarySize(new THREE.Vector3(boardWidth + 0.7, 0.95, boardDepth + 0.45));
  sceneApi.controls.target.set(0, 0.18, 0.08);
  sceneApi.controls.update();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(boardWidth, 0.12, boardDepth),
    new THREE.MeshStandardMaterial({ color: 0x16213a, roughness: 0.9, metalness: 0.05 }),
  );
  base.position.y = 0.06;
  sceneApi.world.add(base);

  const leftRail = buildGuideRail(boardDepth - 0.12, 0.08, 0.12, 0x0f1724);
  leftRail.rotation.y = Math.PI / 2;
  leftRail.position.set(-boardWidth / 2 + 0.1, 0.1, -0.02);
  sceneApi.world.add(leftRail);

  const frontLip = buildGuideRail(boardWidth - 0.18, 0.05, 0.08, 0x111827);
  frontLip.position.set(0, 0.085, boardDepth / 2 - 0.14);
  sceneApi.world.add(frontLip);

  const orientationMarker = buildOrientationMarker();
  orientationMarker.position.set(-boardWidth / 2 + 0.18, 0.08, -boardDepth / 2 + 0.22);
  sceneApi.world.add(orientationMarker);

  for (const cell of pageCells) {
    const { group, target } = createBrailleCellGroup(cell);
    state.interactiveGroups.set(target.id, group);
    state.targetById.set(target.id, target);
    sceneApi.world.add(group);
  }

  const sceneControls = createSceneControls(sceneApi);
  sceneControls.forEach((control) => {
    const controlGroup = buildTactileControlMesh(control.kind, control.active);
    controlGroup.position.copy(control.position.clone().setY(0.12));

    state.interactiveGroups.set(control.id, controlGroup);
    state.targetById.set(control.id, control);
    sceneApi.world.add(controlGroup);
  });

  sceneApi.world.add(buildPageBridge(`Page ${state.currentPage + 1} / ${getPageCount()}`, boardDepth));

  const minBounds = new THREE.Vector3(-boardWidth / 2, 0.14, -boardDepth / 2 + 0.02);
  const maxBounds = new THREE.Vector3(boardWidth / 2, 0.34, boardDepth / 2 - 0.02);
  state.pointerController?.setBounds(minBounds, maxBounds);
}

function renderCurrentPage(sceneApi) {
  const pageCells = getPageCells();
  updateSummary(pageCells);
  createBrailleWorld(sceneApi, pageCells);
  render2DBoard(sceneApi, pageCells);

  if (!pageCells.some((cell) => cell.cellId === state.selectedCellId)) {
    state.selectedCellId = pageCells[0]?.cellId ?? null;
  }
  state.hoveredTargetId = state.selectedCellId;
  if (state.selectedCellId) {
    focusSelectedCell(sceneApi, pageCells);
  } else {
    refreshInteractiveVisuals();
  }

  state.pointerController?.setPosition(
    state.selectedCellId && state.targetById.has(state.selectedCellId)
      ? state.targetById.get(state.selectedCellId).position.clone().setY(0.22)
      : new THREE.Vector3(0, 0.22, 0.2),
  );
  updatePointerTarget(sceneApi, state.pointerController.position, pageCells);
}

async function loadPreview(sceneApi) {
  state.columns = Number(byId("preview-columns").value) || 8;
  state.rowsPerPage = Number(byId("rows-per-page").value) || 4;

  const response = await fetch(previewUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: byId("preview-text").value.trim() || "FeelIT",
      columns: state.columns,
    }),
  });
  if (!response.ok) {
    throw new Error("Preview request failed.");
  }

  const payload = await response.json();
  state.cells = payload.cells;
  state.currentPage = 0;
  renderCurrentPage(sceneApi);
  setStatus(`Generated ${payload.cell_count} tactile cells.`, "preview-generated");
}

function moveSelection(sceneApi, deltaRow, deltaColumn) {
  const pageCells = getPageCells();
  const current = pageCells.find((cell) => cell.cellId === state.selectedCellId) ?? pageCells[0];
  if (!current) {
    return;
  }
  const nextRow = current.localRow + deltaRow;
  const nextColumn = current.column + deltaColumn;
  const next = pageCells.find((cell) => cell.localRow === nextRow && cell.column === nextColumn);
  if (next) {
    state.selectedCellId = next.cellId;
    state.hoveredTargetId = next.cellId;
    focusSelectedCell(sceneApi, pageCells);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await window.FeelITShell.loadShell();

  const sceneApi = createWorkspaceScene(byId("braille-canvas"), {
    cameraPosition: [2.4, 2.2, 3.2],
    target: [0, 0.18, 0.08],
    boundarySize: new THREE.Vector3(3.6, 0.95, 3.2),
  });

  state.pointerController = attachPointerEmulation(sceneApi, {
    initialPosition: new THREE.Vector3(0, 0.22, 0.2),
    boundsMin: new THREE.Vector3(-1.6, 0.14, -1.2),
    boundsMax: new THREE.Vector3(1.6, 0.34, 1.4),
    speed: 1.4,
    onMove: (position) => updatePointerTarget(sceneApi, position, getPageCells()),
    onActivate: () => activatePointerTarget(sceneApi, getPageCells()),
  });

  byId("generate-preview").addEventListener("click", () => {
    loadPreview(sceneApi).catch((error) => setStatus(error.message, "preview-error"));
  });

  byId("load-sample-text").addEventListener("click", () => {
    byId("preview-text").value =
      "Braille reading should remain tactile, spatial, and independent from the audio channel when needed.";
    loadPreview(sceneApi).catch((error) => setStatus(error.message, "sample-error"));
  });

  byId("rows-per-page").addEventListener("change", () => {
    state.rowsPerPage = Number(byId("rows-per-page").value) || 4;
    state.currentPage = 0;
    renderCurrentPage(sceneApi);
  });

  byId("preview-columns").addEventListener("change", () => {
    loadPreview(sceneApi).catch((error) => setStatus(error.message, "columns-error"));
  });

  byId("cell-scale").addEventListener("change", (event) => {
    applyScale(event.target.value);
  });

  byId("braille-boundary-toggle").addEventListener("change", (event) => {
    sceneApi.setBoundaryVisible(event.target.checked);
  });

  byId("prev-page").addEventListener("click", () => {
    state.currentPage = Math.max(0, state.currentPage - 1);
    state.selectedCellId = null;
    renderCurrentPage(sceneApi);
    setStatus("Moved to previous page with fallback web control.", "fallback-prev");
  });

  byId("next-page").addEventListener("click", () => {
    state.currentPage = Math.min(getPageCount() - 1, state.currentPage + 1);
    state.selectedCellId = null;
    renderCurrentPage(sceneApi);
    setStatus("Moved to next page with fallback web control.", "fallback-next");
  });

  document.addEventListener("keydown", (event) => {
    if (event.target.tagName === "TEXTAREA" || event.target.tagName === "INPUT") {
      return;
    }
    if (event.key === "ArrowLeft") moveSelection(sceneApi, 0, -1);
    if (event.key === "ArrowRight") moveSelection(sceneApi, 0, 1);
    if (event.key === "ArrowUp") moveSelection(sceneApi, -1, 0);
    if (event.key === "ArrowDown") moveSelection(sceneApi, 1, 0);
  });

  applyScale("standard");
  await loadPreview(sceneApi);
});
