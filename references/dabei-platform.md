# Dabei/K6 Platform Design Notes

Observed from a live tenant on 2026-07-16 and expanded with PC/mobile platform walkthroughs on 2026-07-21. This is not an official specification; treat it as field guidance for building `.dba` packages that behave like native Dabei/K6 apps.

## Platform-Wide Development Rule

Use this file as a platform capability contract, not as a project note. A customer app such as 佳俊物流 is only one implementation sample. For every new project, first map the requirement to the platform layer that owns the behavior, then decide what can be generated in a DBA package and what must be configured or verified in the tenant.

Do not create business modules to replace native platform features unless the user explicitly wants an auditable business record. Examples:

- Use platform role/data permissions, field permissions, list-button permissions, and tenant settings for access control; do not create a "permission strategy" form for normal permissions.
- Use message push, plugin integration, DingTalk/WeCom robots, or SMS plugins for reminders; do not model reminders as passive text fields.
- Use workflow node settings for approvals, node buttons, submit validation, field permissions, signatures, transfer/reject/return, timeout, and batch approval; do not claim approval from a status field alone.
- Use related records, data fill, data linkage, and related lists for master-data carry-over; do not use plain text fields as the only business relation.
- Use DataM dashboards and native list views for analysis/kanban/calendar/Gantt requirements; do not satisfy dashboard requests with static data tables only.
- Use print templates and QR label templates for documents/labels; do not treat an attachment field as a printable template.
- Use external filling/query, data push, collaboration, and plugins for cross-enterprise or external-system interaction.

## Platform Technical Stack and Service Layers

The decompiled `wechat-dump2` source and live UI show a layered low-code platform:

| Layer | Main responsibility | Source/API evidence | DBA implication |
|---|---|---|---|
| PC app factory | App/group/form/dashboard management, app import/export, form design entry | `/factory/#/appManage`, app import UI, app/form cards | DBA can carry app structure, but imported runtime ids must be rediscovered after import. |
| Runtime app | End-user list pages, add/edit/delete, related selectors, print, workflow task entry | `k6-web-service`, `/data_grids`, `/data/record/*`, `/api/web/form/common/data/*` | CRUD/list behavior must be verified with real records and actual runtime ids. |
| Design service | Forms, fields, DDL metadata, tabs/list views, permissions, validation, print stencils, external filling, quick edit, data push | `k6-design-service`, `StencilController`, `ValidateRuleController`, `FormAuthorityController`, `QuickEditController`, `DataPushRuleController`, `DesignExternalFillingController` | Generate metadata only when it matches observed exported shapes; use local validation plus runtime verification. |
| Rule engine | Data-change, scheduled, and custom-button automation | `k6-judge-service`, `/api/judge/design/rule/*`, Easy Rules, MongoDB rule docs | Save/enable success is metadata proof only; target record mutation is required. |
| Workflow engine | Process definitions, task lifecycle, node actions, approval history | `k6-flow-service`, `/processes_start`, flow definitions/start/todo task APIs | Imported workflow shells are risky; real start and node submit are required. |
| DataM BI | SQL views, widgets, dashboards, dashboard sharing | `datam-admin-starter`, `/api/view/*`, `/api/widget/*`, `/api/dashboard/*` | Dashboard JSON must use safe aliases and be opened through runtime dashboard routes with seeded data. |
| Data import/export | Excel import/export staging, file export, adapters for select/date/user/aboutTable values | `k6-data-service` and export services | Template import/export is platform infrastructure; generated forms must keep component storage shapes compatible. |
| Plugin/SNS | Message rules, DingTalk/WeCom robots, SMS, e-signature, invoice plugin actions | `k6-sns-service`, `k6-plugin-service`, marketplace UI | Plugin features are `platform_config_required` until installed/configured and triggered. |
| Unite/system settings | Watermarks, login settings, approval settings, audit logs | `k6-unite-service`, `/admin/audit/*`, watermark models | Tenant-wide configuration cannot be fully delivered by a DBA package. |

Implementation logic:

