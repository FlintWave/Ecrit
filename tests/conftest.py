"""Shared test fixtures for Écrit test suite."""

import os
import sys
import json
import shutil
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import pytest
from PySide6.QtWidgets import QApplication

from ecrit.ui.styles import theme
from ecrit.ui.styles.theme import NOCTURNE, ORGANIC, set_theme
from ecrit.stores.app_state import AppState


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture(autouse=True)
def reset_theme(qapp):
    set_theme(NOCTURNE)
    yield
    set_theme(NOCTURNE)
    import gc
    gc.collect()
    qapp.processEvents()


@pytest.fixture
def tmp_project(tmp_path):
    project_dir = tmp_path / "TestProject"
    project_dir.mkdir()
    script_file = project_dir / "script.fountain"
    script_file.write_text(SAMPLE_FOUNTAIN, encoding="utf-8")
    meta = {
        "title": "Test Project",
        "author": "Test Author",
        "format_id": "fountain/core",
        "paper": "USLetter",
        "kind": "Single",
    }
    (project_dir / "project.json").write_text(json.dumps(meta), encoding="utf-8")
    return str(project_dir)


@pytest.fixture
def fresh_state(tmp_path):
    state = AppState()
    state.project_folder = str(tmp_path / "projects")
    os.makedirs(state.project_folder, exist_ok=True)
    return state


SAMPLE_FOUNTAIN = """Title: Test Script
Credit: written by
Author: Test Author

====

INT. COFFEE SHOP - DAY

ALICE enters and sits down. She looks around nervously.

ALICE
(whispering)
Is anyone watching?

BOB
Nobody. You're safe.

> CUT TO:

EXT. PARK - NIGHT

They walk under the streetlights.

ALICE
I can't believe we made it.

BOB
(smiling)
Neither can I.

# Act Two

= Synopsis of act two

[[This is a note about the plot.]]

INT. OFFICE - DAY

CHARLIE is typing at a desk.

CHARLIE
We need to talk about what happened.

ALICE
There's nothing to talk about.
"""

EMPTY_FOUNTAIN = ""

MINIMAL_FOUNTAIN = """INT. ROOM - DAY

A person sits.
"""

UNICODE_FOUNTAIN = """Title: Écriture en Français
Author: José García-López

INT. CAFÉ — MATIN

HÉLOÏSE entre. Elle regarde les étagères de pâtisseries.

HÉLOÏSE
Où sont les croissants, s'il vous plaît?

LE BOULANGER
Les voilà, Madame. Très frais ce matin.

> FONDU ENCHAÎNÉ:

EXT. PARC DES BUTTES-CHAUMONT — APRÈS-MIDI

Les enfants jouent près de la cascade.
"""

HUGE_FOUNTAIN = "\n".join(
    [
        f"INT. SCENE {i} - DAY\n\nCHARACTER_{i}\nLine of dialogue number {i}.\n"
        for i in range(500)
    ]
)

MALFORMED_FOUNTAIN = """Title:
Credit:
Author:

INT.

@
(
>

"""
