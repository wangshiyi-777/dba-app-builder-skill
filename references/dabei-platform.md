# Dabei/K6 Platform Design Notes

Observed from a live tenant on 2026-07-16. This is not an official specification; treat it as field guidance for building `.dba` packages that behave like native Dabei/K6 apps.

## Mental Model

Do not model the platform as only forms, fields, and SQL tables. A usable app is closer to:

```text
app/group
  -> form model
  -> field/layout model
  -> list views and tabs
  -> form settings
  -> permissions
  -> workflow versions and nodes
  -> business rules, validation, messages, links, print, and push integrations
```

For generated packages, "imports successfully" is weaker than "works like a platform-native app." Feature completeness should include runtime lists, buttons, rules, workflow actions, and data flow.

## Factory/App Management

The factory side navigation observed:

- App management: applications, groups, ordinary forms, workflow forms, app export, form export, form design.
- Plugin marketplace: installed/available plugins.
- Process management: workflow assets and versions by type.
- Data factory: data flows.
- Extension development: component management.
- System configuration: watermark, approval settings, custom login page, general settings.
- Audit: login logs, design records, operation records.

Form card actions are hidden under the card's three-dot menu:

- Rename/change icon.
- Design form.
- Export form.
- Delete form.

App menu actions include rename/change icon, export app without business data, and uninstall app.

Observed import entry on the workbench home page:

- Click `新建应用`.
- In the first modal, click the `创建空白应用` card.
- In the second modal, switch from `新建应用` to `导入应用`.
- Choose `创建新应用`, upload the `.dba` file, optionally rename the app, then confirm.
- This path is distinct from direct app-management import flows; automation should follow the visible two-step modal when starting from the home page.

## Designer URLs and Form Types

Observed designer URL shape:

```text
/design/#/home?sysId=<appSysId>&menusId=<formId>&formType=0&designType=0
```

- `formType=0`: ordinary form.
- `formType=1`: workflow form.
- Runtime form URL shape:

```text
/dsp_base_app/index.html?sys=<sysId>#/container/<formId>?sys=<sysId>&id=<formId>
```

Design tabs:

- Form design.
- Flow design.
- List design.
- Form settings.
- Permission settings.

## Component Inventory

Observed form-design component groups:

- Basic: single-line text, number, address, multiline text, radio, checkbox, attachment, image, date, single select, multi select, switch, description, rich text, location, handwritten signature, divider, OCR.
- System: approval opinion, serial number, user single/multi, department single/multi, organization single/multi, upstream/downstream company, update time, unique ID.
- Advanced: related record, related multi-select, child table, summary child table, summary, uppercase amount, geofence.
- Custom: tabs, embed, AI analysis.

Mapping guidance:

- Prefer `aboutTable`/related-record components for real business flow instead of plain text fields.
- Use child tables for line items. Do not flatten important line items into repeated text fields.
- Use system workflow fields/components only when cloned from a known-good workflow template.

## Form Properties

Observed form-level properties:

- Group name and form icon.
- Label position: left, right, top.
- Form width: `1000px`, `80%`, `100%`.
- Mobile form layout: vertical or horizontal.
- Mobile list layout: normal or simple.
- New function-calculation switch.
- Advanced settings.
- Physical table name.

DBA implications:

- `styleDetail` must reflect layout, label position, widths, and full-width fields such as attachments, dividers, and child tables.
- `tableName`, field column names, top-level `tables[].ddl`, and symbol placeholders must stay aligned.

## List Design

List design controls runtime usability, not only visible columns.

Observed settings:

- Tabs such as all data, drafts, workflow todo/done/started/delegated.
- List fields and filter conditions.
- View styles: table, gallery, Gantt, floor plan, calendar, hierarchy, kanban.
- Grouping, sorting, default sort field/direction, multi-field sorting.
- Left tree and left-tree settings.
- Operation column, checkbox column, header search, wrapping headers.
- Mobile submitter info.
- Data range.
- List buttons: add/new, delete, import, export, QR print, batch print.

DBA implications:

- Preserve or rebuild `tabs`, `tabFieldReference`, and compatible `tabViews`; these are runtime-list metadata, not disposable import metadata.
- Ordinary forms usually expose `新增`; workflow forms may expose `新建`.
- A package can import yet fail at runtime if list metadata is missing or points at stale tab keys.

## Form Settings

### Field Permissions