- Form data is stored in physical relational tables named by `DesignForm.tableName`; field columns and top-level DDL must match.
- Child tables are separate physical tables with parent linkage such as `pid`; they are not JSON blobs inside the parent record.
- Related records store display text plus helper refs such as `<field>_ref_id` and sometimes `<field>_ref_child_id`; text-only copies are not native relations.
- Single-select values are often stored as JSON-array text such as `["合格"]`; API/rule tests must use frontend-compatible shapes.
- Business rules are persisted separately from form metadata and executed asynchronously after data writes publish judge messages.
- Workflow definitions, node settings, BPMN assets, permissions, buttons, and process keys must be coherent together. Start-form loading is not proof of start success.
- Print templates are Luckysheet-like stencil JSON attached to forms and rendered at runtime; saved template JSON is not proof of visible output.
- DataM wraps SQL in generated outer queries; unsafe aliases such as names containing `%`, `/`, parentheses, or punctuation can break runtime.
- System settings, plugin installation, roles, and permission subjects are tenant configuration and must be verified in the target tenant.

## Platform Capability Map

Use this map before designing any project. Each capability must be assigned a proof level from the capability-boundary table below.

| Platform area | Observed capabilities | Implementation approach | Completion proof |
|---|---|---|---|
| App management | Create/import/export apps, app groups, ordinary forms, workflow forms, dashboards, visit runtime app | DBA package app/group/form/dashboard metadata plus platform import | Import succeeds, app opens, every menu resolves to runtime list/dashboard. |
| Form design | Text/number/date/select/radio/checkbox/address/attachment/image/rich text/location/signature/OCR/system fields/related records/child tables/summary/amount uppercase/geofence/embed/AI analysis | Clone component metadata from proven samples and keep DDL aligned | Add/edit one record per important component and inspect stored payload. |
| List design | Tabs, table/gallery/Gantt/floor/calendar/hierarchy/kanban views, filters, fields, grouping, sorting, left tree, buttons, import/export, QR print, batch print, data range | Preserve `tabs`, `tabFieldReference`, `tabViews`, button refs, view settings | List opens, query succeeds, buttons display according to permissions. |
| Related data | Related record, related multi-select, data fill, data linkage, related lists | Use `aboutTable`, helper ref columns, selector `dataFillList`, related-list settings | Select seeded data in UI, verify auto-filled fields and `_ref_id` payload. |
| Formula/validation | New function calculation, formula submit validation, block or warn behavior | Use platform formula/validate-rule metadata cloned from samples | Submit invalid data and confirm block/prompt; submit valid data succeeds. |
| Business rules | Add/update/delete target data, delete child-table trigger, custom button trigger, scheduled/repeating/date triggers, execution logs | Use judge rule JSON with trigger/action/filter/steps/elseSteps and plugin dependencies | Trigger source record; target record is created/updated/deleted as expected. |
| Workflow | Multiple flows per form, starters, node assignees, approval rules, CC, field permissions, buttons, submit validation, transfer/reject/return, temp save, add-sign, timeout, signature, batch approval, publish/version management | Prefer platform-created workflow samples; rewrite ids/process keys/BPMN coherently | `POST start` creates process/todo; at least one node action succeeds and audit/task state changes. |
| Print/QR | Multiple print templates, sync form style, operation records, QR labels, batch/QR print | Form `stencils[]`, QR stencil metadata, Luckysheet runtime caches | Runtime print action renders field values, child rows, totals, QR/labels. |
| Dashboards/DataM | SQL/data views, widgets, dashboards, chart/table rendering, sharing | DataM views/widgets/dashboard JSON with safe aliases and synchronized model keys | Open runtime dashboard via menu/`#/dashboard/<id>`; `getData` succeeds and charts show seeded values. |
| Plugins/messages | Message push, plugin integration, DingTalk robot, WeCom robot, e-signature, invoice plugin, SMS | Message rules, judge plugin actions, plugin parameter mapping | Plugin installed/configured; trigger produces notification/signature/invoice/SMS evidence. |
| Permissions/security | Role authorization, form/list button permissions, data permissions, field permissions, data range, watermarks, export/print/image watermarks, login methods, audit | Platform permission pages and tenant system settings | Test with each role/account; audit shows operations; unauthorized fields/buttons/data hidden. |
| External/collaboration | External filling, public/password query, data sharing, data push, upstream/downstream collaboration, custom components | External filling settings, push rules, collaboration settings, custom component registry | External link or endpoint works with expected field permissions and payload. |
| Mobile runtime | Workbench, task center, all apps, my account/quotas, common forms/flows, app form list | Same app metadata plus mobile layout settings | Mobile page shows app/forms/tasks; create/handle key records on mobile when required. |

