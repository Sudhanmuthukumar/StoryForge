# StoryForge AI Developer Guide

## System Initialization
StoryForge uses a pure `PySide6` UI framework decoupled completely from offline business logic layers (Services).

## Service Implementations

* **`core/story_manager.py`**: Controls pure Read/Write access arrays. Wraps outputs defensively avoiding destructive data corruption dynamically.
* **`services/`**: Every intelligence engine occupies a discrete `.py` file utilizing 100% standard libraries (`json`, `copy`, `uuid`, `pathlib`, etc). DO NOT introduce new pip dependencies directly unless parsing external inputs (e.g. `pypdf`, `python-docx`).
* **`config/`**: JSON parameter configurations bound closely to parsing multipliers. Changing variables locally updates behavior application-wide strictly without altering code constraints natively.

## Data Structures
All structured mappings are housed inside explicit `DEFAULT` templates natively wrapped inside `utils/constants.py`.
To add a new parameter, implement the modification natively inside the parent template securely utilizing `deepcopy()` injections explicitly.

## Running Tests
Trigger the native testing suites executing:
`python tests/integration_tests.py`
`python tests/performance_tests.py`
`python tests/stress_tests.py`