Controls visibility, writability, and requiredness. Add-data permissions and view/edit permissions are separate. In DBA packages, this touches `addOption`, `editOption`, and workflow-node field permissions.

### Related Lists

When the current form is referenced by another form's related-record field, related lists allow quick viewing/creation of linked data. Use this for native cross-module navigation instead of text-only linking.

Observed route: `#/formsetting/link-list`.

If the current form is not referenced by any `aboutTable` or multi-related field, the page can show that no related-list setup is needed. Do not expect related lists to become useful until real related-record fields exist.

### Data Fill / Data Linkage

Observed from the 华利安 ERP reference package: a working related-record selector can carry field-fill mappings in the selector field's `options.dataFillList`. This is separate from root-level `associationOptions` and from the related field's display/search configuration.

Observed `dataFillList[]` item shape:

- `aboutTableField`: source field model/name on the selected related record.
- `aboutType`: source component type, such as `maminput`, `mamselect`, `digitalformat`, or `aboutTable`.
- `aboutTablePlugin`: object with `model` and `type` for the source field.
- `currentTableField`: target field model/name on the current form.
- `currentType` and `currentFilltype`: target component type.
- `currentTableChidlrenTableModel`: empty for main-form targets; set to the child-table model/name when filling a child-row field.
- `aboutTableChildrenTableModel`: empty when the source is a main-form field.
- `id`, `key`, `tKey`, and `tcKey`: opaque stable ids/keys; cloned/generated packages should keep them unique per mapping.

Generation guidance:

- Add `dataFillList` only to the selector that triggers the fill, not to every filled target field.
- For child-table selectors, add the mapping to the child field inside `childrenTable.children`; if the package also keeps flattened `childrenField` entries in `form.fields`, keep both copies aligned.
- Use this for safe master-data fill cases such as product/material selection filling code, specification, unit, material, price, packing, customs, or declaration fields.
- Do not claim runtime success from `dataFillList` metadata alone. Import and create seed master data, select a related record in the UI, then verify the filled values appear in the submitted payload.

### Business Rules

Observed description: after current-form data changes, automatically add, update, or delete data in other forms.

Observed route: `#/formsetting/business-rule`.

Observed new-rule trigger options:

- Data-change triggers: add data, update data, delete data, delete child-table data, custom button.
- Scheduled triggers: repeating schedule, one-time schedule, and form-date-field cyclic trigger.
- Trigger filters can be added.
- The rule editor includes simple mode, operation logs, execution logs, and save.

Use business rules for:

- Inbound/outbound documents generating inventory ledger records.
- Inbound/outbound documents updating inventory balances.
- Sales orders creating procurement/production/finance/shipping tasks.
- Quality exceptions creating handling tasks.

When business rules are not configured, report cross-module flows as text-linked only.

Design every rule as a contract, not as a loose JSON block:

- trigger form/event/filter
- target form/action type
- update/delete/upsert match filters
- insert/update assignments
- upsert `elseSteps`
- source and target component types
- child-table/batch behavior with a runtime proof case

DBA caution: do not invent full business-rule JSON without a hand-created exported sample from the target tenant or a structurally similar package. It is safer to generate the forms and related fields first, then reverse engineer one minimal saved rule such as "inbound order add -> add inventory ledger."

Observed rule APIs on 2026-07-16:

- `POST /api/judge/design/rule/tabs?formId=<formId>&formType=<0|1>` lists rule tabs.
- `POST /api/judge/design/rule/pageQuery` lists rules for a form.
- `GET /api/judge/design/rule/<ruleId>` returns full rule detail, including `actions[].steps`, `actions[].childSteps`, `isBatch`, `batchAction`, and `status`.
- `POST /api/judge/design/rule/validate` validates basic trigger metadata before save.
- `POST /api/judge/design/rule/save` creates or updates a rule.
- `POST /api/judge/design/rule/handleStatus` enables or disables a rule. Body shape is `{"id":"<ruleId>","status":"ENABLED"}` or `{"id":"<ruleId>","status":"DISABLED"}`.
- `GET /api/judge/design/rule/limit/validate` is called before enabling or saving in the designer.

Observed minimal rule schema:

- Rule root includes `name`, `appId`, `formId`, `formKey`, `formName`, `processDefinitionKey`, `triggerType`, `updateType`, `triggers`, and `actions`.
- For a target-form insert action, `actions[].steps[].fieldName` is the target field name, `fieldValue` is the trigger/source field name when `assignType` is `TRIGGER_VALUE`, and `componentTypeCode`/`fieldValueComponentTypeCode` should match the platform component names such as `maminput`, `mamselect`, `digitalformat`, `date`.
- Related-record target fields may include `fieldNameComponentAboutTypeCode: "aboutTable"` and source related fields may include `componentAboutTypeCode: "aboutTable"`.
- A saved rule is disabled by default unless `handleStatus` is called.

Observed `UPDATE_OR_INSERT` caveat from 佳俊物流 v8 testing:

- `actions[].steps` alone is not enough for first-time insert behavior.
- A structurally valid imported rule with `UPDATE_OR_INSERT`, `steps`, and `filters` can update or appear enabled but fail to create the first balance row when no matching target record exists.
- The platform-created 华利安 ERP sample includes `actions[].elseSteps` on `UPDATE_OR_INSERT`; these map fields for the insert branch.
- When generating inventory-balance rules, set `elseSteps` to the fields required to create a new balance row, typically product/material, warehouse, stock type, current stock via `ADD_UP`, and last-change date. Keep `filters` aligned to the same match keys.
- Runtime test must verify both branches: first inbound creates one balance row; second inbound for the same material/warehouse updates that same row rather than inserting a duplicate.

Important runtime caveat from 佳俊物流 testing:

- The platform accepted `isBatch: 1`, `childSteps`, and `batchAction` payloads that referenced child-table fields, and `GET /api/judge/design/rule/<ruleId>` returned those structures.
- Runtime testing showed that accepted JSON did not prove execution correctness. Three probes generated inventory ledger rows from an inbound document, but the ledger only received main-form fields such as source document and inbound type; child-table fields such as product/material, quantity, and unit remained empty.
- Therefore, do not claim "child table line items generate one ledger row per line" based only on rule-save success. Require a runtime test that creates a document with child rows and then queries the target form to verify every expected child-derived field is populated.
- If child-table line-item automation is required, either obtain a proven platform-created sample where runtime execution maps child rows correctly, or report the gap explicitly and avoid packaging speculative `childSteps` as a completed feature.

### Submit Validation

Observed description: during submit, data that does not satisfy validation rules is blocked or warned.

Observed route: `#/formsetting/submit-check`.

Observed new-validation dialog:

- Uses a formula editor rather than a simple condition table.
- Includes prompt text for failed validation.
- Includes an "only prompt" toggle; when disabled, validation should block submit.
- Formula editor can reference current-form fields and operators.
- Function groups include text, number, date, logic, and advanced functions.
- Observed functions include `LEFT`, `LEN`, `CONCAT`, `VALUE`, `ABS`, `COUNT`, `SUM`, `SUMIF`, `ROUND`, `PRODUCT`, `REDUCE`, `DAYS`, `ADDDAY`, `SYSTIME`, `TODAY`, `IF`, `AND`, `OR`, `CASE`, `ISNULL`, `UUID`, `JOIN`, `LEADER`, and `AVG`.

Typical rules:

- Unique document numbers.
- Non-negative quantity, unit price, amount.
- Outbound quantity cannot exceed stock.
- Payment cannot exceed receivable/payable balance.
- Failed QC requires exception reason and handling method.

### Message Push

Used for notifications after data change or actions. Useful for approval reminders, QC exceptions, and finance/shipping handoffs.

### External Links

Observed capabilities: public query, external form filling, data sharing, link style, public query, password query, displayed content, query fields.

Useful for supplier/customer entry, customer sign-off, and external status query.

### Data Push

Pushes form data to a specified service address after data changes. Use for WMS, finance, customs, or ERP integrations when the target platform has endpoints.

### Quick Edit

Enables list-grid editing. It can optionally execute component validation, function calculation, data linkage, data relation, data filling, and business rules. Good for status, price, inventory, and other high-frequency maintenance fields.

### Print Templates

Supports multiple templates and syncing form style to a blank generated template. Important for contracts, inbound/outbound slips, customs docs, and sign-off forms.

## Permission Settings

Observed permissions page:

- Select role and authorize.
- Create role and authorize.
- Authorization records.
- Columns include role name, form-button permissions, list-button permissions, data permissions, authorized users.

Design guidance:

- Permissions are not only field permissions. Include list buttons, form buttons, data range, and users/roles.
- A logistics/ERP-style app should at least consider admin, sales, procurement, warehouse, QC, finance, shipping/docs, production, and read-only/audit roles.

## Workflow Design

Converting an ordinary form to a workflow has large side effects:

- Existing field permissions become invalid and must be configured on flow nodes.
- Existing business rules are stopped.
- Business rules that target this form are also stopped.
- Submit validation becomes invalid and must be configured at flow nodes.
- Message push rules are reduced to supported reminder types.
- External link switches may be disabled.
- Permission settings need reauthorization.

Workflow-form management supports:

- Multiple independent workflows per form.
- Different starters and business nodes per workflow.
- Drag sorting workflows.
- Starter-field configuration.
- Close flow.
- Create flow.
- Copy flow.
- Flow versions.
- Disable/delete flow.

Workflow canvas observations:

- Node types include handling node and intermediate task node.
- Flow designer has validate and publish actions.
- Node panel includes flow info and node info.
- A selected handling node exposes node name, description, node ID, upstream/downstream, node assignees, CC users, approval rules, field permissions, form-button settings, hang, submit, transfer, reject, return, temporary save, signature, add-sign, timeout, submit validation, signature opinion, transfer scope, batch approval, and handwritten-signature requiredness.
- A workflow form can expose a flow-card management page before entering the canvas. Observed flow-card actions include basic information, flow design, flow copy, flow versions, flow disable, and flow delete.
- The flow canvas palette can include start, handling, end, exclusive gateway, parallel gateway, inclusive gateway, and intermediate task node.

DBA workflow guidance:

- Do not treat a workflow as only a `flowModels` shell. Node permissions, node buttons, validators, and assignee rules determine real behavior.
- Clone a known-good workflow and update IDs, form references, definition IDs, XML/image IDs, and button references consistently.
- Runtime tests for workflow forms should cover start/new, handling/approval, reject, return, transfer, withdraw/delete, and archive where supported.
- Keep approval usability separate from form CRUD usability in reports. A workflow card, definition list, or start-form response is not equivalent to a successful process start.

Observed workflow import caveat from 佳俊物流 v9-v12 testing on 2026-07-17:

- `GET /api/flow/forms/<formId>/definitions`, `GET /api/flow/definitions/<definitionId>/start_form`, and `GET /api/flow/definitions/<definitionId>/buttons` can all return success while the actual start endpoint still fails with `errcode:500` and `系统繁忙，请稍后重试`.
- Do not report an imported workflow as usable until `POST /api/flow/definitions/<definitionId>/start` succeeds and produces a process/todo. Loading the start form is only a metadata check.
- The frontend start body adds `taskSource`, `operatorType: 1`, `source`, `modelId`, and `ignoreValidIds`; include these when reproducing UI behavior, but treat continued 500s as a workflow-engine/model issue that likely requires a platform-created, published workflow sample or backend logs.
- For logistics inventory flows, keep stock ledger/balance mutations on ordinary detail forms when possible. In 佳俊物流 v12, `出库单明细表` as an ordinary form successfully generated one inventory ledger row and deducted inventory balance from 20 to 17, while imported workflow-form starts still returned 500.
- 佳俊物流 v13 confirmed the pragmatic pattern: converting `出库单` from workflow form to ordinary form, while keeping contracts/payment/QC as workflow shells, allowed `出库单 -> 出库单明细表 -> 库存流水 -> 库存余额` to pass runtime testing. The same test imported as a new app, opened 35/35 list pages, passed 8/8 module-level ordinary CRUD smokes, and reduced inventory balance from 14 to 11 after an outbound order. Remaining workflow forms still returned failed actual `/start` probes, so approval usability must be reported separately from inventory-chain usability.

## Runtime Testing Patterns

Ordinary form tests:

- Open list.
- Click `新增`.
- Fill required text, numeric, date, and select fields.
- Submit and expect `errcode: 0` or `success: true`.
- Edit latest record.
- Delete latest record.

Workflow form tests:

- Open list; tabs may include all data, todo, done, started, delegated, drafts.
- Click `新建`.
- Fill required fields and required selects.
- Submit/start flow.
- Continue with workflow-specific actions; do not fail the test just because ordinary edit is absent after flow start.

Automation cautions:

