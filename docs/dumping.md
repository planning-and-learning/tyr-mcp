# Dumping

Planning is in-memory. Dump only when external processes need JSON or Markdown files.

## `DumpFormat`

| Value | Meaning |
|---|---|
| `DumpFormat.JSON` | Machine-readable JSON. |
| `DumpFormat.MD` | Human-readable Markdown summary. |

## Result `dump`

```python
dumped = result.dump(output_dir, formats=(DumpFormat.JSON,), include_plan_text=False)
```

| Name | Type | Default | Description |
|---|---|---|---|
| `output_dir` | `str | Path` | required | Directory to create and write into. |
| `formats` | `tuple[DumpFormat, ...]` | `(DumpFormat.JSON,)` | Requested output formats. |
| `include_plan_text` | `bool` | `False` | Write `plan.txt` when a plan exists. JSON keeps plan metadata and `plan_path`. |

`FindSatisficingPlanResult.dump(...)` writes `result.json` and `task.json` for `DumpFormat.JSON`. When `include_plan_text=True` and a plan exists, it also writes `plan.txt`, a step trace with `[facts]` sections. `DumpFormat.MD` writes `summary.md` with a plan metadata table.

| Field | Type | Description |
|---|---|---|
| `output_dir` | `Path` | Absolute output directory. |
| `files` | `tuple[Path, ...]` | Files written by the dump call. |

```python
result = find_satisficing_plan(task)
dump = result.dump("artifacts/find-plan", formats=(DumpFormat.JSON, DumpFormat.MD))
```
