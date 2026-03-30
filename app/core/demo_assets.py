"""Bundled multi-format 3D demo assets for FeelIT."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DemoModel:
    """Describe one bundled 3D asset for interactive exploration demos."""

    slug: str
    title: str
    category: str
    filename: str
    file_url: str
    file_format: str
    default_material: str
    scale_hint: float
    description: str
    source_name: str
    source_url: str


FORMAT_LABELS = {
    "obj": "OBJ",
    "stl": "STL",
    "gltf": "glTF",
    "glb": "GLB",
}


DEMO_MODELS: tuple[DemoModel, ...] = (
    DemoModel(
        slug="walt_head",
        title="Walt Head",
        category="sculpture",
        filename="WaltHead.obj",
        file_url="/static/assets/models/demo/WaltHead.obj",
        file_format="obj",
        default_material="carved_stone",
        scale_hint=1.25,
        description="Large scanned bust with pronounced facial relief, useful for contour exploration.",
        source_name="three.js examples",
        source_url="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/walt/WaltHead.obj",
    ),
    DemoModel(
        slug="tree",
        title="Tree",
        category="organic",
        filename="tree.obj",
        file_url="/static/assets/models/demo/tree.obj",
        file_format="obj",
        default_material="unfinished_wood",
        scale_hint=0.95,
        description="Organic branching geometry suitable for bark and contour interpretation.",
        source_name="three.js examples",
        source_url="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/tree.obj",
    ),
    DemoModel(
        slug="male_figure",
        title="Male Figure",
        category="human_form",
        filename="male02.obj",
        file_url="/static/assets/models/demo/male02.obj",
        file_format="obj",
        default_material="textured_polymer",
        scale_hint=0.8,
        description="Human body reference model for overall shape, posture, and proportion reading.",
        source_name="three.js examples",
        source_url="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/male02/male02.obj",
    ),
    DemoModel(
        slug="female_figure",
        title="Female Figure",
        category="human_form",
        filename="female02.obj",
        file_url="/static/assets/models/demo/female02.obj",
        file_format="obj",
        default_material="textured_polymer",
        scale_hint=0.82,
        description="Human body reference model with different proportions for guided exploration trials.",
        source_name="three.js examples",
        source_url="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/female02/female02.obj",
    ),
    DemoModel(
        slug="cerberus",
        title="Cerberus",
        category="creature",
        filename="Cerberus.obj",
        file_url="/static/assets/models/demo/Cerberus.obj",
        file_format="obj",
        default_material="polished_metal",
        scale_hint=0.9,
        description="Dense creature mesh with horns, paws, and silhouette changes for complex exploration.",
        source_name="three.js examples",
        source_url="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/cerberus/Cerberus.obj",
    ),
    DemoModel(
        slug="ninja_head",
        title="Ninja Head",
        category="sculpture",
        filename="ninjaHead_Low.obj",
        file_url="/static/assets/models/demo/ninjaHead_Low.obj",
        file_format="obj",
        default_material="carved_stone",
        scale_hint=1.05,
        description="Compact head scan for facial contour reading without the weight of a full-body mesh.",
        source_name="three.js examples",
        source_url="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/models/obj/ninja/ninjaHead_Low.obj",
    ),
    DemoModel(
        slug="closed_book",
        title="Closed Book",
        category="everyday_object",
        filename="closed_book.obj",
        file_url="/static/assets/models/demo/closed_book.obj",
        file_format="obj",
        default_material="coated_paper",
        scale_hint=0.96,
        description="Internal lightweight book form for exploring planar covers, page block thickness, and edge transitions.",
        source_name="FeelIT internal lightweight geometry",
        source_url="internal://feelit/closed_book",
    ),
    DemoModel(
        slug="open_book",
        title="Open Book",
        category="educational_object",
        filename="open_book.obj",
        file_url="/static/assets/models/demo/open_book.obj",
        file_format="obj",
        default_material="coated_paper",
        scale_hint=1.0,
        description="Open reading posture model with sloped page surfaces and a tactile spine region.",
        source_name="FeelIT internal lightweight geometry",
        source_url="internal://feelit/open_book",
    ),
    DemoModel(
        slug="terrain_peak",
        title="Terrain Peak",
        category="landscape",
        filename="terrain_peak.obj",
        file_url="/static/assets/models/demo/terrain_peak.obj",
        file_format="obj",
        default_material="carved_stone",
        scale_hint=1.1,
        description="Stylized mountain relief for topographic exploration and slope transition testing.",
        source_name="FeelIT internal lightweight geometry",
        source_url="internal://feelit/terrain_peak",
    ),
    DemoModel(
        slug="vase_lowpoly",
        title="Low-Poly Vase",
        category="household_object",
        filename="vase_lowpoly.obj",
        file_url="/static/assets/models/demo/vase_lowpoly.obj",
        file_format="obj",
        default_material="glazed_ceramic",
        scale_hint=0.92,
        description="Faceted vessel profile useful for neck, shoulder, and base transition studies.",
        source_name="FeelIT internal lightweight geometry",
        source_url="internal://feelit/vase_lowpoly",
    ),
    DemoModel(
        slug="tactile_bridge_stl",
        title="Tactile Bridge",
        category="accessibility_fixture",
        filename="tactile_bridge.stl",
        file_url="/static/assets/models/demo/tactile_bridge.stl",
        file_format="stl",
        default_material="unfinished_wood",
        scale_hint=0.94,
        description="Bridge-like access shape with supports and one raised guide rail for path-following trials.",
        source_name="FeelIT internal generated geometry",
        source_url="internal://feelit/tactile_bridge",
    ),
    DemoModel(
        slug="locator_token_stl",
        title="Locator Token",
        category="navigation_aid",
        filename="locator_token.stl",
        file_url="/static/assets/models/demo/locator_token.stl",
        file_format="stl",
        default_material="textured_polymer",
        scale_hint=0.78,
        description="Compact stepped token for studying recognisable tactile markers and rotational orientation cues.",
        source_name="FeelIT internal generated geometry",
        source_url="internal://feelit/locator_token",
    ),
    DemoModel(
        slug="orientation_marker_gltf",
        title="Orientation Marker",
        category="navigation_aid",
        filename="orientation_marker.gltf",
        file_url="/static/assets/models/demo/orientation_marker.gltf",
        file_format="gltf",
        default_material="coated_paper",
        scale_hint=0.88,
        description="Self-contained glTF marker with a broad base and pyramidal top for directional cue experiments.",
        source_name="FeelIT internal generated geometry",
        source_url="internal://feelit/orientation_marker",
    ),
    DemoModel(
        slug="navigation_puck_glb",
        title="Navigation Puck",
        category="navigation_aid",
        filename="navigation_puck.glb",
        file_url="/static/assets/models/demo/navigation_puck.glb",
        file_format="glb",
        default_material="polished_metal",
        scale_hint=0.82,
        description="Binary glTF puck with stepped levels and a central peg for quick multi-format runtime validation.",
        source_name="FeelIT internal generated geometry",
        source_url="internal://feelit/navigation_puck",
    ),
)


def build_demo_model_catalog() -> list[dict[str, object]]:
    """Return the bundled model catalog."""
    catalog: list[dict[str, object]] = []
    for model in DEMO_MODELS:
        entry = asdict(model)
        entry["format_label"] = FORMAT_LABELS[model.file_format]
        catalog.append(entry)
    return catalog