- Required selects must be selected; otherwise validation such as `此项为必填项` is a test-script problem, not necessarily a package problem.
- Reproduce the frontend value shape for `mamselect`: submit a one-element array such as `["不合格"]`. The database stores JSON-array text and judge-rule triggers commonly compare against that array shape; a scalar-string API probe can produce a false rule failure.
- Dropdowns showing `个` or `选项一/二/三` usually indicate cloned-template defaults/options. Clear `options.defaultValue` and `options.value`, and replace options with business values.

DataM dashboard cautions observed during 佳俊物流 v16-v17 testing on 2026-07-20:

- DataM can generate an outer query that references configured result aliases without adding identifier quotes. Aliases such as `完成率%`, `增长率%`, `转化率%`, or `利润率%` therefore caused `/api/datam/api/view/getData` SQL errors even though the configured inner SQL used backticks.
- Use safe result names such as `完成率`, `增长率`, `转化率`, and `利润率`; keep the SQL alias, view `model` key/name/alias, and widget `model`/`cols` name/alias synchronized.
- Direct SQL output of a `mamselect` column exposes storage such as `["原料入库"]`. Normalize single-select text in the SQL view before display, and test with both populated and empty values.
- A dashboard passes only after the runtime page renders actual seeded rows without `组件配置异常` and the browser console/getData response contains no relevant errors.

## Logistics/ERP Design Implications

For apps like 佳俊物流:

- Prefer related records for customer, supplier, product, material, order, warehouse, and batch references.
- Treat plain order/customer/product number fields as weaker than native `aboutTable` links. If the latest generated package has zero related-record fields, cross-module flow is only text-linked even if the same business number appears in multiple forms.
- Maintain an association matrix for each relationship: source field, target form, display field, stored helper columns, data-fill fields, and related-list expectations.
- Use business rules for inventory ledger and inventory balance changes.
- Use submit validation for stock, amount, uniqueness, and exception completeness.
- Put approval logic in flow-node settings, not only form-level settings.
- Use print templates for contracts, inbound/outbound slips, customs docs, and sign-off forms.
- Use external links for supplier/customer collaboration only when the business requires external entry/query.
- Report dashboards should ideally be list/statistic/kanban/calendar style, not plain static tables unless the platform lacks a better exported representation.

## Imported-App Runtime IDs

Dabei/K6 can assign new IDs after importing a DBA package. The IDs in the local package JSON may not match the imported runtime/design URLs.

Automation guidance:

- After import, open the app in app management or runtime and extract the actual `sysId` and form/menu IDs before testing designer pages.
- Do not reuse IDs from local `app_config.json` for browser automation unless you have verified they match the imported app.
- Runtime and designer URLs should be treated as import-instance specific.

## Observed Runtime Validation Findings

Observed on 2026-07-16 while testing an imported logistics app on Dabei/K6:

- A workflow form can successfully start with `/api/flow/definitions/<definitionId>/start`, then expose a pending task in the list and in the global todo badge.
- Pending workflow details can show node actions such as submit, transfer, reject, return, temporary save, suspend, and print. Completing a node can call `/api/flow/processes_todo/tasks/<taskId>/submit` and move `sys_current_task_approval_status` to the completed state.
- Workflow start success does not prove business completeness. A form can start and complete a flow even when important child-table details are empty if node submit validation is not configured.
- Ordinary and workflow forms can save related-record display values plus `<field>_ref_id` and `<field>_ref_child_id`. Runtime tests should inspect the returned `data_grids` payload to confirm the reference id exists, not only that the text appears in the list.
- `aboutTable` selectors may be empty until seed/master data exists. Before judging a relation field broken, create seed customer, warehouse, supplier, product, or order records and reopen the selector.
- Inventory-style apps need explicit business rules. Creating an inbound or outbound document does not automatically create inventory ledger or balance rows unless platform business rules have been configured and exported into the DBA package.
- Child-table business requirements are not guaranteed by field presence. If an inbound/outbound document must contain at least one line, add submit validation at the ordinary form or workflow-node level; otherwise the platform may allow an empty-detail document.

Additional validation checklist for ERP/logistics packages:

- Create seed master data for customer, warehouse, product/material, and supplier before testing downstream forms.
- Verify related fields in API payloads include `_ref_id`, not just display text.
- Submit inbound and outbound documents with and without details; confirm the intended validation behavior.
- After inbound/outbound submission or approval, open inventory ledger and inventory balance forms and check for generated rows.
- For workflow forms, test both flow start and at least one node action. Record the endpoint result and whether todo counts change.