## What Can Be Implemented Reliably

Use these categories when answering "can this be done?"

- **Reliable in DBA package when cloned/validated**: app/group/form/field layout, component metadata, physical DDL, child tables, list tabs/views/buttons, ordinary CRUD forms, basic related-record columns, basic print/DataM JSON shape, basic workflow shells from proven exports.
- **Feasible but must be runtime verified**: data fill after selecting related records, child-table save/query, business-rule mutations, inventory/ledger/balance automation, workflow start and node handling, print rendering, DataM chart data, quick edit triggering validations/rules, external links.
- **Requires tenant/platform configuration**: roles/users/data range by account, watermarks, login methods, plugin installation and credentials, SMS/robot/e-signature/invoice plugins, cross-tenant import strategy, system-wide approval phrases, page size/export settings.
- **Not safe to claim from DBA alone**: legal-grade e-signature, SMS delivery, role isolation across multiple accounts, workflow reliability, dashboard correctness, child-table rule fan-out, OCR recognition quality, external-system integration, bulk import templates, or multilingual runtime switching unless the exact tenant feature is configured and tested.

## Project Design Pattern

For any business system on Dabei/K6:

1. Convert requirements into platform capabilities first, then into forms.
2. Keep master data and transaction documents separate, but use native related records to connect them.
3. Use one physical form/table for a unified business entity when the platform can distinguish types with fields. Example pattern: product and material can share one `产品物料档案` with a type field, while BOM child rows select only type `物料`.
4. Use child tables for document lines and BOM lines; use separate ledger/balance/state forms only when downstream querying/reporting needs them.
5. Use business rules for system-generated downstream records, and include a verification case for every rule branch.
6. Use workflow only for human approval/task movement; keep high-risk stock and ledger mutation in ordinary forms/rules unless workflow execution has been proven.
7. Use submit validation for required details, duplicate document numbers, amount/stock constraints, and exception completeness.
8. Use DataM dashboards for KPI/chart requirements and native list kanban/calendar/Gantt for operational views.
9. Use print templates for all documents the user expects to print; attachment upload is only archive storage.
10. Put permissions and data isolation into platform settings and role tests, not business tables.

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

## Capability Boundary Levels

When designing or reviewing a Dabei/K6 `.dba`, classify every requested feature by implementation confidence. This prevents saying "built" when only a form or field exists.

| Level | Meaning | Acceptable evidence |
|---|---|---|
| `can_generate` | The DBA package can carry the metadata and local validation can check it. | Valid app JSON, aligned symbols, DDL, fields, tabs, stencils, rule JSON, or DataM JSON. |
| `api_verified` | The target tenant accepted the relevant API and returned success. | Saved/enabled rule response, CRUD response, template query response, or design setting response. |
| `runtime_verified` | The actual user-facing workflow works with real records. | Browser or API test showing target record mutation, `_ref_id` storage, workflow task movement, print rendering, dashboard data, or audit logs. |
| `platform_config_required` | DBA can prepare fields/placeholders, but final behavior depends on tenant-side settings, plugin installation, roles, or workflow publishing. | Explicit platform configuration checklist and post-config test. |
| `not_safe_to_claim` | The behavior is speculative, unstable, or absent from proven samples. | Report as a limitation until a platform-created sample or runtime proof exists. |

For customer-facing status, use the highest proven level only. A form with fields is `can_generate`; a saved rule is at most `api_verified`; "complete" requires `runtime_verified`.

## Source-Verified Architecture

The `wechat-dump2` decompiled services confirm these platform boundaries:

- `k6-web-service` is the runtime data engine. Form records are stored in relational physical tables named by `DesignForm.getTableName()`, and CRUD uses SQL operations such as `AddRecordOperation`, `DataGridRecordOperation`, `DeleteRecordOperation`, and `PrintRecordOperation`.
- `k6-design-service` is the design-time metadata source for forms, fields, tabs, buttons, permissions, validation rules, linkage, association, push rules, external filling, quick edit, and data relation.
- `k6-judge-service` stores rules in MongoDB and runs them through Easy Rules. Data writes in web-service publish judge messages to the `dsp_to_judge` route; rule save/enable is separate from runtime execution.
- `k6-flow-service` stores process definitions/tasks in MongoDB and supports start, todo, done, transfer, add-sign, reject, return, revoke, cancel, urge, and approval comments. A usable imported workflow requires coherent model, definition, node, authority, button, and BPMN assets.
- `datam-admin-starter` owns BI dashboards. Its SQL converter wraps configured SQL in outer `select ... from (...) tN` queries; unsafe aliases can break runtime even when inner SQL is valid.
- `k6-data-service` is Excel import/export/print-file infrastructure, not the BI engine. It stages large exports and converts values through adapters such as select/date/user/aboutTable adapters.

Generation implication: a `.dba` can reliably generate metadata and tables, but actual automation, workflow, print, dashboard, plugin, and permission behaviors require runtime proof.

## Source/API Capability Index

Use this index when researching implementation logic or debugging runtime behavior. Endpoint prefixes can differ behind gateways, but these controller mappings identify the platform owner of each feature.

| Capability | Main source files | Observed mappings / APIs | Development rule |
|---|---|---|---|
| Runtime list/query | `k6-web-service/.../DataGridResource.java`, `DataGridStreamResource.java`, `DataRecordController.java` | `/data_grids`, `/data_grids/quick`, `/stream_data_grids`, `/data/record/form_record`, `/data/record/queryColumnsByIds`, `/data/record/select_record_columns`, `/data/record/range_filter` | Open list pages and query records with imported runtime ids; table/field mismatches surface here. |
| Runtime add/update/delete | `k6-web-service/.../CommonDataResource.java`, data operations | `/api/web/form/common/data/addRecord`, `/api/web/form/common/data/updateRecord`, `/api/web/form/common/data/batch/deleteRecord`, custom button rule trigger | CRUD success plus list回查 is the minimum ordinary-form proof. |
| Related records/data fill | `AssociationServiceImpl`, `AssignValueConverter`, web `BusinessJudgeController` helpers | `/data/businessJudge/formReference`, `/data/businessJudge/data/form/*`, related selector payloads | Verify selected display text plus `_ref_id`/`_ref_child_id`; verify carried fields in submit payload. |
| Print templates | `k6-design-service/.../StencilController.java`, `k6-web-service/.../PrintRecordOperation.java` | `stencils/add`, `stencils/update`, `stencils/table/{tableId}`, `stencils/table/{tableId}/auth`, `stencils/{id}/authority` | Template list/auth success is not enough; click runtime print and inspect visible values. |
| QR labels | `QrcodeStencilController.java`, `CommonDataResource.java` | `qrcodeStencils/add`, `qrcodeStencils/update`, `qrcodeStencils/forms/{formKey}/qrcodeStencilDetail`, `/checkQrcodeStencilLimit`, `/printQrcode` | QR label config must render with real record data. |
| Submit validation | `ValidateRuleController.java`, web `ValidateRuleController.java` | `/validateRule/createValidateRule`, `/validateRule/getValidateRuleByTableId`, `/validateRule/updateValidateRule`, `/data/validate/{formId}/fields` | Test both invalid and valid submissions; formula metadata alone is not proof. |
| Business rules | `k6-judge-service/.../DesignController.java`, `DataController.java`, `TriggerController.java` | `/api/judge/design/rule/tabs`, `/rule/pageQuery`, `/rule/validate`, `/rule/save`, `/rule/handleStatus`, `/send/plugin`, `/data/rule/form_change` | Save/enable only proves design acceptance; target mutation and execution logs prove runtime. |
| Message rules | `k6-sns-service/.../MessageRuleController.java` | `/message/rule/page`, `/message/rule/edit`, `/message/rule/{id}`, `/message/rule/alterStatus` | Message configuration must be triggered and visible; plugin channels require plugin setup. |
| Workflow definitions/tasks | `k6-flow-service/.../ProcessStartResource.java`, form/task resources | `/processes_start`, `/{processId}/cancel`, `/{processId}/urge`, `/history/{processId}`, flow definition start/start_form/buttons/task submit endpoints | Start-form/buttons loading is weak proof; actual start plus one task action is required. |
| Permissions | `FormAuthorityController.java`, auth service integrations | `/form_authorities`, `/form_authorities/{id}`, copy/delete/update subjects, enable/disable | Verify with roles/accounts; do not model permissions as business data. |
| Quick edit | `QuickEditController.java` | `/forms/{form_id}/quick_edit` GET/POST | Confirm whether quick edit triggers validation, data fill, and business rules as configured. |
| External filling/query | `ExternalFillingResource.java`, `DesignExternalFillingController.java`, `DataExternalController.java` | `/_external_fillings/{form_id}`, enable/disable/password/fields/share options, `/external_fillings/{form_id}/records` | Treat external links as configured services; test field permissions and external submission/query. |
| Data push | `DataPushRuleController.java` | `/data/push_rules?form_id=...&method_type=...`, `/_ref_form_ids` | Push rules need target service verification; package metadata alone is not integration proof. |
| Dashboards/DataM | `ViewRest.java`, `WidgetRest.java`, `DashboardRest.java`, `DashboardWidgetRest.java` | `/api/view/getData`, `/api/view/executeSql`, `/api/view/createView`, `/api/widget/*`, `/api/dashboard/*`, `/api/dashboardWidget/*` | Use safe aliases and open dashboard through runtime route/menu with seeded data. |
| Audit | `k6-unite-service/.../AuditAdminController.java`, `AuditApiController.java` | `/admin/audit/page`, `/admin/audit/loginLog`, `/admin/audit/operateLog`, `/admin/audit/formOperateLog` | Use audit as evidence of design operations, login/account tests, and CRUD/rule-trigger results. |
| Watermarks/system settings | `Watermark.java`, `WatermarkHelper.java`, unite system settings | PC routes under `/factory/#/systemConfig/*` | Tenant-level setting; document required config and verify export/print/image effects. |
| Plugins | `k6-plugin-service`, judge plugin action mappers, marketplace UI | Plugin action validation, plugin push data endpoints | Plugin action can be blocked if plugin is missing; mark as `platform_config_required` until configured. |

