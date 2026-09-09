"""Story structure templates for screenplay outlining.

Each template defines a series of narrative beats that writers can use
to scaffold their outlines on the OutlineCanvas.
"""

from __future__ import annotations

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class StructureBeat:
    """A single narrative beat within a structure template."""

    name: str
    description: str
    act: int
    percentage: int  # 0-100, approximate position in the screenplay


@dataclass(frozen=True, slots=True)
class StructureTemplate:
    """A complete story structure template."""

    name: str
    description: str
    beats: list[StructureBeat] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Built-in templates
# ---------------------------------------------------------------------------

_THREE_ACT = StructureTemplate(
    name="Three-Act Structure",
    description="The classic beginning-middle-end framework used in most screenplays.",
    beats=[
        StructureBeat(
            name="Opening Image",
            description="A visual that represents the starting point of the protagonist's world.",
            act=1,
            percentage=1,
        ),
        StructureBeat(
            name="Theme Stated",
            description="A character hints at the screenplay's thematic premise.",
            act=1,
            percentage=5,
        ),
        StructureBeat(
            name="Catalyst",
            description="An event that disrupts the protagonist's status quo and sets the story in motion.",
            act=1,
            percentage=12,
        ),
        StructureBeat(
            name="Debate",
            description="The protagonist questions whether to accept the call to adventure.",
            act=1,
            percentage=18,
        ),
        StructureBeat(
            name="Break into Two",
            description="The protagonist commits and enters the new world of Act 2.",
            act=1,
            percentage=25,
        ),
        StructureBeat(
            name="B-Story",
            description="A secondary storyline begins, often a love story or mentor relationship.",
            act=2,
            percentage=30,
        ),
        StructureBeat(
            name="Midpoint",
            description="A major reversal or revelation that raises the stakes.",
            act=2,
            percentage=50,
        ),
        StructureBeat(
            name="Bad Guys Close In",
            description="External pressures mount and internal flaws intensify.",
            act=2,
            percentage=60,
        ),
        StructureBeat(
            name="All Is Lost",
            description="The protagonist hits rock bottom; the opposite of the midpoint high.",
            act=2,
            percentage=75,
        ),
        StructureBeat(
            name="Dark Night of the Soul",
            description="The protagonist wallows in hopelessness before finding inner strength.",
            act=2,
            percentage=80,
        ),
        StructureBeat(
            name="Break into Three",
            description="A new idea or inspiration propels the protagonist into the final act.",
            act=3,
            percentage=80,
        ),
        StructureBeat(
            name="Finale",
            description="The protagonist confronts the central conflict and applies the lesson learned.",
            act=3,
            percentage=88,
        ),
        StructureBeat(
            name="Final Image",
            description="A closing visual that shows how the protagonist's world has changed.",
            act=3,
            percentage=99,
        ),
    ],
)

