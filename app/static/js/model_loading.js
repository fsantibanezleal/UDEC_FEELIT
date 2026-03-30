import * as THREE from "../vendor/three/three.module.js";
import { GLTFLoader } from "../vendor/three/GLTFLoader.js";
import { OBJLoader } from "../vendor/three/OBJLoader.js";
import { STLLoader } from "../vendor/three/STLLoader.js";

export const SUPPORTED_MODEL_FORMATS = Object.freeze(["obj", "stl", "gltf", "glb"]);
export const SUPPORTED_MODEL_EXTENSIONS = Object.freeze(
  SUPPORTED_MODEL_FORMATS.map((format) => `.${format}`),
);

const FORMAT_LABELS = Object.freeze({
  obj: "OBJ",
  stl: "STL",
  gltf: "glTF",
  glb: "GLB",
});

const objLoader = new OBJLoader();
const stlLoader = new STLLoader();
function normalizedModelFormat(formatOrFilename) {
  if (!formatOrFilename) {
    return null;
  }
  const token = String(formatOrFilename).trim().toLowerCase();
  if (!token) {
    return null;
  }
  if (SUPPORTED_MODEL_FORMATS.includes(token)) {
    return token;
  }
  const dotIndex = token.lastIndexOf(".");
  if (dotIndex < 0) {
    return null;
  }
  const extension = token.slice(dotIndex + 1);
  return SUPPORTED_MODEL_FORMATS.includes(extension) ? extension : null;
}

function ensureSupportedModelFormat(formatOrFilename) {
  const format = normalizedModelFormat(formatOrFilename);
  if (!format) {
    throw new Error(
      `Unsupported 3D model format. Expected one of ${SUPPORTED_MODEL_EXTENSIONS.join(", ")}.`,
    );
  }
  return format;
}

function modelResourceBase(url) {
  try {
    const resolved = new URL(url, window.location.origin);
    if (resolved.search) {
      return "";
    }
    resolved.hash = "";
    resolved.pathname = resolved.pathname.slice(0, resolved.pathname.lastIndexOf("/") + 1);
    return resolved.toString();
  } catch {
    return "";
  }
}

function wrapStlGeometry(geometry) {
  geometry.computeVertexNormals();
  return new THREE.Mesh(
    geometry,
    new THREE.MeshStandardMaterial({
      color: 0x7b94b3,
      roughness: 0.58,
      metalness: 0.08,
      emissive: 0x0d1622,
    }),
  );
}

async function parseModelPayload(rawPayload, format, resourcePath = "") {
  if (format === "obj") {
    const textPayload =
      typeof rawPayload === "string" ? rawPayload : new TextDecoder().decode(rawPayload);
    return objLoader.parse(textPayload);
  }
  if (format === "stl") {
    return wrapStlGeometry(stlLoader.parse(rawPayload));
  }
  if (format === "gltf" || format === "glb") {
    const gltfLoader = new GLTFLoader();
    const gltf = await gltfLoader.parseAsync(rawPayload, resourcePath);
    return gltf.scene ?? gltf.scenes?.[0] ?? new THREE.Group();
  }
  throw new Error(`Unsupported 3D model format: ${format}`);
}

function resourceNameCandidates(resourceName) {
  const raw = String(resourceName ?? "").trim();
  if (!raw) {
    return [];
  }
  const normalized = raw.replaceAll("\\", "/");
  let decoded = normalized;
  try {
    decoded = decodeURIComponent(normalized);
  } catch {
    decoded = normalized;
  }
  const basename = decoded.slice(decoded.lastIndexOf("/") + 1);
  return [...new Set([normalized, decoded, basename])];
}

function resolveBundleResource(bundleFiles, resourceName) {
  const bundleMap = new Map();
  bundleFiles.forEach((file) => {
    resourceNameCandidates(file.name).forEach((candidate) => {
      if (!bundleMap.has(candidate)) {
        bundleMap.set(candidate, file);
      }
    });
  });

  for (const candidate of resourceNameCandidates(resourceName)) {
    if (bundleMap.has(candidate)) {
      return bundleMap.get(candidate);
    }
  }
  return null;
}

async function parseBundleModelPayload(rawPayload, format, bundleFiles) {
  if (format !== "gltf" && format !== "glb") {
    return parseModelPayload(rawPayload, format, "");
  }

  const loadingManager = new THREE.LoadingManager();
  const objectUrls = new Map();
  loadingManager.setURLModifier((url) => {
    if (!url || url.startsWith("data:") || url.startsWith("blob:")) {
      return url;
    }
    const matchedFile = resolveBundleResource(bundleFiles, url);
    if (!matchedFile) {
      return url;
    }
    if (!objectUrls.has(matchedFile.name)) {
      objectUrls.set(matchedFile.name, URL.createObjectURL(matchedFile));
    }
    return objectUrls.get(matchedFile.name);
  });

  try {
    const gltfLoader = new GLTFLoader(loadingManager);
    const gltf = await gltfLoader.parseAsync(rawPayload, "");
    return gltf.scene ?? gltf.scenes?.[0] ?? new THREE.Group();
  } finally {
    objectUrls.forEach((value) => URL.revokeObjectURL(value));
  }
}

export function modelFormatLabel(formatOrFilename) {
  const format = ensureSupportedModelFormat(formatOrFilename);
  return FORMAT_LABELS[format];
}

export function modelFileAcceptString() {
  return SUPPORTED_MODEL_EXTENSIONS.join(",");
}

export function modelFormatFromFilename(filename) {
  return ensureSupportedModelFormat(filename);
}

export async function loadModelFromUrl(url, formatOrFilename) {
  const format = ensureSupportedModelFormat(formatOrFilename ?? url);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed: ${url}`);
  }
  const rawPayload = format === "obj" ? await response.text() : await response.arrayBuffer();
  const modelRoot = await parseModelPayload(rawPayload, format, modelResourceBase(url));
  return {
    format,
    formatLabel: modelFormatLabel(format),
    modelRoot,
  };
}

export async function loadLocalModelFile(file) {
  const format = ensureSupportedModelFormat(file.name);
  const rawPayload = format === "obj" ? await file.text() : await file.arrayBuffer();
  const modelRoot = await parseModelPayload(rawPayload, format, "");
  return {
    format,
    formatLabel: modelFormatLabel(format),
    modelRoot,
  };
}

export async function loadLocalModelBundle(mainFile, bundleFiles = [mainFile]) {
  const format = ensureSupportedModelFormat(mainFile.name);
  const rawPayload = format === "obj" ? await mainFile.text() : await mainFile.arrayBuffer();
  const modelRoot = await parseBundleModelPayload(rawPayload, format, bundleFiles);
  return {
    format,
    formatLabel: modelFormatLabel(format),
    modelRoot,
  };
}
