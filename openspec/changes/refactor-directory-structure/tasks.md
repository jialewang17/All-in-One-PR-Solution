## 1. Specification & Planning
- [ ] 1.1 Validate existing specs for directory expectations
- [ ] 1.2 Define mapping from current paths to target tree (core/tool subpackages, docs archive, demos/tests split)

## 2. Repository Restructure
- [ ] 2.1 Create new package folders (`core/common`, `core/processing`, `core/querying`, `core/generation`, `core/rlhf`)
- [ ] 2.2 Move corresponding modules and data files into the new packages and update `__init__.py`
- [ ] 2.3 Create new `tools/processing` and `tools/querying` folders and relocate scripts (功能 1-8, menu entry)
- [ ] 2.4 Move demo scripts into `examples/` and test scripts into `tests/`
- [ ] 2.5 Create `docs/archive/` for legacy markdowns and `archive/` for historical entry scripts

## 3. Code Updates
- [ ] 3.1 Update import paths, `sys.path` adjustments, and CLI references (e.g., `pr_rag_system_v1_1.py`, `unified_pr_system.py`)
- [ ] 3.2 Refresh configuration references (README, DIRECTORY_STRUCTURE.md, docs) to match new layout
- [ ] 3.3 Ensure tooling scripts (process, migrate, query) still locate moved modules

## 4. Validation
- [ ] 4.1 Run targeted lint/tests or smoke commands if available
- [ ] 4.2 Update documentation summary of structure and include migration notes
- [ ] 4.3 Review final tree to confirm no leftover v1/v1.1/shared folders remain