## Observed PC/Mobile Routes

Use real routes discovered from the platform UI, not guessed hashes:

- PC app factory: `/factory/#/appManage`.
- Plugin management: `/factory/#/pluginManage`, with tabs `我的插件` and `插件市场`.
- Process management: `/factory/#/processManage`; direct `#/flowManage` did not render in the observed tenant.
- Data factory: `/factory/#/shujuyingyong/model`.
- Extension/component management: `/factory/#/extendDevelop/index`.
- System config: `/factory/#/systemConfig/watermarkManage`, `/approveLanguage`, `/customLogin`, `/sysToConfigure`.
- Audit: `/factory/#/operationalAudit/loginLog`, `/designRecord`, `/operationRecord`.
- Runtime mobile/workbench: `/development/#/home/workbench`, `/home/approval`, `/home/apps`, `/home/user`.
- Runtime app form: `/dsp_base_app/index.html?sys=<sysId>#/container/<formId>?sys=<sysId>&id=<formId>`.
- Runtime dashboard: prefer menu click or `#/dashboard/<dashboardId>`; direct `#/container/<dashboardId>` can render blank for dashboards.
- Form designer: `/design/#/home?sysId=<sysId>&menusId=<formId>&formType=<0|1>&designType=0`.
- List designer: `/design/#/formlist?...`.
- Form settings examples: `/design/#/formsetting/field-permission?...`, `/formsetting/link-list`, `/formsetting/print-list`, `/formsetting/business-rule`, `/formsetting/submit-check`, `/formsetting/message-push`, `/formsetting/form-export`, `/formsetting/qrcode-set`, `/formsetting/data-push`, `/formsetting/data-edit`, `/formsetting/plugin-integration`, `/formsetting/data-cooperate`.

## Capability Matrix for Logistics/ERP DBA Generation

