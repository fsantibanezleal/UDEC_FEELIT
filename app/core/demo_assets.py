"""Real OBJ demo assets bundled with FeelIT."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DemoModel:
    """Describe a bundled OBJ asset for interactive exploration demos."""

    slug: str
    title: str
    category: str
    filename: str
    file_url: str
    default_material: str
    scale_hint: float
    description: str
    source_name: str
    source_url: str


DEMO_MODELS: tuple[DemoModel, ...] = (
    DemoModel(
        slug="walt_head",
        title="Walt Head",
        category="sculpture",
        filename="WaltHead.obj",
        file_url="/static/assets/models/demo/WaltHead.obj",
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
        default_material="glazed_ceramic",
        scale_hint=0.92,
        description="Faceted vessel profile useful for neck, shoulder, and base transition studies.",
        source_name="FeelIT internal lightweight geometry",
        source_url="internal://feelit/vase_lowpoly",
    ),
)


def build_demo_model_catalog() -> list[dict[str, object]]:
    """Return the bundled model catalog."""
    return [asdict(model) for model in DEMO_MODELS]
