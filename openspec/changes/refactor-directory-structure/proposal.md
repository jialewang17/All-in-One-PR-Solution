# Change: Refactor repository directory structure

## Why
- Current repository still mirrors historical v1/v1.1 split, causing duplicated entry scripts, scattered documentation, and unclear boundaries between reusable core logic and executable tooling.
- The user provided a target structure that flattens shared/v1_1 folders, groups code by domain (processing/querying/generation/RLHF), and separates runnable scripts, demos, and tests. We need to align code, docs, and imports with this structure while keeping `pr_rag_system_v1_1.py` as the primary entry point (no new `main.py` file).

## What Changes
- Move/rename files to match the requested tree (root README & requirements, config pack, `core/{common,processing,querying,generation,rlhf}`, `tools/{processing,querying}`, `examples/`, `tests/`, `docs/archive`, `archive/` for legacy entry scripts).
- Update package initializers, imports, sys.path adjustments, and documentation (`DIRECTORY_STRUCTURE.md`, README) to reflect the new layout and explain the “core = domain logic, tools = executable workflows” contract.
- Provide compatibility shims where paths changed (e.g., updating CLI scripts to import from new modules) and ensure menu options (功能 1-14) still work after relocation.

## Impact
- Specs: `unified-pr-system` (new requirement describing layered directory structure).
- Code: repository-wide file moves (core, tools, docs, demos/tests, configs) plus updates to scripts referencing old paths.
- Tooling: developers run commands from the reorganized locations; documentation must guide them through the new layout.

