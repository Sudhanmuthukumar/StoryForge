# StoryForge V1.0.0

StoryForge is a local AI storytelling and narrative engineering platform designed to help creators build, analyze, train, evaluate, and export narrative systems.

The project combines dataset extraction, pattern analysis, knowledge engineering, model training pipelines, evaluation tools, narrative generation systems, and game-development workflows into a single integrated platform.

StoryForge was developed as a personal AI engineering project to explore storytelling systems, dataset construction, local LLM fine-tuning, narrative intelligence, simulation engines, and game narrative generation.

---

## Core Features

### Dataset Lab

Extracts and processes literary source material into structured narrative datasets.

Features:

* Document extraction
* Chapter segmentation
* Pattern extraction
* Dataset generation
* Quality validation
* Benchmark dataset creation

### Knowledge Engine

Builds reusable narrative knowledge from extracted datasets.

Stores:

* Character patterns
* Conflict patterns
* Dialogue patterns
* Narrative structures
* Scene patterns
* Pacing patterns
* Worldbuilding patterns

### Research Lab

Tracks experiments and evaluates narrative pattern effectiveness.

Features:

* Dataset experiment tracking
* Pattern performance analysis
* Evaluation history
* Training history

### Training Pipeline

Local fine-tuning workflow for language models.

Features:

* Dataset preparation
* QLoRA training support
* Training estimation
* Training queue management
* Model registry management

### Evaluation Pipeline

Benchmark and compare trained models.

Features:

* Prompt benchmarking
* Response grading
* Comparative evaluation
* Performance scoring

### Creator Suite

Narrative design tools for writers and worldbuilders.

Includes:

* Story Architect
* Character Forge
* Lore Builder
* Quest Generator
* Narrative Analyzer

### Game Narrative Toolkit

Generates game-ready narrative content.

Includes:

* NPC Forge
* Faction Builder
* Quest Chain Builder
* Campaign Builder

### NPC Intelligence System

Generates stateful NPC behavior.

Includes:

* Memory Engine
* Goal Engine
* Relationship Engine
* Reaction Engine

### Dynamic World State Engine

Simulates deterministic world evolution.

Tracks:

* Security
* Prosperity
* Stability
* Reputation
* Event consequences

### Unreal Export Layer

Exports generated content directly into Unreal Engine compatible formats.

Supported:

* JSON
* YAML
* CSV DataTables

---

## Architecture

StoryForge is organized into modular systems:

Dataset Lab
→ Knowledge Engine
→ Research Lab
→ Training Pipeline
→ Evaluation Pipeline
→ Creator Suite
→ Game Narrative Toolkit
→ NPC Intelligence
→ World State Engine
→ Unreal Export Layer

---

## Project Structure

```text
StoryForge
│
├── config/
├── core/
├── dataset_lab/
├── docs/
├── models/
├── modules/
├── services/
├── tests/
├── ui/
├── utils/
│
├── main.py
├── requirements.txt
└── README.md
```

---

## Technologies Used

* Python
* PyQt6
* Ollama
* QLoRA
* JSON
* YAML
* Unreal Engine DataTables

---

## Training Data

StoryForge does not distribute training datasets, books, model weights, LoRA adapters, GGUF files, or checkpoints.

Training validation sources are documented in:

TRAINING_DATA_SOURCES.md

---

## Running StoryForge

Install dependencies:

```bash
pip install -r requirements.txt
```

Launch:

```bash
python main.py
```

Additional setup instructions are available in:

* INSTALLATION.md
* USER_GUIDE.md
* UNREAL_EXPORT_GUIDE.md

---

## Roadmap

### V1.0.0

* Dataset Lab
* Knowledge Engine
* Research Lab
* Training Pipeline
* Evaluation Pipeline
* Creator Suite
* Game Narrative Toolkit
* NPC Intelligence
* World State Engine
* Unreal Export Layer

### Future Work

* Expanded genre datasets
* Additional model training workflows
* Advanced benchmark suites
* Enhanced world simulation
* Writer Workspace integration

---

## Author

Sudhan M

B.E. Computer Science and Engineering

Interests:

* Artificial Intelligence
* Machine Learning
* NLP
* Game Development
* Narrative Systems
* Software Engineering
