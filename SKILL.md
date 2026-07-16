---
name: dba-app-builder
description: Build, inspect, modify, version, or generate low-code application export packages with the .dba extension, especially zlib-compressed UTF-8 JSON packages containing app groups, forms, fields, buttons, flows, association rules, SQL DDL tables, symbolTable placeholders, dashboards, or version metadata. Use when the user asks to analyze an existing .dba file, reverse engineer a .dba app, create a new system that must ultimately output .dba format, incrementally add fields/features to an existing .dba, convert requirements/function lists into .dba configuration, validate/package a generated .dba file for import testing, or manage the DBA skill/package workflow in git.
---

# DBA App Builder

Use this skill for `.dba` low-code app packages. Treat `.dba` as a private platform format unless the user provides official docs. Prefer template-driven generation from a known-good `.dba` over inventing a full package from scratch.

## Mode Selection

- **Greenfield generation**: use when the user wants a new system/application. Start from a verified importable DBA template, then replace or extend app metadata, modules, forms, fields, DDL, buttons, flows, and dashboards.
- **Incremental modification**: use when the user provides an existing `.dba` and asks to add fields, add forms, adjust workflows, add buttons, or extend functionality. Preserve the source package structure and make the smallest compatible change.
- **Import-debug iteration**: use when the user provides `errcode: 9999` or backend logs. Fix the concrete importer failure first, then regenerate a test package.

## Core Rules

1. Always preserve the original `.dba` file; write extracted and generated files to the workspace or requested output folder.
2. Inspect before editing: identify compression, JSON shape, version, app name, symbol table, forms, tables, flows, and dashboards.
3. Use `scripts/dba_tool.py` for deterministic unpack/pack/summary/resolve operations.
4. If generating an importable `.dba`, start from an existing template `.dba` whenever available, then replace/add app metadata, groups, forms, fields, DDL, and symbol table values.
5. Clearly label generated `.dba` files as import-test artifacts. Platform import compatibility must be verified in the target system.
6. Do not claim successful platform compatibility until the user confirms import worked or provides importer logs.

## Workflow: Analyze Existing DBA

1. Run:

```bash
python3 <skill>/scripts/dba_tool.py inspect INPUT.dba
python3 <skill>/scripts/dba_tool.py unpack INPUT.dba --out work/dba_unpacked
python3 <skill>/scripts/dba_tool.py summary work/dba_unpacked/app.json --out outputs/dba_summary
```

2. Read the generated Markdown/CSV summaries, not the raw JSON first.
3. Report:
   - file format and compression
   - app name/version
   - module/group list
   - form list
   - table count and key tables
   - workflow/button/rule counts
   - whether business data records appear present

## Workflow: Build New System as DBA

1. Freeze requirements first:
   - system name
   - modules
   - forms/entities
   - fields and types
   - child tables
   - workflows
   - buttons/actions
   - permissions
   - dashboards/reports
   - import target/platform if known
2. If user has an existing `.dba`, use it as the structural template. If not, explain that output will be a best-effort package.
3. Produce intermediate deliverables before `.dba`:
   - `feature_list.csv`
   - `data_model.md`
   - `schema.sql`
   - `app_config.json`
4. Generate IDs deterministically enough for consistency:
   - UUID-like 32 hex ids for app/group/form/field/common ids
   - platform-style field names such as `i<token>_<component>_<token>`
   - table names with business prefix plus short token
5. Construct or update `symbolTable.symbols`.
6. Replace raw repeated IDs/table names with `@@{symbols.[n]}` where following the template style.
   - Keep `form.id` and `form.formKey` as the same symbol placeholder. Do not replace `formKey` with a plain string such as `item_category`.
   - Keep `tabFieldReference.formId` and `tabs[].tabFormKey` aligned to the form's symbol placeholder.
7. Run pack and validation:

```bash
python3 <skill>/scripts/dba_tool.py pack app_config.json --out outputs/generated.dba
python3 <skill>/scripts/dba_tool.py inspect outputs/generated.dba
python3 <skill>/scripts/dba_tool.py unpack outputs/generated.dba --out work/generated_check
```

8. Ask the user to import-test the generated `.dba`. If import fails, request the exact error/log and patch the JSON/package accordingly.

## Workflow: Modify Existing DBA

1. Unpack and summarize the source DBA:

```bash
python3 <skill>/scripts/dba_tool.py unpack SOURCE.dba --out work/source_dba --pretty
python3 <skill>/scripts/dba_tool.py summary work/source_dba/app.json --out work/source_dba/summary
```

2. Locate the target group/form/table using the summary CSVs.
3. Choose a same-type template inside the source package:
   - text field: clone an existing `maminput`
   - number/amount/quantity: clone `digitalformat`
   - date: clone `date`
   - option: clone `mamselect` or `mamradio`
   - child detail table: clone an existing `childrenTable` plus its table DDL
   - workflow: clone a similar `flowModels` block and preserve node/button structure
4. Add new symbol entries for new fields/forms/tables/common ids. Prefer appending to `symbolTable.symbols` for incremental changes.
5. Update every representation of the change:
   - `forms[].fields`
   - `styleDetail`
   - `addOption` and `editOption`
   - `tabFieldReference`
   - `tabs`
   - `tabViews` only when cloning or preserving existing saved views; do not invent broad replacement views unless platform testing proves they are required
   - `tables[].ddl`
   - association/rule/button references if touched
