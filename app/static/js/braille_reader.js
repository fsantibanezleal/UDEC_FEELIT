import { bootWorkspace } from "./app.js";
import {
  THREE,
  attachPointerEmulation,
  createLabelSprite,
  createWorkspaceScene,
} from "./three_scene_common.js";

const previewUrl = "/api/braille/preview";
const documentsUrl = "/api/library/documents";
const audioUrl = "/api/library/audio";
const LIBRARY_PAGE_SIZE = 3;

const state = {
  cells: [],
  columns: 8,
  rowsPerPage: 4,
  currentPage: 0,
  libraryPage: 0,
  sceneMode: "library-launcher",
  selectedLibrarySlug: null,
  selectedCellId: null,
  hoveredTargetId: null,
  interactiveGroups: new Map(),
  targetById: new Map(),
  pointerController: null,
  lastStatusKey: "",
  libraryDocuments: [],
  libraryAudio: [],
  activeDocumentPayload: null,
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

function fetchJson(url) {
  return fetch(url).then((response) => {
    if (!response.ok) {
      throw new Error(`Request failed: ${url}`);
    }
    return response.json();
  });
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

function populateSelect(select, items, valueField, labelField) {
  select.innerHTML = "";
  items.forEach((item) => {
    const option = document.createElement("option");
    option.value = item[valueField];
    option.textContent = item[labelField];
    select.appendChild(option);
  });
}

function setSceneMode(mode) {
  state.sceneMode = mode;
  const label = mode === "library-launcher" ? "Library launcher" : "Reading scene";
  byId("reader-scene-mode").textContent = label;
  byId("reader-scene-pill").textContent = label;
  byId("reader-page-status").textContent = label;
}

function documentBySlug(slug) {
  return state.libraryDocuments.find((document) => document.slug === slug) ?? null;
}

function currentDocument() {
  return documentBySlug(byId("library-document-select").value);
}

function currentAudio() {
  return state.libraryAudio.find((audio) => audio.slug === byId("library-audio-select").value);
}

function selectedLibraryDocument() {
  return documentBySlug(state.selectedLibrarySlug) ?? currentDocument();
}

function libraryPageCount() {
  return Math.max(1, Math.ceil(state.libraryDocuments.length / LIBRARY_PAGE_SIZE));
}

function libraryPageSlice(page = state.libraryPage) {
  const safePage = Math.min(Math.max(page, 0), libraryPageCount() - 1);
  const start = safePage * LIBRARY_PAGE_SIZE;
  return {
    page: safePage,
    pageCount: libraryPageCount(),
    documents: state.libraryDocuments.slice(start, start + LIBRARY_PAGE_SIZE),
  };
}

function libraryPageForSlug(slug) {
  const index = state.libraryDocuments.findIndex((document) => document.slug === slug);
  if (index < 0) {
    return 0;
  }
  return Math.floor(index / LIBRARY_PAGE_SIZE);
}

function clearSelectedCellPanel() {
  byId("selected-source").textContent = "--";
  byId("selected-normalized").textContent = "--";
  byId("selected-mask").textContent = "--";
  byId("selected-position").textContent = "--";
  byId("summary-unicode").textContent = "--";
}

function updateFallbackPageButtons() {
  const disabled = state.sceneMode !== "reading" || state.cells.length === 0;
  byId("prev-page").disabled = disabled;
  byId("next-page").disabled = disabled;
}

function setSelectedLibraryDocument(slug, options = {}) {
  const { syncSelect = true, syncAudio = true } = options;
  const document = documentBySlug(slug);
  if (!document) {
    return null;
  }

  state.selectedLibrarySlug = document.slug;
  if (syncSelect) {
    byId("library-document-select").value = document.slug;
  }
  updateDocumentPanel(document, state.activeDocumentPayload?.slug === document.slug ? state.activeDocumentPayload : null);
  if (syncAudio) {
    syncCompanionAudio(document);
  }
  updateAudioPanel();
  return document;
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

function updateLibrarySummary(pageSlice) {
  byId("preview-cell-count").textContent = String(pageSlice.documents.length);
  byId("preview-row-count").textContent = "1";
  byId("summary-characters").textContent = state.activeDocumentPayload?.slug === state.selectedLibrarySlug
    ? String(state.activeDocumentPayload.total_characters)
    : "0";
  byId("summary-columns").textContent = String(state.columns);
  byId("summary-rows").textContent = "0";
  byId("page-indicator").textContent = `Library ${pageSlice.page + 1} / ${pageSlice.pageCount}`;
  clearSelectedCellPanel();
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

function updateDocumentPanel(document, payload = null) {
  if (!document) {
    return;
  }
  const effectivePayload =
    payload ??
    (state.activeDocumentPayload?.slug === document.slug ? state.activeDocumentPayload : null);
  const audioTitles = document.companion_audio_slugs
    .map((slug) => state.libraryAudio.find((audio) => audio.slug === slug)?.title ?? slug)
    .join(", ");
  byId("library-document-author").textContent = document.author;
  byId("library-document-format").textContent = document.format.toUpperCase();
  byId("library-document-summary").textContent = document.summary;
  byId("summary-document-title").textContent = document.title;
  byId("summary-document-source").textContent = document.source_name;
  byId("summary-document-audio").textContent =
    document.companion_audio_slugs.length > 0 ? audioTitles : "No paired track";

  if (effectivePayload) {
    const start = effectivePayload.loaded_characters
      ? effectivePayload.offset + 1
      : effectivePayload.offset;
    const end = effectivePayload.offset + effectivePayload.loaded_characters;
    byId("library-document-range").textContent = `${start} - ${end} / ${effectivePayload.total_characters}`;
    byId("summary-document-characters").textContent = String(effectivePayload.total_characters);
    byId("load-previous-segment").disabled = effectivePayload.previous_offset === null;
    byId("load-next-segment").disabled = effectivePayload.next_offset === null;
    return;
  }

  byId("library-document-range").textContent = "0 - 0";
  byId("summary-document-characters").textContent = "0";
  byId("load-previous-segment").disabled = true;
  byId("load-next-segment").disabled = true;
}

function updateAudioPanel(audio = currentAudio()) {
  const player = byId("library-audio-player");
  if (!audio) {
    player.removeAttribute("src");
    player.load();
    byId("library-audio-summary").textContent =
      "Optional audio references remain secondary to tactile reading.";
    return;
  }

  player.src = audio.file_url;
  player.load();
  byId("library-audio-summary").textContent =
    `${audio.title} by ${audio.creator}. Source: ${audio.source_name}.`;
}

function syncCompanionAudio(document) {
  if (!document || document.companion_audio_slugs.length === 0) {
    return;
  }
  const preferredAudio = document.companion_audio_slugs.find((slug) =>
    state.libraryAudio.some((audio) => audio.slug === slug),
  );
  if (!preferredAudio) {
    return;
  }
  byId("library-audio-select").value = preferredAudio;
  updateAudioPanel();
}

function render2DBoard(pageCells) {
  byId("braille-board-note").textContent = "Secondary debug view for the generated Braille page.";
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
      focusSelectedCell(pageCells);
    });

    rows.get(cell.localRow).appendChild(button);
  }
}

function renderLibraryBoard(pageSlice) {
  byId("braille-board-note").textContent = "Secondary launcher map for the current library page.";
  const board = byId("braille-board");
  board.innerHTML = "";

  const row = document.createElement("div");
  row.className = "braille-row";
  board.appendChild(row);

  pageSlice.documents.forEach((libraryDocument) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "braille-cell-button braille-library-card";
    button.classList.toggle("is-selected", libraryDocument.slug === state.selectedLibrarySlug);
    button.dataset.documentSlug = libraryDocument.slug;

    const title = document.createElement("strong");
    title.className = "braille-library-title";
    title.textContent = libraryDocument.title;

    const meta = document.createElement("span");
    meta.className = "braille-library-meta";
    meta.textContent = `${libraryDocument.author} • ${libraryDocument.format.toUpperCase()}`;

    const summary = document.createElement("span");
    summary.className = "braille-library-summary";
    summary.textContent = libraryDocument.summary;

    button.appendChild(title);
    button.appendChild(meta);
    button.appendChild(summary);
    button.addEventListener("click", () => {
      setSelectedLibraryDocument(libraryDocument.slug);
      loadDocumentSegment(sceneApiRef, 0, { documentSlug: libraryDocument.slug }).catch((error) =>
        setStatus(error.message, `library-board-${libraryDocument.slug}-error`),
      );
    });

    row.appendChild(button);
  });
}

