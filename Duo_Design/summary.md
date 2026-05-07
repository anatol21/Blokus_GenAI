# Blokus Focus Pokus - Repository Summary

This repository contains a plain-Python implementation of the board game **Blokus**, designed for both human play and automated development testing.

## 🕹️ Core Functionality
- **Game Modes:** 
    - **Classic:** Full 4-player implementation on a 20x20 board.
    - **Duo:** 2-player configuration (evolution baseline for the engine).
- **Interfaces:** 
    - **CLI:** For state creation, move validation, and legal move generation.
    - **GUI:** A Tkinter-based interactive interface with drag-and-drop support.
- **Rules Engine:** Implements the full Blokus rulebook, including corner-start requirements, adjacency restrictions, and piece transformations (rotate/flip).

## 🧠 Engines
The project utilizes two distinct types of "engines":

1.  **Game Engine (`src/blokus/engine.py`):**
    - A deterministic Python engine for game logic.
    - **Zero LLM runtime dependency:** The game logic remains independent of AI services for reliability and predictability.
2.  **Development AI Engines:**
    - **Agentic Review:** LLM-powered agents integrated into GitHub workflows for PR intelligence and code review.
    - **Autonomous Repair:** An automation layer (`automation.py`) that monitors CI failures and attempts self-healing on `agent/*` branches.

## 👥 Player Options
- **Controller Types:**
    - **Human:** Manual control via GUI or CLI.
    - **Computer:** Automated gameplay.
- **AI Strategies:**
    - **Default:** Picks the largest possible legal move first to maximize board coverage.
- **Multiplayer:** Supports local pass-and-play; modular structure allows for future multiplayer extensions.

## 🏗️ Technical Highlights
- **Stack:** Plain Python 3, Tkinter (GUI), JSON (State Serialization).
- **Architecture:** Decoupled game logic (engine) from presentation layers (CLI/GUI).
- **Quality Assurance:** Extensive use of JSON schemas for contract validation and repeatable test fixtures.
