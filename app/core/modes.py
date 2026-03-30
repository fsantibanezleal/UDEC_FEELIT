"""Application mode catalog."""

from __future__ import annotations


def build_mode_catalog() -> list[dict[str, object]]:
    """Return the current public mode catalog."""
    return [
        {
            "slug": "object-explorer",
            "route": "/object-explorer",
            "title": "3D Object Explorer",
            "status": "staged",
            "summary": (
                "Dedicated workspace for staging 3D objects, choosing tactile material "
                "presets, and preparing bounded exploration sessions."
            ),
        },
        {
            "slug": "braille-reader",
            "route": "/braille-reader",
            "title": "Braille Reader",
            "status": "active",
            "summary": (
                "Operational reading workspace that turns text into a tactile Braille layout "
                "inside a bounded virtual surface."
            ),
        },
        {
            "slug": "haptic-desktop",
            "route": "/haptic-desktop",
            "title": "Haptic Desktop",
            "status": "prototype",
            "summary": (
                "Mode-oriented workspace for focusable action objects, audio labels, and "
                "future haptic interaction with digital content."
            ),
        },
        {
            "slug": "haptic-workspace-manager",
            "route": "/haptic-workspace-manager",
            "title": "Haptic Workspace Manager",
            "status": "active",
            "summary": (
                "Management workspace for creating, registering, and inspecting structured "
                "Haptic Desktop workspaces rooted in external user folders."
            ),
        },
        {
            "slug": "haptic-configuration",
            "route": "/haptic-configuration",
            "title": "Haptic Configuration",
            "status": "active",
            "summary": (
                "Runtime-facing workspace for selecting the active haptic backend, "
                "inspecting dependency readiness, and reviewing the contact-model baseline."
            ),
        },
    ]