function createBrailleCellGroup(cell) {
  const cellGroup = new THREE.Group();
  const x = (cell.column - (state.columns - 1) / 2) * 0.34;
  const z = cell.localRow * 0.48 - ((state.rowsPerPage - 1) * 0.24) - 0.18;
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

function createLibraryDocumentGroup(document, position) {
  const group = new THREE.Group();
  group.position.copy(position.clone().setY(0.12));

  const pages = new THREE.Mesh(
    new THREE.BoxGeometry(0.56, 0.12, 0.38),
    new THREE.MeshStandardMaterial({
      color: 0xe5e7eb,
      roughness: 0.78,
      metalness: 0.04,
    }),
  );
  pages.position.y = 0.08;
  pages.userData.kind = "document-pages";
  group.add(pages);

  const cover = new THREE.Mesh(
    new THREE.BoxGeometry(0.6, 0.05, 0.42),
    new THREE.MeshStandardMaterial({
      color: 0x1a2940,
      roughness: 0.56,
      metalness: 0.08,
      emissive: 0x0a1420,
    }),
  );
  cover.position.y = 0.145;
  cover.userData.kind = "document-cover";
  group.add(cover);

  const spine = new THREE.Mesh(
    new THREE.BoxGeometry(0.08, 0.16, 0.42),
    new THREE.MeshStandardMaterial({
      color: 0xf2cc60,
      roughness: 0.34,
      metalness: 0.04,
      emissive: 0x4a2d00,
    }),
  );
  spine.position.set(-0.26, 0.1, 0);
  spine.userData.kind = "document-spine";
  group.add(spine);

  const badge = new THREE.Mesh(
    new THREE.CylinderGeometry(0.05, 0.05, 0.04, 20),
    new THREE.MeshStandardMaterial({
      color: document.companion_audio_slugs.length > 0 ? 0x79c0ff : 0x4b5563,
      roughness: 0.32,
      metalness: 0.06,
      emissive: document.companion_audio_slugs.length > 0 ? 0x163f63 : 0x0f1724,
    }),
  );
  badge.rotation.x = Math.PI / 2;
  badge.position.set(0.18, 0.18, 0);
  badge.userData.kind = "document-badge";
  group.add(badge);

  const label = createLabelSprite(document.title, {
    background: "rgba(13,17,23,0.86)",
    fontSize: 17,
    color: "#f0f6fc",
  });
  label.position.set(0, 0.38, 0);
  group.add(label);

  return {
    group,
    target: {
      id: `library-document-${document.slug}`,
      type: "library-document",
      title: document.title,
      position: position.clone().setY(0.22),
      radius: 0.32,
      document,
      action: async () => {
        setSelectedLibraryDocument(document.slug);
        await loadDocumentSegment(sceneApiRef, 0, { documentSlug: document.slug });
      },
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
  } else if (kind === "next") {
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
  } else if (kind === "library") {
    [-0.1, 0, 0.1].forEach((offset, index) => {
      const book = new THREE.Mesh(
        new THREE.BoxGeometry(0.11, 0.035, 0.2),
        new THREE.MeshStandardMaterial({
          color: active ? 0xf2cc60 : 0x52525b,
          roughness: 0.36,
          metalness: 0.04,
          emissive: 0x4a2d00,
        }),
      );
      book.position.set(offset, 0.08 + index * 0.035, 0);
      book.userData.kind = "control-ridge";
      group.add(book);
    });
  } else if (kind === "segment-previous" || kind === "segment-next") {
    [-0.08, 0.08].forEach((offset) => {
      const marker = new THREE.Mesh(
        new THREE.CylinderGeometry(0.026, 0.026, 0.12, 18),
        new THREE.MeshStandardMaterial({
          color: active ? 0x39d2c0 : 0x4b5563,
          roughness: 0.34,
          metalness: 0.04,
          emissive: 0x123129,
        }),
      );
      marker.rotation.z = Math.PI / 2;
      marker.position.set(offset, 0.095, 0);
      marker.userData.kind = "control-ridge";
      group.add(marker);
    });

    const arrow = new THREE.Mesh(
      new THREE.ConeGeometry(0.05, 0.12, 3),
      new THREE.MeshStandardMaterial({
        color: active ? 0x39d2c0 : 0x52525b,
        roughness: 0.34,
        metalness: 0.04,
        emissive: 0x123129,
      }),
    );
    arrow.rotation.z = kind === "segment-next" ? -Math.PI / 2 : Math.PI / 2;
    arrow.position.set(kind === "segment-next" ? 0.15 : -0.15, 0.1, 0);
    arrow.userData.kind = "control-ridge";
    group.add(arrow);
  } else {
    const hub = new THREE.Mesh(
      new THREE.CylinderGeometry(0.1, 0.14, 0.1, 24),
      new THREE.MeshStandardMaterial({
        color: active ? 0x39d2c0 : 0x4b5563,
        roughness: 0.34,
        metalness: 0.05,
        emissive: 0x123129,
      }),
    );
    hub.position.y = 0.1;
    hub.userData.kind = "control-ridge";
    group.add(hub);
  }

  return group;
}

function createLibraryControls(pageSlice) {
  const controlZ = 1.44;
  return [
    {
      id: "launcher-hub",
      type: "control",
      title: "Library launcher hub",
      kind: "hub",
      active: true,
      position: new THREE.Vector3(0, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        const currentDocumentTitle = selectedLibraryDocument()?.title ?? "No bundled document";
        setStatus(
          `Library launcher page ${pageSlice.page + 1} of ${pageSlice.pageCount}. Selected document: ${currentDocumentTitle}.`,
          `launcher-hub-${pageSlice.page}`,
        );
      },
    },
    {
      id: "launcher-previous",
      type: "control",
      title: "Previous library page control",
      kind: "previous",
      active: pageSlice.page > 0,
      position: new THREE.Vector3(-1.08, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        if (pageSlice.page <= 0) {
          setStatus("Previous library page tactile control is disabled.", "launcher-prev-disabled");
          return;
        }
        state.libraryPage = pageSlice.page - 1;
        renderLibraryLauncher(sceneApiRef);
        setStatus("Moved to previous library page.", "launcher-prev");
      },
    },
    {
      id: "launcher-next",
      type: "control",
      title: "Next library page control",
      kind: "next",
      active: pageSlice.page < pageSlice.pageCount - 1,
      position: new THREE.Vector3(1.08, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        if (pageSlice.page >= pageSlice.pageCount - 1) {
          setStatus("Next library page tactile control is disabled.", "launcher-next-disabled");
          return;
        }
        state.libraryPage = pageSlice.page + 1;
        renderLibraryLauncher(sceneApiRef);
        setStatus("Moved to next library page.", "launcher-next");
      },
    },
  ];
}

function createReadingControls(boardDepth) {
  const controlZ = ((state.rowsPerPage - 1) / 2) * 0.48 + 0.56;
  const segmentZ = -boardDepth / 2 + 0.34;
  return [
    {
      id: "control-library",
      type: "control",
      title: "Return to library launcher",
      kind: "library",
      active: true,
      position: new THREE.Vector3(0, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        renderLibraryLauncher(sceneApiRef);
        setStatus("Returned to the Braille library launcher.", "library-return");
      },
    },
    {
      id: "control-previous",
      type: "control",
      title: "Previous page tactile control",
      kind: "previous",
      active: state.currentPage > 0,
      position: new THREE.Vector3(-1.08, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        if (state.currentPage <= 0) {
          setStatus("Previous page tactile control is disabled.", "control-prev-disabled");
          return;
        }
        state.currentPage -= 1;
        state.selectedCellId = null;
        renderCurrentPage(sceneApiRef);
        setStatus("Moved to previous Braille page.", "page-prev");
      },
    },
    {
      id: "control-next",
      type: "control",
      title: "Next page tactile control",
      kind: "next",
      active: state.currentPage < getPageCount() - 1,
      position: new THREE.Vector3(1.08, 0.18, controlZ),
      radius: 0.24,
      action: () => {
        if (state.currentPage >= getPageCount() - 1) {
          setStatus("Next page tactile control is disabled.", "control-next-disabled");
          return;
        }
        state.currentPage += 1;
        state.selectedCellId = null;
        renderCurrentPage(sceneApiRef);
        setStatus("Moved to next Braille page.", "page-next");
      },
    },
    {
      id: "control-segment-previous",
      type: "control",
      title: "Previous document segment control",
      kind: "segment-previous",
      active: state.activeDocumentPayload?.previous_offset !== null,
      position: new THREE.Vector3(-0.9, 0.18, segmentZ),
      radius: 0.24,
      action: async () => {
        const offset = state.activeDocumentPayload?.previous_offset;
        if (offset === null || offset === undefined) {
          setStatus("Previous document segment tactile control is disabled.", "segment-prev-disabled");
          return;
        }
        await loadDocumentSegment(sceneApiRef, offset, { documentSlug: state.selectedLibrarySlug });
        setStatus("Loaded the previous document segment.", `segment-prev-${offset}`);
      },
    },
    {
      id: "control-segment-next",
      type: "control",
      title: "Next document segment control",
      kind: "segment-next",
      active: state.activeDocumentPayload?.next_offset !== null,
      position: new THREE.Vector3(0.9, 0.18, segmentZ),
      radius: 0.24,
      action: async () => {
        const offset = state.activeDocumentPayload?.next_offset;
        if (offset === null || offset === undefined) {
          setStatus("Next document segment tactile control is disabled.", "segment-next-disabled");
          return;
        }
        await loadDocumentSegment(sceneApiRef, offset, { documentSlug: state.selectedLibrarySlug });
        setStatus("Loaded the next document segment.", `segment-next-${offset}`);
      },
    },
  ];
}

let sceneApiRef = null;

function refreshInteractiveVisuals() {
  state.interactiveGroups.forEach((group, targetId) => {
    const target = state.targetById.get(targetId);
    const isHovered = targetId === state.hoveredTargetId;
    const isSelectedCell = target.type === "cell" && targetId === state.selectedCellId;
    const isSelectedDocument =
      target.type === "library-document" && target.document.slug === state.selectedLibrarySlug;

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

      if (target.type === "library-document") {
        if (node.userData.kind === "document-cover") {
          node.material.color.setHex(isHovered || isSelectedDocument ? 0x234165 : 0x1a2940);
        }
        if (node.userData.kind === "document-pages") {
          node.material.color.setHex(isHovered || isSelectedDocument ? 0xf8fafc : 0xe5e7eb);
        }
        if (node.userData.kind === "document-spine" || node.userData.kind === "document-badge") {
          node.material.emissive.setHex(isHovered || isSelectedDocument ? 0x1f6feb : 0x4a2d00);
        }
        return;
      }

      if (node.userData.kind === "control-base") {
        node.material.color.setHex(
          !target.active ? 0x1a1f28 : isHovered ? 0x1f3855 : 0x20324a,
        );
      }
      if (node.userData.kind === "control-ridge") {
        node.material.emissive.setHex(isHovered && target.active ? 0x1f6feb : 0x14263d);
      }
    });
  });
}