| Requirement type | What DBA can usually generate | Runtime proof required before calling complete |
|---|---|---|
| Ordinary master data and transaction forms | Groups, forms, fields, child tables, DDL, tabs, list views, add/edit/delete/import/export buttons. | Open list, add/edit/delete one real record, confirm `errcode:0` or `success:true`. |
| Related-record selection | `aboutTable` fields, display/search fields, helper columns ending `_ref_id` and `_ref_child_id`. | Select seeded master data in UI or matching API payload; query saved record and confirm display value plus refs. |
| Data fill / auto carry-over | `options.dataFillList` cloned from proven selector structure. | Select a customer/product/supplier/order and verify filled fields in form and submitted payload. |
| Child table storage | `childrenTable`, child DDL, `pid`, child field columns, print/query relation by parent id. | Save a parent with multiple child rows and query child table rows by `pid`. |
| Child row to target-row automation | Rule metadata may support `INSERT_CHILD`, `DELETE_CHILD`, `batchAction`, `descartesAction`, and `childSteps`. | Must create a document with child rows, then query target rows and confirm each child-derived field is populated. Do not infer from save success. |
| Main-form business rules | Judge rule JSON with trigger type, filters, action type, steps, enabled status. | Create/update/delete source record and query target form; inspect rule execution records if available. |
| Inventory balance upsert | `UPDATE_OR_INSERT` action with match filters, update steps, and insert `elseSteps`. | Test first inbound creates one balance row; second inbound updates same row. |
| Submit validation / duplicate checks | Design validation rules and field `noRepetition` when represented by a proven package. | Submit invalid data and confirm it blocks or prompts as intended. |
| Workflow approvals | Workflow form shell plus model/definition/node settings/buttons/BPMN/authority metadata cloned from a proven sample. | `start_form` and buttons loading are not enough. `POST start` must create a process/todo, and at least one node action must complete. |
| Print templates | `Form.stencils[]` with Luckysheet metadata and schema bindings. | Runtime print action renders nonblank output with field values, child rows, totals, approval comments if used, and no unresolved placeholders. |
| Dashboards | DataM config, view SQL, widgets, safe aliases. | Open dashboard; verify charts/tables show seeded data and `getData` has no SQL/component errors. |
| Message/SMS/robots | Rule or push metadata and plugin action placeholders. | Plugin installed and configured; trigger action creates a send record or visible notification. |
| Permissions/data range | Role, field, button, list, and data-range settings when preserved from platform metadata. | Log in as each role or use operation/data-range evidence; verify visibility and disabled buttons. |

## Source-Verified Rule Constraints

The judge-service validator enforces these constraints and DBA generation should treat them as hard rules:

- `UPDATE`, `DELETE`, and `UPDATE_OR_INSERT` actions require non-empty filters.
- `INSERT`, `UPDATE`, and `UPDATE_OR_INSERT` actions require non-empty steps.
- `UPDATE_OR_INSERT` requires non-empty `elseSteps`; otherwise first-time insert behavior is incomplete.
- Trigger conditions require field name, component type, field value, and operator, and duplicate trigger fields are rejected except date-range start/end special cases.
- Plugin actions such as DingTalk robot, WeCom robot, and SendCloud SMS are validated against installed plugin action config; missing or unavailable plugins block enabling.
- Rules that target workflow forms need a process definition key unless explicitly configured for all definitions.
- The engine performs deep/cycle checks. Cross-form rules can be rejected when they create a trigger loop.

DBA packages should therefore include a rule contract for every rule: trigger form/event/filter, target form/action, filters, steps, elseSteps, continue-trigger behavior, plugin dependencies, and runtime test cases.

## Source-Verified Print Constraints

`PrintRecordOperation` confirms that print data retrieval can include:

- main-form records selected by ids
- child-table rows queried by `pid`
- workflow progress and approval comments/signatures
- current printer and print time
- system creation date
- field visibility filtering according to permissions
- aggregate values from the default list view

This means the data layer can support rich contract, invoice, packing, customs, label, and approval prints. The fragile layer is the template renderer: Luckysheet metadata, merges, cell schema wrappers, and child-table schemas must be runtime tested.

## Source-Verified Association Constraints

`AssociationServiceImpl` and `AssignValueConverter` show these behaviors:

- Related-record queries read `aboutTableInfo.aboutFormKey`, target field keys, selected search fields, filters, and sort options.
- References to target child-table fields join the target child table to the target main table by `pid`.
- Assignment conversion can populate normal values, select-array text, user/org names, aboutTable display values, `_ref_id`, and `_ref_child_id`.
- For child-table references, `_ref_id` can refer to parent id and `_ref_child_id` to child id.

Therefore, generated relations must not be text-only. Keep display columns plus ref columns, and test both main-form and child-form relation payloads.

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

Observed import entry on the PC app factory/application management page on 2026-07-21:

- Click `新建应用`.
- In the first modal, click the `创建空白应用` card.
- In the second modal, switch from `新建应用` to `导入应用`.
- Import mode supports `创建新应用` and `覆盖原应用（会清空目标应用的业务数据）`.
- Upload accepts `.dba` and `.dbt`.
- `创建新应用` explicitly says it creates a new application and does not affect existing apps.
- If using `覆盖原应用`, warn the user because target app business data will be cleared.

App management observations from 2026-07-21:

- Left side lists applications; right side lists the selected application's groups, forms, and dashboards.
- The selected app can expose ordinary forms, workflow forms, and dashboards in the same group list.
- Common page actions include `访问应用`, `新建分组`, `分组排序`, type filter, and form/dashboard search.
- The `访问应用` route is the reliable way to discover runtime `sysId` and runtime form/menu ids after import.

System/platform management observations from 2026-07-21:

- Watermark settings support system-page watermark, exported-document watermark, print watermark, and attachment-image watermark. Content can include current user, company short name, custom content, and dates, with font/color/size/rotation/tile settings.
- Approval settings include auto-open next todo after approval, overdue color display, task-center quick approval buttons, agree/reject display, approval sorting, and approval phrases.
- Custom login page supports preset backgrounds and custom background images.
- General settings include mobile title, whether list related-record details can be clicked, max PC list page size 200/500/1000, clear-all button visibility, login methods, attachment preview mode, new function-calculation scope, exported address-component format, mobile floating button visibility, and enterprise-join auto approval/review.
- Plugin marketplace has "my plugins" and marketplace areas. Observed market plugins include DingTalk group robot, WeCom group robot, e签宝 electronic signature, invoice-management plugin, and Sencloud SMS notification. `我的插件` can be empty while `插件市场` still has installable plugins.
- For ERP/logistics requirements, evaluate platform plugins before modeling everything as plain fields: group robots and SMS can support procurement timeout, payment overdue, QC exception, and handoff notifications; e签宝 may support formal electronic-signature scenarios; the invoice plugin may support invoice workflows.
- Data factory exposes data flows, help docs, and new-data-flow entry. Use this for cross-form/external processing research before inventing heavy DBA-side logic.
- Extension development exposes custom components, including form components, form buttons, list buttons, and list items.

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

Important runtime-id detail from 2026-07-21:

- DOM class names on form cards can include a prefixed id-like value, for example class `a7d05...` while the actual runtime form id is `7d05...`.
- Do not infer the real form id from CSS class names alone. Open the runtime form URL and read `#/container/<formId>?sys=<sysId>&id=<formId>`, or enter design from the runtime page's `设计` button.
- The runtime page's `设计` button produced a correct design URL including `sysId`, `menusId`, `formType`, `designType`, `referer`, and `label`.

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

Observed on 2026-07-21:

- If only one list tab exists, the platform warns that the tab will not be shown in the runtime list.
- View styles include table, gallery, Gantt, floor plan, calendar, hierarchy, and kanban. Use these native views when they satisfy the requirement before inventing a separate kanban module.
- List design includes data-range settings, which should be considered together with form permission settings for role-based visibility.

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

Observed 2026-07-21 list page affordances:

- Business-rule page has operation records, a new-version toggle, an "only view enabled rules" filter, and a new-rule button.
- Treat these as design-time controls. They do not prove runtime execution; still run create/update/delete data-flow tests.

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

Observed 2026-07-21:

- The message-push page describes triggers after data changes or after a specific action. Use it for due-date reminders, procurement timeout reminders, finance overdue-payment reminders, and QC exception notices when the package can represent or preserve the rule metadata.

### External Links

Observed capabilities: public query, external form filling, data sharing, link style, public query, password query, displayed content, query fields.

