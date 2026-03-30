"""Toolchain discovery helpers for the native haptic bridge workflow."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field


class ToolchainComponentStatus(BaseModel):
    """Describe one build-tool component relevant to the native bridge path."""

    slug: str
    title: str
    status: str
    detected_path: str | None = None
    detected_version: str | None = None
    evidence: list[str] = Field(default_factory=list)
    install_hint: str = ""


def _existing_path(raw_path: str | Path | None) -> str | None:
    """Return one normalized path string when the target exists."""
    if not raw_path:
        return None
    candidate = Path(raw_path).expanduser()
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    return str(resolved) if resolved.exists() else None


def _version_from_command(executable_path: str, version_args: list[str]) -> str | None:
    """Return the first non-empty line reported by one tool version command."""
    try:
        completed = subprocess.run(
            [executable_path, *version_args],
            capture_output=True,
            text=True,
            timeout=6,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    for stream in (completed.stdout, completed.stderr):
        for line in stream.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    return None


def _vs_2022_roots() -> list[Path]:
    """Return the common Visual Studio 2022 edition roots that may exist."""
    editions = ["Community", "Professional", "Enterprise", "BuildTools"]
    return [
        Path("C:/Program Files/Microsoft Visual Studio/2022") / edition
        for edition in editions
    ]


def _candidate_paths(
    *,
    override_env: str,
    command_name: str,
    extra_candidates: Iterable[str | Path],
) -> list[str]:
    """Return ordered candidate executable paths for one tool."""
    candidates: list[str] = []

    override = _existing_path(os.getenv(override_env, "").strip())
    if override:
        candidates.append(override)

    which_path = shutil.which(command_name)
    if which_path:
        resolved = _existing_path(which_path)
        if resolved and resolved not in candidates:
            candidates.append(resolved)

    for candidate in extra_candidates:
        resolved = _existing_path(candidate)
        if resolved and resolved not in candidates:
            candidates.append(resolved)

    return candidates


def _discover_tool(
    *,
    slug: str,
    title: str,
    override_env: str,
    command_name: str,
    version_args: list[str],
    extra_candidates: Iterable[str | Path],
    install_hint: str,
) -> ToolchainComponentStatus:
    """Discover one native build-tool executable."""
    evidence: list[str] = []
    candidates = _candidate_paths(
        override_env=override_env,
        command_name=command_name,
        extra_candidates=extra_candidates,
    )
    if not candidates:
        evidence.append(f"No executable candidates found for {command_name}.")
        return ToolchainComponentStatus(
            slug=slug,
            title=title,
            status="missing",
            evidence=evidence,
            install_hint=install_hint,
        )

    executable_path = candidates[0]
    evidence.append(f"Using executable candidate: {executable_path}")
    version = _version_from_command(executable_path, version_args)
    if version:
        evidence.append(f"Version probe succeeded: {version}")
        return ToolchainComponentStatus(
            slug=slug,
            title=title,
            status="ready",
            detected_path=executable_path,
            detected_version=version,
            evidence=evidence,
            install_hint=install_hint,
        )

    evidence.append("Executable exists but version probe failed.")
    return ToolchainComponentStatus(
        slug=slug,
        title=title,
        status="detected-without-version",
        detected_path=executable_path,
        evidence=evidence,
        install_hint=install_hint,
    )


def _discover_visual_studio() -> ToolchainComponentStatus:
    """Discover the current Visual Studio installation used for native Windows builds."""
    evidence: list[str] = []
    override = _existing_path(os.getenv("FEELIT_VS_ROOT", "").strip())
    if override:
        evidence.append(f"Using FEELIT_VS_ROOT override: {override}")
        return ToolchainComponentStatus(
            slug="visual-studio",
            title="Visual Studio 2022",
            status="ready",
            detected_path=override,
            evidence=evidence,
            install_hint="Optional when the bridge is built with clang++, but useful for MSBuild flows.",
        )

    for root in _vs_2022_roots():
        resolved = _existing_path(root)
        if resolved:
            evidence.append(f"Detected Visual Studio root: {resolved}")
            return ToolchainComponentStatus(
                slug="visual-studio",
                title="Visual Studio 2022",
                status="ready",
                detected_path=resolved,
                evidence=evidence,
                install_hint="Optional when the bridge is built with clang++, but useful for MSBuild flows.",
            )

    evidence.append("No Visual Studio 2022 installation root was detected.")
    return ToolchainComponentStatus(
        slug="visual-studio",
        title="Visual Studio 2022",
        status="missing",
        evidence=evidence,
        install_hint=(
            "Install Visual Studio 2022 or Build Tools if the bridge should also support "
            "MSBuild-driven Windows builds."
        ),
    )


def _discover_msvc_toolset() -> ToolchainComponentStatus:
    """Discover the installed MSVC toolset root when available."""
    evidence: list[str] = []
    override = _existing_path(os.getenv("FEELIT_MSVC_ROOT", "").strip())
    if override:
        evidence.append(f"Using FEELIT_MSVC_ROOT override: {override}")
        return ToolchainComponentStatus(
            slug="msvc-toolset",
            title="MSVC Toolset",
            status="ready",
            detected_path=override,
            detected_version=Path(override).name,
            evidence=evidence,
            install_hint="Optional when the bridge is built with clang++, but useful for ABI parity on Windows.",
        )

    for root in _vs_2022_roots():
        msvc_parent = root / "VC" / "Tools" / "MSVC"
        if not msvc_parent.exists():
            continue
        versions = sorted(
            (entry for entry in msvc_parent.iterdir() if entry.is_dir()),
            key=lambda entry: entry.name,
            reverse=True,
        )
        if versions:
            detected = versions[0]
            evidence.append(f"Detected MSVC toolset root: {detected}")
            return ToolchainComponentStatus(
                slug="msvc-toolset",
                title="MSVC Toolset",
                status="ready",
                detected_path=str(detected),
                detected_version=detected.name,
                evidence=evidence,
                install_hint="Optional when the bridge is built with clang++, but useful for ABI parity on Windows.",
            )

    evidence.append("No MSVC toolset root was detected.")
    return ToolchainComponentStatus(
        slug="msvc-toolset",
        title="MSVC Toolset",
        status="missing",
        evidence=evidence,
        install_hint=(
            "Install Visual Studio 2022 or Build Tools if the bridge should target the MSVC toolchain."
        ),
    )


def _discover_resource_compiler() -> ToolchainComponentStatus:
    """Discover the Windows resource compiler used by CMake bridge builds."""
    evidence: list[str] = []
    override = _existing_path(os.getenv("FEELIT_RC_EXE", "").strip())
    if override:
        evidence.append(f"Using FEELIT_RC_EXE override: {override}")
        version = _version_from_command(override, ["--version"])
        if version and "Exactly one input file" in version:
            version = None
        return ToolchainComponentStatus(
            slug="resource-compiler",
            title="Windows Resource Compiler",
            status="ready" if version else "detected-without-version",
            detected_path=override,
            detected_version=version,
            evidence=evidence,
            install_hint="Required by CMake on Windows when compiling the native FeelIT bridge scaffold.",
        )

    candidates: list[Path] = [Path("C:/Program Files/LLVM/bin/llvm-rc.exe")]
    windows_kits = Path("C:/Program Files (x86)/Windows Kits/10/bin")
    if windows_kits.exists():
        versions = sorted(
            (entry for entry in windows_kits.iterdir() if entry.is_dir()),
            key=lambda entry: entry.name,
            reverse=True,
        )
        for version_dir in versions:
            candidates.append(version_dir / "x64" / "rc.exe")

    for candidate in candidates:
        resolved = _existing_path(candidate)
        if not resolved:
            continue
        evidence.append(f"Detected resource compiler: {resolved}")
        version = _version_from_command(resolved, ["--version"])
        if version and "Exactly one input file" in version:
            version = None
        return ToolchainComponentStatus(
            slug="resource-compiler",
            title="Windows Resource Compiler",
            status="ready" if version or resolved.lower().endswith("rc.exe") else "detected-without-version",
            detected_path=resolved,
            detected_version=version,
            evidence=evidence,
            install_hint="Required by CMake on Windows when compiling the native FeelIT bridge scaffold.",
        )

    evidence.append("No Windows resource compiler was detected.")
    return ToolchainComponentStatus(
        slug="resource-compiler",
        title="Windows Resource Compiler",
        status="missing",
        evidence=evidence,
        install_hint="Install LLVM or the Windows SDK resource compiler to satisfy CMake on Windows.",
    )


def build_native_toolchain_statuses() -> list[ToolchainComponentStatus]:
    """Return the current toolchain state for the FeelIT native bridge path."""
    cmake_candidates: list[str | Path] = [
        Path("C:/Program Files/CMake/bin/cmake.exe"),
        *[
            root / "Common7" / "IDE" / "CommonExtensions" / "Microsoft" / "CMake" / "CMake" / "bin" / "cmake.exe"
            for root in _vs_2022_roots()
        ],
    ]
    ninja_candidates: list[str | Path] = [
        Path(os.getenv("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ninja.exe",
        *[
            root / "Common7" / "IDE" / "CommonExtensions" / "Microsoft" / "CMake" / "Ninja" / "ninja.exe"
            for root in _vs_2022_roots()
        ],
    ]
    clang_candidates: list[str | Path] = [
        Path("C:/Program Files/LLVM/bin/clang++.exe"),
    ]
    msbuild_candidates: list[str | Path] = [
        *[
            root / "MSBuild" / "Current" / "Bin" / "MSBuild.exe"
            for root in _vs_2022_roots()
        ],
    ]

    return [
        _discover_tool(
            slug="cmake",
            title="CMake",
            override_env="FEELIT_CMAKE_EXE",
            command_name="cmake",
            version_args=["--version"],
            extra_candidates=cmake_candidates,
            install_hint="Install CMake to configure the native FeelIT bridge build tree.",
        ),
        _discover_tool(
            slug="ninja",
            title="Ninja",
            override_env="FEELIT_NINJA_EXE",
            command_name="ninja",
            version_args=["--version"],
            extra_candidates=ninja_candidates,
            install_hint="Install Ninja to use the default fast generator for FeelIT native bridge builds.",
        ),
        _discover_tool(
            slug="clang++",
            title="LLVM clang++",
            override_env="FEELIT_CLANGXX_EXE",
            command_name="clang++",
            version_args=["--version"],
            extra_candidates=clang_candidates,
            install_hint="Install LLVM to compile the native FeelIT bridge scaffold without depending on PATH state.",
        ),
        _discover_tool(
            slug="msbuild",
            title="MSBuild",
            override_env="FEELIT_MSBUILD_EXE",
            command_name="msbuild",
            version_args=["-version", "-nologo"],
            extra_candidates=msbuild_candidates,
            install_hint="Install Visual Studio Build Tools if FeelIT should support MSBuild-based native bridge builds.",
        ),
        _discover_visual_studio(),
        _discover_msvc_toolset(),
        _discover_resource_compiler(),
    ]