function focusSelectedCell(pageCells) {
  document.querySelectorAll(".braille-cell-button").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.cellId === state.selectedCellId);
  });

  const selected = pageCells.find((cell) => cell.cellId === state.selectedCellId);
  if (!selected) {
    refreshInteractiveVisuals();
    return;
  }

  const x = (selected.column - (state.columns - 1) / 2) * 0.34;
  const z = selected.localRow * 0.48 - ((state.rowsPerPage - 1) * 0.24) - 0.18;
  state.pointerController?.setPosition(new THREE.Vector3(x, 0.22, z));
  updateSelectedCell(selected);
  refreshInteractiveVisuals();
}

function focusSelectedLibraryDocument(pageSlice) {
  document.querySelectorAll(".braille-library-card").forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.documentSlug === state.selectedLibrarySlug);
  });

  const selectedDocument = pageSlice.documents.find((item) => item.slug === state.selectedLibrarySlug);
  if (!selectedDocument) {
    refreshInteractiveVisuals();
    return;
  }

  const target = state.targetById.get(`library-document-${selectedDocument.slug}`);
  if (target) {
    state.pointerController?.setPosition(target.position.clone());
    state.hoveredTargetId = target.id;
  }
  refreshInteractiveVisuals();
}

function idlePointerMessage() {
  return state.sceneMode === "library-launcher"
    ? "Pointer moving across the Braille library launcher."
    : "Pointer moving over the reading surface.";
}