Useful for supplier/customer entry, customer sign-off, and external status query.

### Data Push

Pushes form data to a specified service address after data changes. Use for WMS, finance, customs, or ERP integrations when the target platform has endpoints.

Observed 2026-07-21:

- The data-push page includes a JSON sample action and a create-push-rule action.

### Quick Edit

Enables list-grid editing. It can optionally execute component validation, function calculation, data linkage, data relation, data filling, and business rules. Good for status, price, inventory, and other high-frequency maintenance fields.

Observed 2026-07-21:

- Quick edit can run component validation, function calculation, data linkage, data relation, data filling, and business rules. When enabling it, test that list-grid edits trigger the same downstream automation as full form edits, or report the difference.

### Print Templates

Supports multiple templates and syncing form style to a blank generated template. Important for contracts, inbound/outbound slips, customs docs, and sign-off forms.

Observed 2026-07-21:

- The print-template page describes runtime printing by template style, supports multiple templates, operation records, and creating new templates.
- For forms created with the table designer, the platform may auto-create a blank print template that can synchronize the form style.
- If runtime `打印` opens an empty view, first inspect whether a template exists, whether it was synchronized, whether the print action is bound to the expected template, and whether field schema bindings are renderer-compatible.

Observed print-renderer constraints from 佳俊物流 testing on 2026-07-20:

- A stencil that saves and is returned by the authorized-template API can still preview as an empty `about:srcdoc` iframe. Treat this as a renderer failure and verify it from the runtime `打印` action with seeded data.
- Luckysheet print layout requires `config`, visible row/column offsets, total width/height, and `celldata`. For a merge, emit the range in `config.merge`, the full `mc` record on the origin cell, and origin references on the covered cells.
- For a repeating child table, the print cell schema must be a `childrenTable` wrapper carrying the nested child-field schema. The ordinary flattened `childrenField` representation does not produce repeatable rows.
- The observed declaration-element renderer failed when value cells were merged across five columns. Use a normal two-column label/value layout with no merges for this document type if that failure recurs; preserve all field bindings and borders.

## Permission Settings

Observed permissions page:

- Select role and authorize.
- Create role and authorize.
- Authorization records.
- Columns include role name, form-button permissions, list-button permissions, data permissions, authorized users.

Design guidance:

- Permissions are not only field permissions. Include list buttons, form buttons, data range, and users/roles.
- A logistics/ERP-style app should at least consider admin, sales, procurement, warehouse, QC, finance, shipping/docs, production, and read-only/audit roles.
- Do not create a business module named "permission strategy" unless the customer explicitly needs a business record of permission requests. The platform already provides role authorization, form-button permissions, list-button permissions, data permissions, field permissions, and data range settings.

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

Observed 2026-07-21 from a sales-contract workflow form:

- The workflow-form design page states that one form can have multiple independent flows with different starters and business nodes.
- Flow-card management exposes starter-field configuration, close flow, create flow, starter settings, operation records, basic information, flow design, flow copy, flow versions, flow disable, and flow delete.
- The workflow canvas shows validate and publish controls. Do not publish during inspection unless explicitly requested.

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

PC/mobile platform walkthrough findings from 2026-07-21:

- PC operation audit has three useful verification pages:
  - Login logs: login person, login time, login platform, IP, location, result.
  - Design records: operator, time, app, menu, operation description, result; useful for tracing app/form/rule/template changes.
  - Operation records: operator, time, app, menu, operation description, result; useful for proving CRUD/test data mutations occurred.
- Mobile/workbench URL shape: `/development/#/home/workbench`.
- Mobile home includes AI assistant, global search, todo/handled/started/draft/informed entries, common forms, and my apps.
- Mobile task center includes todo, suspended, handled, started, drafts, delegated, informed, common flows, and app-grouped flows.
- Mobile "all apps" lists imported apps and can enter an app's form list.
- Mobile "my" shows account/package quotas such as users, AI tokens, attachment usage, data flows, business rules, total records, data lookup, and OCR.
- Mobile app form list shows ordinary forms, workflow forms, and dashboards together under app groups. When testing mobile support, open the latest imported app and verify the same modules appear as on PC.

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