_SAVE_THE_CAT = StructureTemplate(
    name="Save the Cat",
    description="Blake Snyder's 15-beat structure for tightly paced screenplays.",
    beats=[
        StructureBeat(
            name="Opening Image",
            description="A snapshot of the protagonist's life before the story begins.",
            act=1,
            percentage=1,
        ),
        StructureBeat(
            name="Theme Stated",
            description="Someone poses a question or makes a statement that is the movie's theme.",
            act=1,
            percentage=5,
        ),
        StructureBeat(
            name="Set-Up",
            description="Introduce the protagonist's world, stakes, and the things that need fixing.",
            act=1,
            percentage=10,
        ),
        StructureBeat(
            name="Catalyst",
            description="A life-changing event that knocks down the protagonist's house of cards.",
            act=1,
            percentage=12,
        ),
        StructureBeat(
            name="Debate",
            description="The protagonist wrestles with whether to take action.",
            act=1,
            percentage=18,
        ),
        StructureBeat(
            name="Break into Two",
            description="The protagonist makes a choice and enters the upside-down world of Act 2.",
            act=1,
            percentage=25,
        ),
        StructureBeat(
            name="B Story",
            description="A new character or subplot arrives, often carrying the theme.",
            act=2,
            percentage=30,
        ),
        StructureBeat(
            name="Fun and Games",
            description="The promise of the premise -- the reason the audience bought a ticket.",
            act=2,
            percentage=37,
        ),
        StructureBeat(
            name="Midpoint",
            description="A false victory or false defeat that raises the stakes.",
            act=2,
            percentage=50,
        ),
        StructureBeat(
            name="Bad Guys Close In",
            description="Opposition tightens, allies scatter, internal doubts grow.",
            act=2,
            percentage=60,
        ),
        StructureBeat(
            name="All Is Lost",
            description="The lowest point; a whiff of death -- real or metaphorical.",
            act=2,
            percentage=75,
        ),
        StructureBeat(
            name="Dark Night of the Soul",
            description="Darkness before the dawn; the protagonist digs deep.",
            act=2,
            percentage=78,
        ),
        StructureBeat(
            name="Break into Three",
            description="Thanks to the B Story and the hero's fresh idea, a solution emerges.",
            act=3,
            percentage=80,
        ),
        StructureBeat(
            name="Finale",
            description="Applying everything learned, the protagonist defeats the bad guys.",
            act=3,
            percentage=88,
        ),
        StructureBeat(
            name="Final Image",
            description="The opposite of the Opening Image, proving real change has occurred.",
            act=3,
            percentage=99,
        ),
    ],
)

_HEROS_JOURNEY = StructureTemplate(
    name="Hero's Journey",
    description="Campbell and Vogler's mythic 12-stage story structure.",
    beats=[
        StructureBeat(
            name="Ordinary World",
            description="The hero's mundane life before the adventure begins.",
            act=1,
            percentage=1,
        ),
        StructureBeat(
            name="Call to Adventure",
            description="A challenge or quest is presented to the hero.",
            act=1,
            percentage=10,
        ),
        StructureBeat(
            name="Refusal of the Call",
            description="The hero hesitates, afraid of the unknown.",
            act=1,
            percentage=15,
        ),
        StructureBeat(
            name="Meeting the Mentor",
            description="The hero encounters a guide who provides wisdom or tools.",
            act=1,
            percentage=20,
        ),
        StructureBeat(
            name="Crossing the Threshold",
            description="The hero commits to the adventure and enters the special world.",
            act=1,
            percentage=25,
        ),
        StructureBeat(
            name="Tests, Allies, Enemies",
            description="The hero faces trials, makes friends, and confronts foes.",
            act=2,
            percentage=35,
        ),
        StructureBeat(
            name="Approach to the Inmost Cave",
            description="The hero nears the central ordeal, preparing for the big challenge.",
            act=2,
            percentage=45,
        ),
        StructureBeat(
            name="Ordeal",
            description="The hero faces the greatest challenge and experiences a death-and-rebirth moment.",
            act=2,
            percentage=50,
        ),
        StructureBeat(
            name="Reward",
            description="The hero seizes the prize earned through the ordeal.",
            act=2,
            percentage=60,
        ),
        StructureBeat(
            name="The Road Back",
            description="The hero begins the journey home, often pursued or tested again.",
            act=3,
            percentage=75,
        ),
        StructureBeat(
            name="Resurrection",
            description="A final test where the hero applies everything learned; the climax.",
            act=3,
            percentage=88,
        ),
        StructureBeat(
            name="Return with the Elixir",
            description="The hero comes home transformed, bearing a gift for the ordinary world.",
            act=3,
            percentage=99,
        ),
    ],
)