function updatePointerTarget(sceneApi, position) {
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
    setStatus(idlePointerMessage(), `pointer-${state.sceneMode}`);
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

  if (nearestTarget.type === "library-document") {
    setStatus(
      `${nearestTarget.document.title}. Activate to load the tactile reading session.`,
      nearestTarget.id,
    );
    return;
  }

  setStatus(nearestTarget.title, nearestTarget.id);
}

function activatePointerTarget(sceneApi) {
  const target = state.targetById.get(state.hoveredTargetId);
  if (!target) {
    setStatus("No tactile target is currently under the pointer.", "no-target");
    return;
  }

  sceneApi.setPointerState("active");
  window.setTimeout(() => {
    updatePointerTarget(sceneApi, state.pointerController.position);
  }, 180);

  if (target.type === "control" || target.type === "library-document") {
    Promise.resolve(target.action?.()).catch((error) => {
      setStatus(error.message, `activate-error-${target.id}`);
    });
    return;
  }

  setStatus(
    `Selected Braille cell ${target.cell.row + 1}:${target.cell.column + 1}.`,
    `activate-${target.id}`,
  );
}

function createLibraryWorld(sceneApi, pageSlice) {
  sceneApi.clearWorld();
  state.interactiveGroups.clear();
  state.targetById.clear();

  const width = 5.8;
  const depth = 4.0;
  sceneApi.setBoundarySize(new THREE.Vector3(width + 0.7, 1.0, depth + 0.55));
  sceneApi.applySceneView([4.1, 2.9, 4.9], [0, 0.2, 0.2], {
    preserveUserView: true,
  });

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.12, depth),
    new THREE.MeshStandardMaterial({ color: 0x16213a, roughness: 0.88, metalness: 0.05 }),
  );
  base.position.y = 0.06;
  sceneApi.world.add(base);

  const frontLip = buildGuideRail(width - 0.2, 0.05, 0.08, 0x111827);
  frontLip.position.set(0, 0.085, depth / 2 - 0.14);
  sceneApi.world.add(frontLip);

  const backRail = buildGuideRail(width - 0.2, 0.05, 0.08, 0x111827);
  backRail.position.set(0, 0.085, -depth / 2 + 0.14);
  sceneApi.world.add(backRail);

  const titleBridge = buildPageBridge(`Library ${pageSlice.page + 1} / ${pageSlice.pageCount}`, depth);
  sceneApi.world.add(titleBridge);

  const positions = [
    new THREE.Vector3(-1.55, 0, -0.08),
    new THREE.Vector3(0, 0, -0.08),
    new THREE.Vector3(1.55, 0, -0.08),
  ];
  pageSlice.documents.forEach((document, index) => {
    const { group, target } = createLibraryDocumentGroup(document, positions[index]);
    state.interactiveGroups.set(target.id, group);
    state.targetById.set(target.id, target);
    sceneApi.world.add(group);
  });

  createLibraryControls(pageSlice).forEach((control) => {
    const controlGroup = buildTactileControlMesh(control.kind, control.active);
    controlGroup.position.copy(control.position.clone().setY(0.12));
    state.interactiveGroups.set(control.id, controlGroup);
    state.targetById.set(control.id, control);
    sceneApi.world.add(controlGroup);
  });

  const minBounds = new THREE.Vector3(-width / 2 + 0.15, 0.14, -depth / 2 + 0.22);
  const maxBounds = new THREE.Vector3(width / 2 - 0.15, 0.34, depth / 2 - 0.12);
  state.pointerController?.setBounds(minBounds, maxBounds);
}

