import { THREE, createWorkspaceScene } from "./three_scene_common.js";

const previewUrl = "/api/braille/preview";

const state = {
  cells: [],
  columns: 8,
  rowsPerPage: 4,
  currentPage: 0,
  selectedCellId: null,
  meshByCellId: new Map(),
};

function byId(id) {
  return document.getElementById(id);
}

function setStatus(message) {
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
  byId("preview-row-count").textContent = String(pageCells.length ? Math.max(...pageCells.map((cell) => cell.localRow)) + 1 : 0);
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

function highlightSelectedMesh(sceneApi, pageCells) {
  state.meshByCellId.forEach((mesh, cellId) => {
    const isSelected = cellId === state.selectedCellId;
    mesh.traverse((node) => {
      if (!node.isMesh) {
        return;
      }
      if (node.userData.kind === "active-dot") {
        node.material.emissive.setHex(isSelected ? 0x1f6feb : 0x4a2d00);
      }
      if (node.userData.kind === "cell-base") {
        node.material.color.setHex(isSelected ? 0x1c2b3f : 0x111827);
      }
    });
  });

  const selected = pageCells.find((cell) => cell.cellId === state.selectedCellId);
  if (selected) {
    const x = (selected.column - (state.columns - 1) / 2) * 0.34;
    const z = (selected.localRow - ((state.rowsPerPage - 1) / 2)) * 0.48;
    sceneApi.setPointerPosition(new THREE.Vector3(x, 0.22, z));
    updateSelectedCell(selected);
  }
}

function selectCell(sceneApi, pageCells, cellId) {
  state.selectedCellId = cellId;
  document.querySelectorAll(".braille-cell-button").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.cellId === cellId);
  });
  highlightSelectedMesh(sceneApi, pageCells);
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
    button.addEventListener("click", () => selectCell(sceneApi, pageCells, cell.cellId));

    rows.get(cell.localRow).appendChild(button);
  }
}

function createBrailleWorld(sceneApi, pageCells) {
  sceneApi.clearWorld();
  state.meshByCellId.clear();

  const boardWidth = Math.max(2.4, state.columns * 0.34 + 0.8);
  const boardDepth = Math.max(1.6, state.rowsPerPage * 0.48 + 0.6);
  sceneApi.setBoundarySize(new THREE.Vector3(boardWidth + 0.6, 0.8, boardDepth + 0.6));
  sceneApi.controls.target.set(0, 0.14, 0);
  sceneApi.controls.update();

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(boardWidth, 0.12, boardDepth),
    new THREE.MeshStandardMaterial({ color: 0x16213a, roughness: 0.9, metalness: 0.05 }),
  );
  base.position.y = 0.06;
  sceneApi.world.add(base);

  for (const cell of pageCells) {
    const cellGroup = new THREE.Group();
    const x = (cell.column - (state.columns - 1) / 2) * 0.34;
    const z = (cell.localRow - ((state.rowsPerPage - 1) / 2)) * 0.48;
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

    state.meshByCellId.set(cell.cellId, cellGroup);
    sceneApi.world.add(cellGroup);
  }
}

function renderCurrentPage(sceneApi) {
  const pageCells = getPageCells();
  updateSummary(pageCells);
  createBrailleWorld(sceneApi, pageCells);
  render2DBoard(sceneApi, pageCells);

  if (!pageCells.some((cell) => cell.cellId === state.selectedCellId)) {
    state.selectedCellId = pageCells[0]?.cellId ?? null;
  }
  if (state.selectedCellId) {
    selectCell(sceneApi, pageCells, state.selectedCellId);
  }
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
  setStatus(`Generated ${payload.cell_count} tactile cells.`);
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
    selectCell(sceneApi, pageCells, next.cellId);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  await window.FeelITShell.loadShell();

  const sceneApi = createWorkspaceScene(byId("braille-canvas"), {
    cameraPosition: [2.4, 2.2, 3.2],
    target: [0, 0.14, 0],
    boundarySize: new THREE.Vector3(3.6, 0.8, 2.8),
  });

  byId("generate-preview").addEventListener("click", () => {
    loadPreview(sceneApi).catch((error) => setStatus(error.message));
  });

  byId("load-sample-text").addEventListener("click", () => {
    byId("preview-text").value =
      "Braille reading should remain tactile, spatial, and independent from the audio channel when needed.";
    loadPreview(sceneApi).catch((error) => setStatus(error.message));
  });

  byId("rows-per-page").addEventListener("change", () => {
    state.rowsPerPage = Number(byId("rows-per-page").value) || 4;
    state.currentPage = 0;
    renderCurrentPage(sceneApi);
  });

  byId("preview-columns").addEventListener("change", () => {
    loadPreview(sceneApi).catch((error) => setStatus(error.message));
  });

  byId("cell-scale").addEventListener("change", (event) => {
    applyScale(event.target.value);
  });

  byId("braille-boundary-toggle").addEventListener("change", (event) => {
    sceneApi.setBoundaryVisible(event.target.checked);
  });

  byId("prev-page").addEventListener("click", () => {
    state.currentPage = Math.max(0, state.currentPage - 1);
    renderCurrentPage(sceneApi);
  });

  byId("next-page").addEventListener("click", () => {
    state.currentPage = Math.min(getPageCount() - 1, state.currentPage + 1);
    renderCurrentPage(sceneApi);
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