6. Preserve importer invariants:
   - `form.id == form.formKey`
   - `tabFieldReference.formId == form.id`
   - `tabs[].tabFormKey == form.id`
   - every field-bearing form must have usable `tabs` and `tabFieldReference`
   - when `tabViews` exist, each `tabViews[].tabKey` must match a `tabs[].tabKey` in the same form
   - no temporary plain ids such as `item_category`
7. Package and import-test one change set at a time. Name outputs by step, e.g. `v1_add_fields.dba`, `v2_add_form.dba`, `v3_add_workflow.dba`.

## Importer Pitfalls

- If backend logs show `检测到表单id、key不一致存在:@@{symbols.[n]},...` and `StringIndexOutOfBoundsException` in `SymbolTable.extractSymbolIndex`, set `form.formKey = form.id` and align `tabFieldReference.formId` plus all `tabs[].tabFormKey`.
- Import success is not enough. After any import-debug package, the user must click menus and open representative list pages. If logs show `/tab_views/<id>/settings` with `TabGridViewHelper.fromTab` `NullPointerException`, treat it as a list/menu runtime metadata failure, not an import failure.
- Do not remove `tabFieldReference` as a generic duplicate-key fix. It is required by list/menu runtime in observed packages. Removing it can allow import but make every menu fail when opened.
- When stripping duplicate-key metadata, distinguish import-only relation metadata from runtime list metadata:
  - Safer to strip when duplicate errors require it: `leftTreeOption`, `associationOptions`, `relationOptions`, `referenceRanges`, `referenceForms`, `referenceDataList`, `dataFillList`, `functionOptions`, `assciation`, `aboutTableInfo`, `aboutTableId`, `aboutPluginFormId`, `aboutTablePlugin`, `referenceFormKey`, `referenceFormId`, `linkage`, `linkageTable`, `linkageOptions`, `qrcodeStencil`, `aggregations`.
  - Preserve or rebuild for every field-bearing form: `tabs`, `tabFieldReference`, `styleDetail`, `addOption`, `editOption`, `dataTitle`, and table DDL.
  - Preserve existing `tabViews` unless they are the concrete cause of the runtime failure. If rebuilding them, bind each view to a real tab by setting `tabViews[].tabKey` to an existing same-form `tabs[].tabKey`.
- If the last known-good package is known, use it as the runtime baseline. Compare good vs failing packages for counts and invariants before deleting metadata. In one observed failure chain, package `v8` opened menus correctly, later packages imported only after `tabFieldReference` was stripped, and all menus then failed with `TabGridViewHelper.fromTab`. The successful fix restored the `v8`-style `tabFieldReference/tabs/tabViews` runtime metadata while still stripping only the duplicate-key import metadata.
- For newly added field-bearing forms cloned from a template, ensure `tabs` are also cloned or rebuilt. A form with fields and `tabFieldReference` but no `tabs` may import yet fail at menu/list runtime.
- Validation checklist before handing an import-debug `.dba` to the user:
  - `inspect`, `unpack`, and `summary` pass.
  - `form.id == form.formKey` for every form.
  - every field-bearing form has `tabs`, `tabFieldReference`, `styleDetail`, `addOption`, and `editOption`.
  - `tabFieldReference.formId == form.id`.
  - every `tabs[].formKey` and `tabs[].tabFormKey` equals the form key.
  - every existing `tabViews[].tabKey` matches a same-form `tabs[].tabKey`.
  - intentionally stripped duplicate-key metadata counts are zero.
- Search the generated JSON for old field names, old table names, and temporary plain keys before packaging.
- Treat `errcode: 9999` as insufficient; ask for backend logs around `/apps/import`.

## Git Management

- Keep this skill as a normal git repository when the user asks to version or upload it.
- Commit only the skill folder contents: `SKILL.md`, `agents/`, `references/`, and `scripts/`.
- Do not commit generated `.dba` artifacts, unpacked customer packages, logs, or workspace outputs unless the user explicitly asks.
- Prefer a private GitHub repository for this skill because importer behavior and platform details may be sensitive.

## Component Mapping

Use these common component names unless a template shows a stricter convention:

| Business field | Component type | SQL type |
|---|---|---|
| single-line text | `maminput` | `varchar(120)` |
| long text | `mamtextarea` / `mamtextsuper` | `text` |
| number, amount, area | `digitalformat` | `double` |
| date | `date` | `bigint(14)` |
| single select | `mamselect` | `text` |
| radio | `mamradio` | `text` |
| user | `userHelp` | `longtext` plus name/id helper columns when template uses them |
| multiple users | `userHelpMulti` | `longtext` plus helper columns |
| department | `department` | `longtext` plus helper columns |
| related record | `aboutTable` | `varchar(255)` plus `_ref_id` and `_ref_child_id` text columns |
| child detail table | `childrenTable` | separate table with `pid` foreign-key style column |
| attachment | `documentUpload` | `text` |
| section divider | `separatorline` | `longtext` |

## SQL Conventions

For each main form table, include common system columns unless the template differs:

- `id`, `seq`, `data_title`, `summary`
- creator/updater org fields
- workflow fields for approval forms
- `sys_status`, `table_id`, `data_type`

For child tables, include:

- `id`, `pid`, `seq`
- creator/updater fields
- `sys_status`, `table_id`, `from_ref_id`
- business columns
- `KEY <table>_pid (pid)`

Prefer `ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COMMENT='<form/table label>'` when matching the observed package style.

## References

Read `references/dba-format.md` when you need details on the observed package structure, placeholder resolution, or known compatibility risks.