function createBrailleWorld(sceneApi, pageCells) {
  sceneApi.clearWorld();
  state.interactiveGroups.clear();
  state.targetById.clear();

  const boardWidth = Math.max(2.4, state.columns * 0.34 + 0.8);
  const boardDepth = Math.max(1.9, state.rowsPerPage * 0.48 + 1.15);
  sceneApi.setBoundarySize(new THREE.Vector3(boardWidth + 0.7, 0.95, boardDepth + 0.45));
  sceneApi.applySceneView([2.4, 2.2, 3.2], [0, 0.18, 0.08], {
    preserveUserView: true,
  });

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

  const sceneControls = createReadingControls(boardDepth);
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

function renderLibraryLauncher(sceneApi) {
  const pageSlice = libraryPageSlice(state.libraryPage);
  state.libraryPage = pageSlice.page;
  const fallbackDocument = pageSlice.documents[0] ?? state.libraryDocuments[0] ?? null;
  if (
    !selectedLibraryDocument()
    || !pageSlice.documents.some((document) => document.slug === state.selectedLibrarySlug)
  ) {
    setSelectedLibraryDocument((fallbackDocument ?? {}).slug);
  }

  setSceneMode("library-launcher");
  updateFallbackPageButtons();
  updateLibrarySummary(pageSlice);
  createLibraryWorld(sceneApi, pageSlice);
  renderLibraryBoard(pageSlice);

  const focusTargetId = state.targetById.has(`library-document-${state.selectedLibrarySlug}`)
    ? `library-document-${state.selectedLibrarySlug}`
    : "launcher-hub";
  state.hoveredTargetId = focusTargetId;
  if (focusTargetId.startsWith("library-document-")) {
    focusSelectedLibraryDocument(pageSlice);
  } else {
    const target = state.targetById.get(focusTargetId);
    state.pointerController?.setPosition(target?.position?.clone() ?? new THREE.Vector3(0, 0.22, 0.8));
    refreshInteractiveVisuals();
  }
  updatePointerTarget(sceneApi, state.pointerController.position);
}

function renderCurrentPage(sceneApi) {
  setSceneMode("reading");
  const pageCells = getPageCells();
  updateSummary(pageCells);
  createBrailleWorld(sceneApi, pageCells);
  render2DBoard(pageCells);
  updateFallbackPageButtons();

  if (!pageCells.some((cell) => cell.cellId === state.selectedCellId)) {
    state.selectedCellId = pageCells[0]?.cellId ?? null;
  }
  state.hoveredTargetId = state.selectedCellId;
  if (state.selectedCellId) {
    focusSelectedCell(pageCells);
  } else {
    refreshInteractiveVisuals();
  }

  state.pointerController?.setPosition(
    state.selectedCellId && state.targetById.has(state.selectedCellId)
      ? state.targetById.get(state.selectedCellId).position.clone().setY(0.22)
      : new THREE.Vector3(0, 0.22, 0.2),
  );
  updatePointerTarget(sceneApi, state.pointerController.position);
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

async function loadDocumentSegment(sceneApi, offset = 0, options = {}) {
  const document = documentBySlug(options.documentSlug ?? currentDocument()?.slug ?? state.selectedLibrarySlug);
  if (!document) {
    throw new Error("No bundled document is available.");
  }

  setSelectedLibraryDocument(document.slug);
  state.libraryPage = libraryPageForSlug(document.slug);
  const maxChars = Number(byId("document-segment-size").value) || document.recommended_excerpt_chars;
  const url = `/api/library/documents/${encodeURIComponent(document.slug)}?offset=${offset}&max_chars=${maxChars}`;
  const payload = await fetchJson(url);
  state.activeDocumentPayload = payload;
  byId("preview-text").value = payload.text;
  updateDocumentPanel(document, payload);
  syncCompanionAudio(document);
  await loadPreview(sceneApi);
  setStatus(`Loaded ${document.title} segment into the tactile buffer.`, `library-${document.slug}-${payload.offset}`);
}

function moveSelection(deltaRow, deltaColumn) {
  if (state.sceneMode !== "reading") {
    return;
  }
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
    focusSelectedCell(pageCells);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  bootWorkspace(
    {
      title: "Braille Reader startup failed",
      stageSelector: "#braille-canvas",
      runtimePillId: "reader-runtime-pill",
      runtimePillText: "Runtime error",
      pageStatusId: "reader-page-status",
      pageStatusText: "Boot failed",
      stageStatusId: "reader-status-bar",
      summaryIds: [
        "selected-source",
        "selected-normalized",
        "selected-mask",
        "selected-position",
        "summary-unicode",
      ],
    },
    async () => {
      const sceneApi = createWorkspaceScene(byId("braille-canvas"), {
        cameraPosition: [2.4, 2.2, 3.2],
        target: [0, 0.18, 0.08],
        boundarySize: new THREE.Vector3(3.6, 0.95, 3.2),
        debugKey: "braille-reader",
      });
      sceneApiRef = sceneApi;

      state.pointerController = attachPointerEmulation(sceneApi, {
        initialPosition: new THREE.Vector3(0, 0.22, 0.2),
        boundsMin: new THREE.Vector3(-1.6, 0.14, -1.2),
        boundsMax: new THREE.Vector3(1.6, 0.34, 1.4),
        speed: 1.4,
        onMove: (position) => updatePointerTarget(sceneApi, position),
        onActivate: () => activatePointerTarget(sceneApi),
      });

      const [documentPayload, audioPayload] = await Promise.all([
        fetchJson(documentsUrl),
        fetchJson(audioUrl),
      ]);

      state.libraryDocuments = documentPayload.documents;
      state.libraryAudio = audioPayload.audio;

      populateSelect(byId("library-document-select"), state.libraryDocuments, "slug", "title");
      populateSelect(byId("library-audio-select"), state.libraryAudio, "slug", "title");
      if (state.libraryDocuments[0]) {
        setSelectedLibraryDocument(state.libraryDocuments[0].slug);
        state.libraryPage = 0;
      }

      byId("library-audio-select").addEventListener("change", () => {
        updateAudioPanel();
      });

      byId("load-library-document").addEventListener("click", () => {
        loadDocumentSegment(sceneApi).catch((error) => setStatus(error.message, "document-load-error"));
      });

      byId("load-previous-segment").addEventListener("click", () => {
        const offset = state.activeDocumentPayload?.previous_offset;
        if (offset === null || offset === undefined) {
          setStatus("The current document is already at the first segment.", "document-prev-disabled");
          return;
        }
        loadDocumentSegment(sceneApi, offset).catch((error) =>
          setStatus(error.message, "document-prev-error"),
        );
      });

      byId("load-next-segment").addEventListener("click", () => {
        const offset = state.activeDocumentPayload?.next_offset;
        if (offset === null || offset === undefined) {
          setStatus("The current document is already at the last bundled segment.", "document-next-disabled");
          return;
        }
        loadDocumentSegment(sceneApi, offset).catch((error) =>
          setStatus(error.message, "document-next-error"),
        );
      });

      byId("library-document-select").addEventListener("change", () => {
        const document = setSelectedLibraryDocument(byId("library-document-select").value, { syncAudio: false });
        if (!document) {
          return;
        }
        state.libraryPage = libraryPageForSlug(document.slug);
        if (state.sceneMode === "library-launcher") {
          renderLibraryLauncher(sceneApi);
          setStatus(`Selected ${document.title} in the Braille library launcher.`, `select-${document.slug}`);
        }
      });

      byId("generate-preview").addEventListener("click", () => {
        loadPreview(sceneApi).catch((error) => setStatus(error.message, "preview-error"));
      });

      byId("rows-per-page").addEventListener("change", () => {
        state.rowsPerPage = Number(byId("rows-per-page").value) || 4;
        if (state.sceneMode === "reading" && state.cells.length > 0) {
          state.currentPage = 0;
          renderCurrentPage(sceneApi);
        }
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
        if (state.sceneMode !== "reading") {
          setStatus("Fallback page controls are disabled while the library launcher is active.", "fallback-prev-disabled");
          return;
        }
        state.currentPage = Math.max(0, state.currentPage - 1);
        state.selectedCellId = null;
        renderCurrentPage(sceneApi);
        setStatus("Moved to previous page with fallback web control.", "fallback-prev");
      });

      byId("next-page").addEventListener("click", () => {
        if (state.sceneMode !== "reading") {
          setStatus("Fallback page controls are disabled while the library launcher is active.", "fallback-next-disabled");
          return;
        }
        state.currentPage = Math.min(getPageCount() - 1, state.currentPage + 1);
        state.selectedCellId = null;
        renderCurrentPage(sceneApi);
        setStatus("Moved to next page with fallback web control.", "fallback-next");
      });

      document.addEventListener("keydown", (event) => {
        if (
          event.target.tagName === "TEXTAREA" ||
          event.target.tagName === "INPUT" ||
          event.target.tagName === "SELECT"
        ) {
          return;
        }
        if (event.key === "ArrowLeft") moveSelection(0, -1);
        if (event.key === "ArrowRight") moveSelection(0, 1);
        if (event.key === "ArrowUp") moveSelection(-1, 0);
        if (event.key === "ArrowDown") moveSelection(1, 0);
      });

      window.__feelitBrailleDebug = {
        getSceneMode: () => state.sceneMode,
        getSelectedLibrarySlug: () => state.selectedLibrarySlug,
        getLibraryPage: () => state.libraryPage,
        targetIds: () => Array.from(state.targetById.keys()),
        targets: () =>
          Array.from(state.targetById.values()).map((target) => ({
            id: target.id,
            title: target.title,
            type: target.type,
            position: target.position?.toArray?.() ?? null,
            radius: target.radius ?? 0,
            active: target.active ?? true,
          })),
        pointerBounds: () => state.pointerController?.getBounds?.() ?? null,
        activateTarget: async (targetId) => {
          const target = state.targetById.get(targetId);
          if (!target) {
            return false;
          }
          state.hoveredTargetId = targetId;
          refreshInteractiveVisuals();
          await Promise.resolve(target.action?.());
          return true;
        },
      };

      applyScale("standard");
      setSceneMode("library-launcher");
      updateAudioPanel();
      updateFallbackPageButtons();
      renderLibraryLauncher(sceneApi);
      setStatus("Braille library launcher ready. Select a document in the 3D world to begin reading.", "launcher-ready");
    },
  );
});
