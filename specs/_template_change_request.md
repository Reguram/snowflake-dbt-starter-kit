# Change Request — <YYYY-MM-DD>
**From:** <BA name>
**Models impacted:** `<model_a>`, `<model_b>`
**Source:** `<source_name>`

<!-- Free-form context paragraph the engineer can read for background. -->

## <model_a>

- In `<model_a>`, rename `<old_col>` to `<new_col>`.
- Add column `<col>` to `<model_a>` (type: <string|number|boolean|date|timestamp>; description: <short text>; tests: <not_null,unique,...>).
- Drop column `<col>` from `<model_a>`.
- Coalesce `<col_a>` and `<col_b>` into `<new_col>` in `<model_a>`.
- Concatenate `<col_a>` and `<col_b>` into `<new_col>` in `<model_a>`.
- Change type of `<model_a>.<col>` to <integer>.
- Change description of `<model_a>.<col>` to "<text>".
- Add test <not_null|unique> to `<model_a>.<col>`.

## <model_b>

- ...

<!--
Save this file as:
  specs/<source_name>/_changes/<YYYY-MM-DD>-<short-slug>.md

Then open it in your agent (Cortex Code / Copilot / Claude Code) and say:
  "Apply this change document to source <source_name>."

The spec-driven-model-sync skill takes over: parses each bullet, previews
the edits, and (after you confirm) writes them to the model SQL + schema.yml
and updates the spec/lockfile. No Python or shell command is needed.
-->
