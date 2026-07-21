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
3. Use `scripts/dba_tool.py` for deterministic unpack/pack/summary/resolve/validate operations.
4. If generating an importable `.dba`, start from an existing template `.dba` whenever available, then replace/add app metadata, groups, forms, fields, DDL, and symbol table values.
5. Clearly label generated `.dba` files as import-test artifacts. Platform import compatibility must be verified in the target system.
6. Do not claim successful platform compatibility until the user confirms import worked or provides importer logs.
7. Do not claim business-flow completeness from forms alone. A cross-module process is complete only when represented by platform-native related-record fields, child tables, business rules, workflow node settings, submit validations, or verified runtime behavior.
8. For Dabei/K6/搭贝应用工厂 packages, start from the platform-wide capability model, not from one customer's app. Decide whether a requirement belongs to form/field metadata, list design, business rules, workflow, DataM, print, plugins, permissions, tenant system settings, or external integration before editing a DBA.
9. For Dabei/K6/搭贝应用工厂 packages, classify every requested feature by proof level before calling it complete: `can_generate`, `api_verified`, `runtime_verified`, `platform_config_required`, or `not_safe_to_claim`. Use `references/dabei-platform.md` as the capability-boundary contract.
10. When the user asks to understand or verify the Dabei/K6 platform itself, run a platform-wide probe instead of inspecting only the current customer app. Cover PC factory/designer/settings, runtime app forms, workflow/task surfaces, DataM dashboards, print rendering, mobile routes, source/API owners, and tenant-configuration boundaries. Record the highest evidence level per capability.

## Dabei/K6 Platform-First Development Workflow

When working on any Dabei/K6 project, treat the customer requirement as an instance of the platform, not as the whole platform. Before designing forms or changing JSON:

1. Map each requirement to a platform capability layer:
   - designer surface ownership: form designer, list designer, form settings, permission designer, or flow designer
   - app/group/form/field/DDL
   - list views, tabs, filters, buttons, import/export, QR/print buttons
   - related records, data fill, data linkage, related lists
   - child tables, summaries, formula calculations, submit validations
   - business rules, scheduled rules, custom-button rules
   - workflow models, node permissions, node buttons, approval actions, signatures
   - print templates and QR label templates
   - DataM views, widgets, dashboards, dashboard sharing
   - plugin notifications/signatures/invoices/SMS/robots
   - role/data permissions, field permissions, tenant system settings, audit
   - external filling/query links, data push, collaboration, custom components
2. For each layer, decide whether the DBA package can carry the configuration, whether tenant-side configuration is required, and what runtime proof is needed.
3. Use live platform UI and source/API evidence when available. A feature is not "implemented" because the current customer app happens to have a similarly named module.
4. Prefer platform-native features over business-module workarounds. For example, use permission settings for data range, plugin/message rules for notifications, DataM/list views for dashboards, and workflow node settings for approvals.
5. Keep project-specific decisions outside the generic platform rules. A project such as 佳俊物流 may provide examples and regression findings, but it must not narrow the skill's understanding of what the platform can do.
6. For design-heavy requests, produce a designer mapping table before changing DBA JSON: requirement, designer entry, DBA object(s), API/source owner, runtime proof. Treat this as the source of truth for implementation scope.
7. Separate the five designer surfaces before judging completion: form designer, list designer, form settings, permission designer, and flow designer. A requirement is incomplete if only fields exist while its native subsystem, such as rule, validation, print, DataM, permission, quick edit, plugin, external link, or flow node, is unconfigured or untested.
8. For every related field, rule, validation, print template, dashboard, permission, and quick-edit configuration, name the expected runtime evidence before editing: selected `_ref_id`, carried values, target data mutation, blocked/allowed submit, visible print values, rendered chart data, hidden/visible field/button, or quick-edit-triggered rule execution.

## Dabei/K6 Capability Evidence Contract

When the target is Dabei/K6/搭贝应用工厂, treat generated metadata as only the first proof layer. A form, rule, workflow, print template, dashboard, or permission setting is complete only at its highest proven evidence level:

- `can_generate`: package JSON, symbol table, fields, DDL, list metadata, stencil/rule/DataM JSON, and local validation are coherent.
- `api_verified`: the target tenant accepted the relevant API call, such as CRUD, rule save/enable, template query, or design setting save.
- `runtime_verified`: real seeded records prove the user-facing behavior: related `_ref_id` storage, field carry-over, target-record mutation, workflow task movement, print rendering, dashboard data, permission visibility, or audit evidence.
- `platform_config_required`: DBA can prepare placeholders, but tenant roles, plugins, workflow publishing, SMS/robot/signature setup, or other admin settings must be configured and retested.
- `not_safe_to_claim`: the behavior has no proven exported sample, is unstable in runtime tests, or is contradicted by source/runtime evidence.

