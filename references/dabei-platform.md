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

### Business Rules

Observed description: after current-form data changes, automatically add, update, or delete data in other forms.

Use business rules for:

- Inbound/outbound documents generating inventory ledger records.
- Inbound/outbound documents updating inventory balances.
- Sales orders creating procurement/production/finance/shipping tasks.
- Quality exceptions creating handling tasks.

When business rules are not configured, report cross-module flows as text-linked only.

### Submit Validation

Observed description: during submit, data that does not satisfy validation rules is blocked or warned.

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

DBA workflow guidance:

- Do not treat a workflow as only a `flowModels` shell. Node permissions, node buttons, validators, and assignee rules determine real behavior.
- Clone a known-good workflow and update IDs, form references, definition IDs, XML/image IDs, and button references consistently.
- Runtime tests for workflow forms should cover start/new, handling/approval, reject, return, transfer, withdraw/delete, and archive where supported.

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
- Dropdowns showing `个` or `选项一/二/三` usually indicate cloned-template defaults/options. Clear `options.defaultValue` and `options.value`, and replace options with business values.

## Logistics/ERP Design Implications

For apps like 佳俊物流:

- Prefer related records for customer, supplier, product, material, order, warehouse, and batch references.
- Use business rules for inventory ledger and inventory balance changes.
- Use submit validation for stock, amount, uniqueness, and exception completeness.
- Put approval logic in flow-node settings, not only form-level settings.
- Use print templates for contracts, inbound/outbound slips, customs docs, and sign-off forms.
- Use external links for supplier/customer collaboration only when the business requires external entry/query.
- Report dashboards should ideally be list/statistic/kanban/calendar style, not plain static tables unless the platform lacks a better exported representation.
