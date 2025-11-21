## ADDED Requirements

### Requirement: 分层目录结构
The unified PR system SHALL organize repository contents into clearly separated layers to reflect domain responsibilities.

#### Scenario: Core vs Tools separation
- **WHEN** developers inspect the repository tree
- **THEN** all reusable domain logic MUST reside under `core/` subdivided into `common`, `processing`, `querying`, `generation`, and `rlhf`
- **AND** executable workflow scripts MUST reside under `tools/` subdivided into `processing` (功能 1-5) and `querying` (功能 6-8)
- **AND** menu entry `pr_rag_system_v1_1.py` SHALL be located under `tools/` and continue to expose功能 1-8 + 14 without requiring a new `main.py`

#### Scenario: Documentation, demos, and archives
- **WHEN** users look for demos/tests/documentation
- **THEN** demo scripts SHALL be stored in `examples/`, automated tests in `tests/`, and operational docs in `docs/` with legacy markdowns archived in `docs/archive/`
- **AND** deprecated entry scripts (e.g., `pr_process_all_v1_1.py`, `unified_pr_system.py`) SHALL be moved to root-level `archive/`
- **AND** README/DIRECTORY_STRUCTURE documentation MUST describe this structure so new contributors can map功能 to directories quickly