Do not describe a feature as "已完成" for the customer unless it is `runtime_verified`, or the deliverable explicitly says which remaining tenant-side configuration/test is required.

For platform-wide capability research, use these more explicit evidence labels in reports:

- `observed_ui`: a PC/mobile page or setting is visible, but no write or runtime behavior was verified.
- `source_verified`: decompiled source or frontend endpoint snippets identify the service/API owner.
- `api_verified`: the target tenant accepted a relevant API operation and response was captured.
- `runtime_verified`: real UI or seeded data proves the user-facing behavior.
- `platform_config_required`: the platform supports it, but plugins, roles, accounts, tenant settings, external endpoints, or credentials must be configured and retested.
- `not_safe_to_claim`: do not sell it as working yet.

## Source-Derived Platform Invariants

These constraints are derived from the K6/Dabei decompiled services and must be treated as hard generation rules unless a known-good template proves otherwise.

- Import symbol conversion expects symbol placeholders in form identity fields. Keep `form.id == form.formKey`; keep related form references on the same placeholder style where the template uses placeholders.
- Runtime list pages query `tabs` by `appId + formKey` and `tabViews` by `formKey + tabKey`. A form that imports but lacks aligned `tabs`, `tabFieldReference`, or `tabViews` can fail only when the menu is opened.
- Physical data grids query the SQL table named by `form.tableName`; missing `tables[]` DDL or missing field columns will surface later as `对应关联表未生效` or SQL `unknown column` errors.
- Design table creation validates duplicate field names, maximum column-name length, standard database naming, and system-column collisions. Generate platform-style ASCII column names and avoid system columns such as `sys_status`, `sys_create_time`, `data_title`, `summary`, `table_id`, and workflow status columns.
- Child-table components are real physical tables. A `childrenTable` field must have a same-named table DDL and its child fields' columns must exist in that DDL.
- `aboutTable` fields should include helper storage columns such as display value plus `_ref_id` and, when needed, `_ref_child_id`. Text-only references are not a native business relation.
- PolarDB-like sources may use InnoDB-style DDL while older observed packages use MyISAM. Prefer the source template's engine and charset; do not mix engines casually inside one package.
- Ordinary print templates are stored on each `Form` as `stencils[]` and imported into `gen_table_stencil`; do not add top-level `stencils`. A template id must be a symbol placeholder whose symbol entry is `{"t":"COMMON","v":"<uuid>"}`, while `tableId` must point at the form placeholder (`{"t":"FORM",...}`) and `tenantId` should remain `@@{tenantId}`. Inside the stencil `template` JSON string, cell `schema` objects should preserve field placeholders such as `@@{symbols.[n]}` rather than expanding them to symbol-entry objects. App preview can fail with generic `errcode:9999` if newly appended symbols are raw strings instead of `SymbolEntry` objects.
- A Luckysheet print stencil needs browser-runtime sheet metadata, not only static `data`: generate `config`, `visibledatarow`, `visibledatacolumn`, `ch_width`, `rh_height`, and `celldata`. For every merged range, keep `config.merge`, the origin cell's full `mc`, and follower-cell `mc` caches aligned. `config.merge` alone can leave an otherwise valid stencil visually blank.
- A print field for a child-detail row must use the native `childrenTable` schema wrapper with the nested child field. A flattened `childrenField` schema may import but will not repeat actual line records in print output. Bind system creation date to `sys_create_time`, not a synthetic field named `创建时间`.
- Treat an empty print iframe or a preview with no rendered table as a renderer compatibility failure even when the saved stencil JSON is populated. On the observed Dabei renderer, declaration-element templates with a field cell merged across five columns rendered blank. A fully unmerged two-column fallback can render labels while leaving bound values empty. Use a three-column layout instead: label at column 0 and each field-value origin at column 1 merged narrowly through column 2 (`cs=2`), with aligned `config.merge`, origin `mc`, follower `mc`, `celldata`, and runtime sheet metadata. Visually retest every template option with a real record and assert the bound values, not only the table shell, are rendered.

## Project-to-DBA Design Discipline

For "any project" requests, design in this order before writing JSON:

1. **Master data**: customers, suppliers, products/materials, warehouses, employees, departments, dictionaries.
2. **Transaction documents**: orders, inbound/outbound, QC, payments, invoices, tasks, contracts.
3. **Detail lines**: child tables for line items; never flatten important repeating data into numbered text fields.
4. **State tables**: inventory balance, ledger, receivable/payable, progress/status records.
5. **Native links**: `aboutTable` references between documents and master data, plus `_ref_id` payload verification.
6. **Automation**: business rules for ledger/balance/task creation; workflow node settings for approvals; submit validations for required detail rows and stock/amount rules.
7. **Experience metadata**: tabs, list views, buttons, permissions, print templates, dashboards, and seed-data assumptions.

If a requirement cannot be represented with a proven exported sample for a native feature, mark it as a known limitation instead of inventing speculative JSON.

## Association/Relation Contract

For every cross-module relationship, produce an association matrix before generating the DBA JSON:

- source form and source field
- target form and target display field
- stored columns, including display value plus `_ref_id` and `_ref_child_id` when the platform component uses them
- data-fill assignments from target fields back into source fields
- related-list/list-view expectations on both forms
- whether the relation is single related record, multi-related record, child-table relation, or plain text reference

Generation rules:

- Use `aboutTable` or the template's related-record component for real master/detail and document/document links. Plain text numbers are acceptable only as searchable display fields, not as the sole business relation.
- Keep association metadata (`associationOptions`, `relationOptions`, `linkageOptions`, `referenceForms`, `dataFillList`) only when cloned from a known-good package or verified against a platform-created sample. Do not invent deep relation JSON from field names alone.
- When relation metadata is stripped to fix import duplicate-key failures, preserve the actual related-record field columns. Report the relation as "field-level reference only" until runtime selection and `_ref_id` payload storage are tested.
- Seed master data is part of relation testing. A related-record selector can appear empty if customer, supplier, warehouse, product, employee, or order seed records do not exist yet.

## Business Rule Generation Contract

Business rules are the native automation layer for inventory, ledger, finance, task creation, and status propagation. A generated rule is incomplete unless all of these are defined:

- trigger form, trigger event, trigger filters, and enabled/disabled status
- action target form and action type (`INSERT`, `UPDATE`, `DELETE`, or `UPDATE_OR_INSERT`)
- match filters for `UPDATE`, `DELETE`, and `UPDATE_OR_INSERT`
- assignment steps for `INSERT`, `UPDATE`, and `UPDATE_OR_INSERT`
- `elseSteps` for the insert branch of every `UPDATE_OR_INSERT`
- explicit source/target component types for assignments where the platform requires them
- child-table or batch mappings only when cloned from a proven runtime-working sample

Source-derived rule invariants:

- `UPDATE_OR_INSERT` without `elseSteps` can save but fail to create the first target record.
- `UPDATE`, `DELETE`, and `UPDATE_OR_INSERT` require filters; otherwise the rule is unsafe or rejected.
- `INSERT`, `UPDATE`, and `UPDATE_OR_INSERT` require steps; save success without assignments is metadata-only.
- `childSteps`, `batchAction`, or cartesian mappings must be runtime-tested with child rows. The designer may accept the JSON while execution still leaves child-derived fields empty.
- After import, rule validation/save/enable success is not proof of execution. Test the actual data mutation branch, including both the update branch and first-time insert branch for balance-style rules.

## Workflow Generation Contract

Approval workflows must be generated from a platform-created, published workflow template whenever the app must actually start approvals.

Required coherent workflow assets:

- form type, form id/formKey, tableName, workflow status fields, and processKey
- `flowModels` model id, definition id/key, version metadata, and model/form process keys
- `authorityRule` starters, inspectors, monitors, slayers, and role/user references
- `nodeSettings` node ids/names, assignees, field permissions, form/list buttons, submit validations, print/signature settings, and approval actions
- BPMN XML, process image, XML/image file ids, and node ids rewritten together
- workflow buttons and list tabs such as todo, done, started, delegated, drafts when the template uses them

Workflow rules:

- Do not treat a `flowModels` shell as a usable approval. Start-form metadata can load while the real `/api/flow/definitions/<definitionId>/start` still fails.
- Prefer ordinary forms plus business rules for high-risk inventory/ledger mutations unless a workflow sample has been proven to start and execute node actions in the target tenant.
- Report approval forms separately from ordinary CRUD and business-rule flows. A logistics/ERP app can have working inventory automation while imported approval starts still require a platform-authored workflow sample.

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
   - target platform-native behavior: associations, list views, workflow nodes, business rules, validation rules, print templates, data push, and role permissions
   - for Dabei/K6/搭贝应用工厂 targets, read `references/dabei-platform.md` before designing the app structure or judging feature completeness
