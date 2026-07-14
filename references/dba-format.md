# Observed DBA Package Format

This reference documents an observed `.dba` package shape. It is not an official specification.

## Container

- File extension: `.dba`
- Outer encoding: zlib-compressed bytes
- Decompressed payload: UTF-8 JSON, usually one very long line

Python unpack:

```python
payload = zlib.decompress(Path("input.dba").read_bytes())
obj = json.loads(payload.decode("utf-8"))
```

Python pack:

```python
raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
Path("output.dba").write_bytes(zlib.compress(raw))
```

## Top-Level Keys

Observed package:

```json
{
  "app": {},
  "datamConfig": "... JSON string ...",
  "symbolTable": {
    "doSample": false,
    "symbols": [{"t": "APP|GROUP|FORM|TABLE_NAME|FIELD|COMMON", "v": "..."}],
    "tenantId": "..."
  },
  "tables": [],
  "version": "v1979"
}
```

## Symbol Placeholders

The JSON uses placeholders such as:

```text
@@{symbols.[0]}
```

Resolve by replacing index `n` with `symbolTable.symbols[n].v`.

Common symbol types:

- `APP`: app id/key
- `GROUP`: module/group id
- `FORM`: form id
- `TABLE_NAME`: physical table name
- `FIELD`: field id
- `COMMON`: button id, rule id, relation id, or other internal id

When generating from a template, preserve this placeholder style. When analyzing, always produce a resolved copy for humans.

## App Structure

`app` usually contains:

- `appKey`, `id`, `tenantId`
- `name`, `category`, `icon`, `location`
- `groups`
- timestamps and install/status metadata

Each group contains:

- `id`, `appId`, `name`, `seq`
- `forms`

Each form may contain:

- `id`, `name`, `tableName`, `groupId`, `seq`, `formType`, `status`
- `fields`
- `buttons`
- `flowModels`
- `associationOptions`
- `judgeRules`, `hideRules`, `readOnlyRules`, `linkageOptions`
- `tabs`
- import/export, print, style, reference metadata

Dashboard/report pages may have no `tableName` and no `fields`; details may live in `datamConfig`.

## Field Shape

Observed fields usually include:

- `id`
- `fieldKey`
- `name` (platform field/column name)
- `type`
- `comment` (human label)
- `childrenField`
- `referenced`
- `virtual`
- `seq`
- `options`
- `columns`

`options.editOption` commonly controls:

- `see`
- `must`
- `write`
- `disable`

`columns` maps a field to one or more SQL columns. `aboutTable` typically has base display column plus `_ref_id` and `_ref_child_id`.

## Tables

Top-level `tables` contains entries like:

```json
{
  "ddl": "CREATE TABLE IF NOT EXISTS ...",
  "tableName": "@@{symbols.[n]}"
}
```

Main tables include common system columns and optional workflow columns.

Child tables use `pid` as parent pointer and usually include:

```sql
KEY `<child_table>_pid` (`pid`)
```

## Buttons and Actions

Common buttons:

- base form actions: submit, edit, print, delete, copy, save draft, temp save
- workflow actions: transfer, refuse, send back, cancel
- business actions: terminate, adjust bill, change subject, rename, renew, litigation, supplementary agreement, sign, split, collect, invoice, upload invoice, send SMS

Buttons may include `enableCondition.expression`. Preserve these when cloning flows from a template.

## Workflows

Workflow forms contain `flowModels`. Typical nested keys:

- `authorityRule`
- `form.processKey`
- `nodeSettings`
- `nodeSettings[].buttons`
- `nodeSettings[].flowSubjects`
- `setting`
- `processImage`

Do not hand-roll complex flow syntax when a template is available. Clone a simple working flow and replace IDs/names.

## Compatibility Risks

Generated `.dba` may fail import if the platform validates:

- unsupported `version`
- stale or duplicate IDs
- tenant/app ownership
- component schema drift
- workflow XML/image/config consistency
- missing reference forms
- invalid dashboard config
- plugin-specific fields not generated exactly

Always treat generated `.dba` as an import-test artifact until imported successfully.

## Known Import Error: form id/key mismatch

Observed backend logs:

```text
检测到表单id、key不一致存在:@@{symbols.[2325]},item_category
StringIndexOutOfBoundsException: String index out of range: -13
at cn.k6cloud.app.utils.migrate.symbol.symboltable.SymbolTable.extractSymbolIndex
at cn.k6cloud.app.utils.migrate.app.AppTmplSymbolConverter.resetRefKey
```

Cause: the importer expects `formKey` to be a symbol placeholder and tries to extract the numeric index from it. A plain string such as `item_category` crashes the importer.

Fix:

- `form.formKey` must equal `form.id`, e.g. both `@@{symbols.[2325]}`.
- `form.tabFieldReference.formId` must equal the same placeholder.
- Each `tabs[].tabFormKey` must equal the same placeholder.
