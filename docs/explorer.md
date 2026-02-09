# Policy Explorer

Interactive graph visualization of the contract topology — statutes, benefit sections, test coverage, and network quirks.

![Explorer screenshot](media/2026-02-09_15-44.png)

## Usage

```bash
./explore.sh          # opens browser at localhost:8787
./explore.sh 9000     # custom port
```

## What the Graph Shows

The explorer builds its data by introspecting the policy models and parsing the test suite at startup. No manual graph maintenance needed — add a test class or policy section and it appears automatically.

### Node Types

| Shape | Color | Meaning |
|-------|-------|---------|
| Diamond | Amber | Founding statutes (ACA, MHPAEA, NSA, NMHPA, COBRA, ERISA) |
| Circle | Blue | Policy sections (Deductibles, Emergency, Dental, etc.) |
| Square | Red | Test classes — financial risk |
| Square | Orange | Test classes — coverage risk |
| Square | Purple | Test classes — regulatory risk |
| Square | Green | Test classes — correspondence risk |
| Triangle | Yellow | Network quirks (lab trap, observation status, etc.) |

### Edges

| Arrow | Meaning |
|-------|---------|
| Statute → Section | This statute governs/authorizes this benefit section |
| Section → Test | This test class verifies this section |
| Quirk → Section | This quirk affects this section |

## Interaction

- **Click a node** — opens detail panel with drill-down
- **Click linked items** in the detail panel to navigate the graph
- **Toggle node types** in the sidebar legend to filter
- **Press F** — fit entire graph to viewport
- **Scroll** — zoom
- **Drag** — pan

## Detail Panel

Clicking a node shows context-specific information:

- **Statute**: name, USC/CFR citation, which sections it governs
- **Section**: governing statutes, test classes that verify it, known quirks
- **Test class**: risk category, individual assertions with risk docstrings
- **Quirk**: description, affected services, risk if unhandled

## Architecture

The explorer is a single-file Python server (`tools/explorer.py`) that:

1. Imports the Green Cross policy instance
2. Walks the model to extract sections, statutes, and quirk nodes
3. Parses test files with Python's `ast` module to extract classes, methods, and docstrings
4. Serves the graph as JSON at `/api/graph`
5. Serves the visualization (`tools/index.html`) which renders with vis.js

No build step. No external dependencies beyond Pydantic (already installed for the models).