2. If user has an existing `.dba`, use it as the structural template. If not, explain that output will be a best-effort package.
3. Produce intermediate deliverables before `.dba`:
   - `feature_list.csv`
   - `data_model.md`
   - `association_matrix.md`
   - `business_rules.md`
   - `workflow_plan.md`
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
python3 <skill>/scripts/dba_tool.py validate work/generated_check/app.json --out outputs/generated.validate.json
```

8. Read `outputs/generated.validate.json`. Fix every `issues[]` item before handing over the package. Explain any remaining `warnings[]` as runtime-test risks.
9. Ask the user to import-test the generated `.dba`, or perform the import/runtime test yourself when the user provides platform access. If import fails, request the exact error/log and patch the JSON/package accordingly.

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
7. Run `dba_tool.py validate` after every changed package and fix all `issues[]`.
8. Package and import-test one change set at a time. Name outputs by step, e.g. `v1_add_fields.dba`, `v2_add_form.dba`, `v3_add_workflow.dba`.

## Workflow: Import-Debug Iteration

Use this tighter loop when the user reports that import or runtime failed:

1. Classify the failure:
   - Import failure: `/apps/import`, symbol conversion, duplicate key, invalid metadata.
   - Menu/list runtime failure: `/tab_views/<id>/settings`, `TabGridViewHelper`, blank list page, missing tabs/views.
   - Data-grid runtime failure: SQL table missing, unknown column, bad `sourceId/tableName`, child-table DDL missing.
   - Workflow runtime failure: start-form loads but `/flow/definitions/<id>/start` fails.
   - Rule runtime failure: rule saves/enables but does not create/update target records.
2. Compare the failing package against the last known-good package before deleting metadata.
3. Fix only the failing layer first. Do not strip runtime metadata to solve an import-only duplicate-key error.
4. Repack, unpack, summarize, and validate:

```bash
python3 <skill>/scripts/dba_tool.py pack fixed.json --out outputs/fixed.dba
python3 <skill>/scripts/dba_tool.py unpack outputs/fixed.dba --out work/fixed_check
python3 <skill>/scripts/dba_tool.py summary work/fixed_check/app.json --out work/fixed_check/summary
python3 <skill>/scripts/dba_tool.py validate work/fixed_check/app.json --out outputs/fixed.validate.json
```

5. Ask for backend logs around the exact failing endpoint if local validation passes but the platform still fails.

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
- If logs show `对应关联表未生效` from `DataGridQueryHandler`, treat it as a missing physical table or wrong `sourceId/tableName`, not as a permissions problem. Verify `forms[].tableName`, top-level `tables[]`, and the target database table.
- If logs show SQL unknown-column errors, compare `fields[].columns`, `styleDetail`/view selected fields, and top-level DDL. The field can exist visually but lack a physical SQL column.
- If a workflow form loads metadata but actual start returns `系统繁忙，请稍后重试`, do not report workflow success. Require a platform-created published workflow sample or backend logs.
- If a business rule saves and enables but does not mutate target data, treat save success as metadata-only. Runtime-test both insert and update branches, especially `UPDATE_OR_INSERT` rules and child-table mappings.
- Validation checklist before handing an import-debug `.dba` to the user:
  - `inspect`, `unpack`, and `summary` pass.
  - `validate` has no `issues[]`.
  - `form.id == form.formKey` for every form.
  - every field-bearing form has `tabs`, `tabFieldReference`, `styleDetail`, `addOption`, and `editOption`.
  - `tabFieldReference.formId == form.id`.
  - every `tabs[].formKey` and `tabs[].tabFormKey` equals the form key.
  - every existing `tabViews[].tabKey` matches a same-form `tabs[].tabKey`.
  - intentionally stripped duplicate-key metadata counts are zero.
- Search the generated JSON for old field names, old table names, and temporary plain keys before packaging.
- Treat `errcode: 9999` as insufficient; ask for backend logs around `/apps/import`.

## Runtime Testing After Import

Import success is only the first gate. When platform access is available, use an isolated browser automation session so testing does not disturb the user's browser, then verify the app as an operator would.

Minimum runtime checks:

- Confirm the imported app opens and every module/menu can load its list page.
- For ordinary forms, test `新增 -> 编辑 -> 删除` and capture the API result; successful CRUD should return `errcode: 0` or `success: true`.
- For workflow/approval forms, do not judge them by ordinary edit behavior. Test `新建/发起`, then validate workflow actions separately: approve/handle, reject, transfer, withdraw, archive, or delete according to the target platform behavior.
- Treat `新增` and `新建` as equivalent create-entry labels. Workflow tabs often use `新建` and include views such as `待我办理`, `我已办理`, `我发起的`, and `我的草稿`.
- Fill required select fields during automation. A failed submit with `此项为必填项` usually means the test skipped a dropdown, not necessarily that the package is broken.
- Test at least one cross-module business flow with a shared business number or seed value. Verify the same value is visible across upstream/downstream modules. If records are only text-linked, report that true association/auto-fill rules still need implementation.
- For data grids, open at least one list page per module and watch for table-missing or unknown-column errors. These usually indicate DDL/tableName/field-column mismatch, even if import succeeded.
- For related-record fields, create seed master data first, select a record in the UI, submit, then verify the API payload stores `_ref_id`, not only display text.
- For business rules, verify target records are actually created/updated. Rule import/save/enable success is not proof of execution.
- Match the frontend payload shape when testing rules. A Dabei/K6 single-select `mamselect` is submitted as a one-element array such as `["不合格"]`, not the scalar string `"不合格"`; using a scalar can make an otherwise working condition rule appear broken.
- For workflows, verify actual flow start and at least one task action endpoint, not only the start-form metadata endpoint.

Dropdown/default-value regression checks:

- Scan all `mamselect` and `mamradio` fields for non-empty `options.defaultValue` or `options.value` unless the requirement explicitly needs a default.
- Search latest generated JSON, `styleDetail`, `addOption`, and `editOption` for template residues such as `选项一`, `选项二`, `选项三`, or accidental defaults like `个`.
- If users report dropdowns showing a repeated value such as `个`, inspect cloned template fields first. Clear the default and replace template options with real business options, then retest in the imported app.

Dashboard/DataM regression checks:

- Keep SQL result aliases, view-model keys, and widget column names aligned and limited to letters, numbers, underscores, or ordinary Chinese text. Avoid `%`, `/`, parentheses, and other characters that require identifier quoting: DataM can wrap the configured SQL in an outer query without quoting those aliases, causing `/api/datam/api/view/getData` to fail even though the inner SQL is valid.
- `mamselect` values are stored as JSON-array text. When a custom SQL dashboard reads a single-select column directly, normalize it to display text so the table shows `原料入库` instead of `["原料入库"]`.
- Open every imported dashboard with seeded records, verify visible rows and values, and inspect both the `getData` response and browser console. Dashboard metadata/import success alone is not runtime proof.

Print-template regression checks:

- Use a real record containing every bound master field and at least one child-detail row. Open every template option from the runtime print action, not only the stencil designer or template-list endpoint.
- Inspect the print iframe visually for a rendered table, expected field values, detail rows, totals, and unresolved `${...}` placeholders. A successful stencil query or populated `template` JSON is not proof that clicking `打印` renders content.
- If one template is blank while another from the same form works, compare `sheet.column`, row/column runtime caches, `celldata`, cell-level `mc`, merge spans, and field schema wrapper type before changing form data or template IDs.

Recommended runtime report:

- Package path, imported app name, test date, target URL if relevant, and preserved version values.
- Local validation counts: groups, forms, tables, fields, workflows, button refs, `dataTitle`/`summary`, dropdown residue count.
- Runtime table listing each form and whether create/edit/delete or workflow start/delete passed.
- Known limitations: missing association rules, inventory balance automation, approval-node handling, report aggregation, dashboards, or permissions.

## Local Validation Command

Run this before every handoff:

```bash
python3 <skill>/scripts/dba_tool.py validate work/generated_check/app.json --out outputs/generated.validate.json
```

The validator checks source-derived invariants including:

- invalid symbol indexes
- `form.id` / `form.formKey` mismatch
- missing field-bearing form runtime metadata
- tab and tab-view key mismatches
- missing top-level table DDL
- field columns missing from DDL
- duplicate or non-standard database field names
- system-column collisions
- missing child-table DDL
- missing related-record helper columns
- inconsistent or incomplete association metadata
- incomplete business-rule trigger/action/filter/step metadata
- risky child-table/batch business-rule mappings
- incomplete workflow model/process/node settings metadata
- invalid DataM JSON and unsafe dashboard result aliases that can break the platform's outer SQL

Exported child fields may appear both under `childrenTable.children` and as top-level `childrenField: true` mirrors. Validate mirror columns against the child-table DDL only; do not require them in the main-form DDL. Resolve child-table symbol placeholders before applying database-name checks.

Fix every `issues[]` item. Treat `warnings[]` as explicit runtime-test risks that must be reported.

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

Read `references/dabei-platform.md` when the target platform is Dabei/K6/搭贝应用工厂, or when you need to design platform-native forms, list views, workflow approvals, business rules, submit validations, permissions, or runtime test flows.