_STORY_CIRCLE = StructureTemplate(
    name="Story Circle",
    description="Dan Harmon's simplified 8-step adaptation of the Hero's Journey.",
    beats=[
        StructureBeat(
            name="You",
            description="A character is in their comfort zone.",
            act=1,
            percentage=1,
        ),
        StructureBeat(
            name="Need",
            description="But they want something.",
            act=1,
            percentage=13,
        ),
        StructureBeat(
            name="Go",
            description="They enter an unfamiliar situation.",
            act=1,
            percentage=25,
        ),
        StructureBeat(
            name="Search",
            description="They adapt to the new situation, searching for what they need.",
            act=2,
            percentage=37,
        ),
        StructureBeat(
            name="Find",
            description="They find what they wanted.",
            act=2,
            percentage=50,
        ),
        StructureBeat(
            name="Take",
            description="But they pay a heavy price for it.",
            act=2,
            percentage=63,
        ),
        StructureBeat(
            name="Return",
            description="They return to their familiar situation.",
            act=3,
            percentage=75,
        ),
        StructureBeat(
            name="Change",
            description="Having changed as a result of the journey.",
            act=3,
            percentage=99,
        ),
    ],
)

_FIVE_ACT = StructureTemplate(
    name="Five-Act Structure",
    description="The Shakespearean five-act dramatic structure.",
    beats=[
        StructureBeat(
            name="Exposition",
            description="Introduce the setting, characters, and the inciting incident.",
            act=1,
            percentage=5,
        ),
        StructureBeat(
            name="Rising Action",
            description="Complications and conflicts build as the protagonist pursues their goal.",
            act=2,
            percentage=25,
        ),
        StructureBeat(
            name="Climax",
            description="The turning point -- the moment of highest tension and dramatic conflict.",
            act=3,
            percentage=50,
        ),
        StructureBeat(
            name="Falling Action",
            description="The consequences of the climax unfold; tension begins to resolve.",
            act=4,
            percentage=75,
        ),
        StructureBeat(
            name="Denouement",
            description="Final resolution; loose ends are tied and a new equilibrium is established.",
            act=5,
            percentage=95,
        ),
    ],
)

_KISHOTENKETSU = StructureTemplate(
    name="Kishotenketsu",
    description="A four-act East Asian narrative structure built on contrast rather than conflict.",
    beats=[
        StructureBeat(
            name="Ki (Introduction)",
            description="Introduce the characters, setting, and situation without conflict.",
            act=1,
            percentage=10,
        ),
        StructureBeat(
            name="Sho (Development)",
            description="Develop the established elements; deepen the audience's understanding.",
            act=2,
            percentage=35,
        ),
        StructureBeat(
            name="Ten (Twist)",
            description="An unexpected turn that recontextualises everything; the core of the story.",
            act=3,
            percentage=60,
        ),
        StructureBeat(
            name="Ketsu (Conclusion)",
            description="Reconcile the twist with the earlier acts; bring the narrative to harmony.",
            act=4,
            percentage=90,
        ),
    ],
)

_SEQUENCE_APPROACH = StructureTemplate(
    name="Sequence Approach",
    description="Frank Daniel's eight-sequence structure across three acts.",
    beats=[
        StructureBeat(
            name="Sequence 1 -- Status Quo & Inciting Incident",
            description="Establish the world and deliver the event that gets the story going.",
            act=1,
            percentage=6,
        ),
        StructureBeat(
            name="Sequence 2 -- Predicament & Lock In",
            description="The protagonist grapples with the new situation and commits to a path.",
            act=1,
            percentage=18,
        ),
        StructureBeat(
            name="Sequence 3 -- First Obstacle & Raising the Stakes",
            description="Initial attempts meet resistance; the true scope of the problem emerges.",
            act=2,
            percentage=31,
        ),
        StructureBeat(
            name="Sequence 4 -- First Culmination / Midpoint",
            description="A major event shifts the direction of the story at the halfway mark.",
            act=2,
            percentage=44,
        ),
        StructureBeat(
            name="Sequence 5 -- Subplot & Rising Action",
            description="Subplots interweave; pressure builds as the protagonist digs deeper.",
            act=2,
            percentage=56,
        ),
        StructureBeat(
            name="Sequence 6 -- Main Culmination / End of Act 2",
            description="A devastating setback or revelation propels the story into the final act.",
            act=2,
            percentage=69,
        ),
        StructureBeat(
            name="Sequence 7 -- New Tension & Twist",
            description="A fresh complication or twist raises urgency heading into the climax.",
            act=3,
            percentage=81,
        ),
        StructureBeat(
            name="Sequence 8 -- Resolution",
            description="The climax, aftermath, and final image bring the story to a close.",
            act=3,
            percentage=94,
        ),
    ],
)


# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------

TEMPLATES: dict[str, StructureTemplate] = {
    "three_act": _THREE_ACT,
    "save_the_cat": _SAVE_THE_CAT,
    "heros_journey": _HEROS_JOURNEY,
    "story_circle": _STORY_CIRCLE,
    "five_act": _FIVE_ACT,
    "kishotenketsu": _KISHOTENKETSU,
    "sequence_approach": _SEQUENCE_APPROACH,
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_template(key: str) -> StructureTemplate | None:
    """Return a template by its registry key, or ``None`` if not found."""
    return TEMPLATES.get(key)


def list_templates() -> list[tuple[str, str]]:
    """Return ``(key, display_name)`` pairs for every built-in template."""
    return [(key, tpl.name) for key, tpl in TEMPLATES.items()]


def generate_outline_nodes(template: StructureTemplate) -> list[dict]:
    """Convert a template's beats into outline graph nodes for *OutlineCanvas*.

    Layout strategy:
    - Each act is arranged as a horizontal row.
    - Beats within an act are spaced evenly left to right.
    - An ``ActBreak`` node is placed at the start of each row.
    - Each beat becomes a ``Scene`` node with its description as the synopsis.
    - Consecutive nodes are connected so the canvas draws connectors.

    The returned dicts match the schema expected by
    ``OutlineCanvas.set_nodes()``:  ``id``, ``x``, ``y``, ``kind``,
    ``label``, ``synopsis``, and ``connections``.
    """
    if not template.beats:
        return []

    # Group beats by act
    acts: dict[int, list[StructureBeat]] = {}
    for beat in template.beats:
        acts.setdefault(beat.act, []).append(beat)

    nodes: list[dict] = []
    node_id = 0
    prev_id: int | None = None

    # Layout constants
    x_start = 40
    y_start = 40
    row_height = 140
    col_width = 230

    for act_index, act_num in enumerate(sorted(acts)):
        beats_in_act = acts[act_num]

        # Act break node
        act_node_id = node_id
        node_id += 1
        act_x = x_start
        act_y = y_start + act_index * row_height

        connections: list[int] = []
        if prev_id is not None:
            connections = [act_node_id]
            # Add connection from the previous node to this act break
            for n in nodes:
                if n["id"] == prev_id:
                    n["connections"].append(act_node_id)
                    break

        act_node: dict = {
            "id": act_node_id,
            "x": act_x,
            "y": act_y,
            "kind": "ActBreak",
            "label": f"Act {act_num}",
            "synopsis": "",
            "connections": [],
        }
        nodes.append(act_node)
        prev_id = act_node_id

        # Beat nodes
        for beat_index, beat in enumerate(beats_in_act):
            beat_node_id = node_id
            node_id += 1
            beat_x = x_start + (beat_index + 1) * col_width
            beat_y = act_y

            beat_node: dict = {
                "id": beat_node_id,
                "x": beat_x,
                "y": beat_y,
                "kind": "Scene",
                "label": beat.name,
                "synopsis": beat.description,
                "connections": [],
            }

            # Connect previous node to this beat
            for n in nodes:
                if n["id"] == prev_id:
                    n["connections"].append(beat_node_id)
                    break

            nodes.append(beat_node)
            prev_id = beat_node_id

    return nodes
