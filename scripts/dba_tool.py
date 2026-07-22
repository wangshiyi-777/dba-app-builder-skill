#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional


SYMBOL_RE = re.compile(r"@@\{symbols\.\[(\d+)\]\}")


def read_dba(path: Path) -> dict:
    data = path.read_bytes()
    try:
        payload = zlib.decompress(data)
    except zlib.error as exc:
        raise SystemExit(f"not zlib-compressed or unsupported .dba: {exc}") from exc
    try:
        return json.loads(payload.decode("utf-8"))
    except Exception as exc:
        raise SystemExit(f"decompressed payload is not UTF-8 JSON: {exc}") from exc


def read_json(path: Path) -> dict:
    return json.loads(path.read_text("utf-8"))


def write_json(path: Path, obj: dict, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(obj, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    path.write_text(text, "utf-8")


def pack_json(path: Path, out: Path) -> None:
    obj = read_json(path)
    raw = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(zlib.compress(raw))


def symbol_values(obj: dict) -> list[str]:
    symbols = ((obj.get("symbolTable") or {}).get("symbols") or [])
    values = []
    for item in symbols:
        if isinstance(item, dict):
            values.append(str(item.get("v", "")))
        else:
            values.append(str(item))
    return values


def resolve_string(value: str, values: list[str]) -> str:
    def repl(match: re.Match) -> str:
        index = int(match.group(1))
        return values[index] if index < len(values) else match.group(0)
    return SYMBOL_RE.sub(repl, value)


def resolve_any(value, values: list[str]):
    if isinstance(value, str):
        return resolve_string(value, values)
    if isinstance(value, list):
        return [resolve_any(item, values) for item in value]
    if isinstance(value, dict):
        return {resolve_string(str(key), values): resolve_any(item, values) for key, item in value.items()}
    return value


def inspect_file(path: Path) -> None:
    data = path.read_bytes()
    print(f"path: {path}")
    print(f"bytes: {len(data)}")
    try:
        payload = zlib.decompress(data)
    except zlib.error as exc:
        print(f"zlib: no ({exc})")
        return
    print("zlib: yes")
    print(f"decompressed_bytes: {len(payload)}")
    try:
        obj = json.loads(payload.decode("utf-8"))
    except Exception as exc:
        print(f"json: no ({exc})")
        return
    print("json: yes")
    print(f"top_keys: {', '.join(obj.keys())}")
    app = obj.get("app") or {}
    st = obj.get("symbolTable") or {}
    print(f"app_name: {app.get('name', '')}")
    print(f"version: {obj.get('version', '')}")
    print(f"groups: {len(app.get('groups') or [])}")
    print(f"tables: {len(obj.get('tables') or [])}")
    print(f"symbols: {len(st.get('symbols') or [])}")
    print(f"tenant_id: {st.get('tenantId', app.get('tenantId', ''))}")


def unpack(path: Path, out: Path, pretty: bool) -> None:
    obj = read_dba(path)
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "app.json", obj, pretty=pretty)
    resolved = resolve_any(obj, symbol_values(obj))
    write_json(out / "app.resolved.json", resolved, pretty=True)
    print(out / "app.json")
    print(out / "app.resolved.json")


def summarize(json_path: Path, out: Path) -> None:
    obj = read_json(json_path)
    values = symbol_values(obj)
    app = resolve_any(obj.get("app") or {}, values)
    tables = resolve_any(obj.get("tables") or [], values)
    out.mkdir(parents=True, exist_ok=True)

    forms = []
    fields = []
    buttons = []
    workflows = []
    rules = []
    associations = []
    child_table_parent = {}

    for group in app.get("groups") or []:
        group_name = group.get("name", "")
        for form in group.get("forms") or []:
            form_name = form.get("name", "")
            table_name = form.get("tableName", "")
            forms.append({
                "group": group_name,
                "group_seq": group.get("seq", ""),
                "form": form_name,
                "form_id": form.get("id", ""),
                "table_name": table_name,
                "seq": form.get("seq", ""),
                "field_count": len(form.get("fields") or []),
                "workflow_count": len(form.get("flowModels") or []),
                "button_count": len(form.get("buttons") or []),
                "association_count": sum(len(as_list(form.get(key))) for key in ["associationOptions", "relationOptions", "linkageOptions", "referenceForms", "dataFillList"]),
                "judge_rule_count": len(form.get("judgeRules") or []),
                "tab_count": len(form.get("tabs") or []),
            })
            for field in form.get("fields") or []:
                opts = field.get("options") or {}
                edit = opts.get("editOption") or {}
                field_name = field.get("name", "")
                if field.get("type") == "childrenTable":
                    child_table_parent[field_name] = f"{group_name}/{form_name}"
                fields.append({
                    "group": group_name,
                    "form": form_name,
                    "table_name": table_name,
                    "field_name": field_name,
                    "label": field.get("comment", ""),
                    "component_type": field.get("type", ""),
                    "is_child_field": field.get("childrenField", ""),
                    "seq": field.get("seq", ""),
                    "visible": edit.get("see", ""),
                    "required": edit.get("must", ""),
                    "writable": edit.get("write", ""),
                    "db_columns": "; ".join(
                        f"{col.get('name', '')}:{col.get('dbType', '')}({col.get('columnLength', '')})"
                        for col in field.get("columns") or []
                    ),
                })
            for button in form.get("buttons") or []:
                buttons.append({
                    "group": group_name,
                    "form": form_name,
                    "table_name": table_name,
                    "button_name": button.get("name", ""),
                    "component_name": button.get("componentName", ""),
                    "event_type": "|".join(button.get("eventType") or []),
                    "checked": button.get("checked", ""),
                    "base": button.get("base", ""),
                    "click_ref_form_id": button.get("clickRefFormId", ""),
                    "enable_expression": ((button.get("enableCondition") or {}).get("expression", "")),
                })
            for index, flow in enumerate(form.get("flowModels") or [], 1):
                nodes = flow.get("nodeSettings") or []
                starters = ((flow.get("authorityRule") or {}).get("starters") or [])
                workflows.append({
                    "group": group_name,
                    "form": form_name,
                    "table_name": table_name,
                    "workflow_index": index,
                    "process_key": ((flow.get("form") or {}).get("processKey", "")),
                    "node_count": len(nodes),
                    "node_names": " -> ".join(str(n.get("nodeName") or n.get("name") or n.get("taskName") or "") for n in nodes),
                    "starter_auth": "|".join(str(s.get("authName", "")) for s in starters),
                })
            for index, rule in enumerate(form.get("judgeRules") or [], 1):
                actions = as_list((rule or {}).get("actions") if isinstance(rule, dict) else None)
                rules.append({
                    "group": group_name,
                    "form": form_name,
                    "table_name": table_name,
                    "rule_index": index,
                    "rule_name": (rule or {}).get("name", "") if isinstance(rule, dict) else "",
                    "status": (rule or {}).get("status", "") if isinstance(rule, dict) else "",
                    "trigger_type": (rule or {}).get("triggerType", "") if isinstance(rule, dict) else "",
                    "update_type": (rule or {}).get("updateType", "") if isinstance(rule, dict) else "",
                    "action_count": len(actions),
                    "action_types": "|".join(str(a.get("updateType") or a.get("actionType") or a.get("type") or "") for a in actions if isinstance(a, dict)),
                    "has_filters": any(bool(as_list((a or {}).get("filters") if isinstance(a, dict) else None)) for a in actions),
                    "has_steps": any(bool(as_list((a or {}).get("steps") if isinstance(a, dict) else None)) for a in actions),
                    "has_else_steps": any(bool(as_list((a or {}).get("elseSteps") if isinstance(a, dict) else None)) for a in actions),
                    "has_child_steps": any(bool(as_list((a or {}).get("childSteps") if isinstance(a, dict) else None)) for a in actions),
                })
            for meta_key in ["associationOptions", "relationOptions", "linkageOptions", "referenceForms", "dataFillList"]:
                for index, item in enumerate(as_list(form.get(meta_key)), 1):
                    refs = []
                    fields_ref = []
                    if isinstance(item, dict):
                        for sub in flatten_dicts(item):
                            for key, value in sub.items():
                                if key.lower().endswith("formid") or key.lower().endswith("formkey"):
                                    refs.append(str(value))
                                if key.lower().endswith("fieldname") or key.lower().endswith("fieldkey"):
                                    fields_ref.append(str(value))
                    associations.append({
                        "group": group_name,
                        "form": form_name,
                        "table_name": table_name,
                        "metadata_key": meta_key,
                        "index": index,
                        "form_refs": "|".join(sorted(set(refs))),
                        "field_refs": "|".join(sorted(set(fields_ref))),
                    })

    table_rows = []
    comment_re = re.compile(r"COMMENT='([^']*)'")
    column_re = re.compile(r"^\s*`([^`]+)`\s+([^,]+?)(?:\s+COMMENT\s+'((?:[^'\\]|\\.)*)')?,?\s*$")
    for table in tables:
        ddl = table.get("ddl", "")
        table_name = table.get("tableName", "")
        table_comment = ""
        match = comment_re.search(ddl)
        if match:
            table_comment = match.group(1)
        column_count = 0
        sample = []
        for line in ddl.splitlines():
            match = column_re.match(line)
            if not match:
                continue
            col, _typ, comment = match.groups()
            if col.upper().startswith("PRIMARY") or col.upper().startswith("KEY"):
                continue
            column_count += 1
            if comment and not col.startswith("sys_") and col not in {"id", "seq", "pid", "data_title", "summary", "table_id", "data_type", "from_ref_id"}:
                sample.append(comment)
        table_rows.append({
            "table_name": table_name,
            "table_comment": table_comment,
            "parent": child_table_parent.get(table_name, ""),
            "column_count": column_count,
            "business_columns_sample": "；".join(sample[:20]),
        })

    write_csv(out / "forms.csv", forms)
    write_csv(out / "fields.csv", fields)
    write_csv(out / "buttons.csv", buttons)
    write_csv(out / "workflows.csv", workflows)
    write_csv(out / "rules.csv", rules)
    write_csv(out / "associations.csv", associations)
    write_csv(out / "tables.csv", table_rows)

    component_counts = Counter(row["component_type"] for row in fields if row["component_type"])
    group_counts = defaultdict(lambda: {"forms": 0, "fields": 0, "flows": 0, "buttons": 0})
    for form in forms:
        group = form["group"]
        group_counts[group]["forms"] += 1
        group_counts[group]["fields"] += int(form["field_count"])
        group_counts[group]["flows"] += int(form["workflow_count"])
        group_counts[group]["buttons"] += int(form["button_count"])

    md = []
    md.append(f"# DBA Summary\n")
    md.append(f"- App: {app.get('name', '')}")
    md.append(f"- Version: {obj.get('version', '')}")
    md.append(f"- Groups: {len(app.get('groups') or [])}")
    md.append(f"- Forms: {len(forms)}")
    md.append(f"- Tables: {len(tables)}")
    md.append(f"- Fields: {len(fields)}")
    md.append(f"- Workflows: {len(workflows)}")
    md.append(f"- Buttons: {len(buttons)}")
    md.append(f"- Business rules: {len(rules)}")
    md.append(f"- Association metadata rows: {len(associations)}")
    md.append("\n## Groups\n")
    md.append("| Group | Forms | Fields | Flows | Buttons |")
    md.append("|---|---:|---:|---:|---:|")
    for group, counts in sorted(group_counts.items()):
        md.append(f"| {group} | {counts['forms']} | {counts['fields']} | {counts['flows']} | {counts['buttons']} |")
    md.append("\n## Component Counts\n")
    for key, count in component_counts.most_common(20):
        md.append(f"- {key}: {count}")
    md.append("\n## Forms\n")
    md.append("| Group | Form | Table | Fields | Workflows | Buttons |")
    md.append("|---|---|---|---:|---:|---:|")
    for form in forms:
        md.append(f"| {form['group']} | {form['form']} | `{form['table_name']}` | {form['field_count']} | {form['workflow_count']} | {form['button_count']} |")
    (out / "summary.md").write_text("\n".join(md), "utf-8")

    for path in ["summary.md", "forms.csv", "fields.csv", "buttons.csv", "workflows.csv", "rules.csv", "associations.csv", "tables.csv"]:
        print(out / path)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", "utf-8")
        return
    with path.open("w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def iter_strings(value, path="$"):
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from iter_strings(item, f"{path}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            yield from iter_strings(item, f"{path}.{key}")


def parse_ddl_columns(ddl: str) -> set[str]:
    columns = set()
    body_match = re.search(r"\((.*)\)", ddl, re.S)
    body = body_match.group(1) if body_match else ddl
    for match in re.finditer(r"`([^`]+)`\s+(?:varchar|char|text|longtext|int|bigint|double|decimal|float|date|datetime|timestamp|tinyint|smallint|mediumint|json)\b", body, re.I):
        columns.add(match.group(1))
    if columns:
        return columns
    for line in ddl.splitlines():
        line = line.strip()
        if not line.startswith("`"):
            continue
        match = re.match(r"`([^`]+)`\s+", line)
        if match:
            columns.add(match.group(1))
    return columns


def as_list(value) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []


def is_present(value) -> bool:
    return value not in (None, "", [], {})


def pick_first(mapping: dict, keys: list[str]):
    for key in keys:
        if key in mapping and is_present(mapping.get(key)):
            return mapping.get(key)
    return None


def flatten_dicts(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from flatten_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from flatten_dicts(item)


def validate_style_cols(items, scope_label: str, warn) -> None:
    """Dabei designer uses col as row ordinal, not 12-grid offset."""
    if not isinstance(items, list):
        return

    rows = defaultdict(list)
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        columns = item.get("columns")
        if isinstance(columns, list):
            if item.get("type") == "tabs":
                for panel_index, panel in enumerate(columns):
                    if isinstance(panel, dict):
                        validate_style_cols(panel.get("columns"), f"{scope_label}/tabs[{panel_index}]", warn)
            else:
                validate_style_cols(columns, f"{scope_label}/{item.get('name') or item.get('type') or 'columns'}", warn)
        row = item.get("row")
        col = item.get("col")
        if isinstance(row, int) and isinstance(col, int):
            rows[row].append((index, col))

    for row, pairs in sorted(rows.items()):
        actual = [col for _index, col in sorted(pairs)]
        expected = list(range(len(actual)))
        if actual != expected:
            warn(
                f"{scope_label}: styleDetail row {row} has col values {actual}, "
                f"expected ordinal {expected}; designer may render only part of the row"
            )


def validate_package(path: Path, out: Optional[Path] = None) -> int:
    if path.suffix.lower() == ".dba":
        obj = read_dba(path)
    else:
        obj = read_json(path)

    values = symbol_values(obj)
    app = obj.get("app") or {}
    tables = obj.get("tables") or []
    resolved_tables = resolve_any(tables, values)
    issues = []
    warnings = []

    def issue(message: str) -> None:
        issues.append(message)

    def warn(message: str) -> None:
        warnings.append(message)

    for string_path, text in iter_strings(obj):
        for match in SYMBOL_RE.finditer(text):
            index = int(match.group(1))
            if index >= len(values):
                issue(f"{string_path}: symbol index {index} is out of range ({len(values)} symbols)")

    symbol_counter = Counter(v for v in values if v)
    duplicate_symbols = [value for value, count in symbol_counter.items() if count > 1]
    if duplicate_symbols:
        warn(f"duplicate symbol values: {len(duplicate_symbols)} values are repeated")

    table_by_raw = {str(table.get("tableName", "")): table for table in tables if isinstance(table, dict)}
    table_by_resolved = {str(table.get("tableName", "")): table for table in resolved_tables if isinstance(table, dict)}
    raw_to_resolved_table = {}
    for raw, resolved in zip(tables, resolved_tables):
        if isinstance(raw, dict) and isinstance(resolved, dict):
            raw_to_resolved_table[str(raw.get("tableName", ""))] = resolved

    db_name_re = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
    system_columns = {
        "id", "pid", "seq", "data_title", "summary", "table_id", "data_type", "from_ref_id",
        "sys_status", "sys_create_id", "sys_create_name", "sys_create_time",
        "sys_update_id", "sys_update_name", "sys_update_time",
        "sys_create_org_id", "sys_create_org_name", "sys_create_branch_id", "sys_create_branch_name",
        "sys_current_task_approval_status", "sys_task_name",
        "gmt_created", "gmt_modified",
    }

    forms = []
    form_by_ref = {}
    form_label_by_ref = {}
    fields_by_form_ref = defaultdict(set)
    component_by_form_field = defaultdict(dict)
    all_field_names = set()
    about_fields = []
    association_items = []
    judge_rules = []
    workflow_models = []
    fields_total = 0
    related_fields = 0
    child_tables = 0
    workflow_forms = 0
    association_metadata_count = 0
    judge_rule_count = 0
    dashboard_count = 0

    for group_index, group in enumerate(app.get("groups") or []):
        group_name = group.get("name", f"group[{group_index}]")
        for form_index, form in enumerate(group.get("forms") or []):
            forms.append(form)
            form_name = form.get("name", f"form[{form_index}]")
            form_label = f"{group_name}/{form_name}"
            form_id = form.get("id")
            form_key = form.get("formKey")
            form_fields = form.get("fields") or []
            fields_total += len(form_fields)
            if form.get("flowModels"):
                workflow_forms += 1
            for ref in [form_id, form_key]:
                if is_present(ref):
                    form_by_ref[str(ref)] = form
                    form_label_by_ref[str(ref)] = form_label
                    resolved_ref = resolve_string(str(ref), values)
                    form_by_ref[resolved_ref] = form
                    form_label_by_ref[resolved_ref] = form_label
            for field in form_fields:
                field_name = field.get("name")
                if field_name:
                    all_field_names.add(str(field_name))
                    for ref in [form_id, form_key, resolve_string(str(form_id or ""), values), resolve_string(str(form_key or ""), values)]:
                        if ref:
                            fields_by_form_ref[str(ref)].add(str(field_name))
                            component_by_form_field[str(ref)][str(field_name)] = str(field.get("type") or "")
                if field.get("type") == "childrenTable":
                    for child in field.get("children") or []:
                        child_name = child.get("name")
                        if child_name:
                            all_field_names.add(str(child_name))
            for key in ["associationOptions", "relationOptions", "linkageOptions", "referenceForms", "dataFillList"]:
                items = as_list(form.get(key))
                association_metadata_count += len(items)
                for item in items:
                    association_items.append((form_label, key, item))
            for rule in form.get("judgeRules") or []:
                judge_rule_count += 1
                judge_rules.append((form_label, form, rule))
            for flow in form.get("flowModels") or []:
                workflow_models.append((form_label, form, flow))

            if form_id != form_key:
                issue(f"{form_label}: form.id must equal form.formKey ({form_id!r} != {form_key!r})")

            table_name = form.get("tableName")
            if form_fields and not table_name:
                issue(f"{form_label}: field-bearing form is missing tableName")
            if table_name:
                resolved_table_name = resolve_string(str(table_name), values)
                table = table_by_raw.get(str(table_name)) or table_by_resolved.get(resolved_table_name)
                resolved_table = raw_to_resolved_table.get(str(table_name)) or table_by_resolved.get(resolved_table_name)
                if not table and not resolved_table:
                    issue(f"{form_label}: tableName {table_name!r} has no matching top-level tables[] entry")
                else:
                    ddl = str((resolved_table or table).get("ddl", ""))
                    if resolved_table_name and resolved_table_name not in ddl:
                        warn(f"{form_label}: resolved table name {resolved_table_name!r} not found in DDL text")

            if form_fields:
                for required_key in ["styleDetail", "addOption", "editOption"]:
                    if form.get(required_key) in (None, "", [], {}):
                        issue(f"{form_label}: field-bearing form missing {required_key}")
                style_detail = form.get("styleDetail")
                if isinstance(style_detail, str) and style_detail.strip():
                    try:
                        style_items = json.loads(style_detail)
                    except Exception:
                        style_items = None
                    if isinstance(style_items, list):
                        validate_style_cols(style_items, form_label, warn)
                tabs = form.get("tabs") or []
                if not tabs:
                    issue(f"{form_label}: field-bearing form has no tabs")
                tab_ref = form.get("tabFieldReference")
                if not tab_ref:
                    issue(f"{form_label}: field-bearing form missing tabFieldReference")
                elif isinstance(tab_ref, dict) and tab_ref.get("formId") != form_id:
                    issue(f"{form_label}: tabFieldReference.formId must equal form.id")

                tab_keys = set()
                for tab_index, tab in enumerate(tabs):
                    tab_id = tab.get("id") or tab.get("tabKey")
                    if tab_id:
                        tab_keys.add(tab_id)
                    for key in ["formKey", "tabFormKey"]:
                        if key in tab and tab.get(key) != form_key:
                            issue(f"{form_label}: tabs[{tab_index}].{key} must equal form.formKey")

                for view_index, view in enumerate(form.get("tabViews") or []):
                    tab_key = view.get("tabKey")
                    if tab_key and tab_keys and tab_key not in tab_keys:
                        issue(f"{form_label}: tabViews[{view_index}].tabKey {tab_key!r} does not match same-form tabs")

            def validate_field_list(field_list, scope_label, target_table_name):
                nonlocal related_fields
                names = []
                target_resolved = resolve_string(str(target_table_name or ""), values)
                table = table_by_raw.get(str(target_table_name or "")) or table_by_resolved.get(target_resolved)
                resolved_table = raw_to_resolved_table.get(str(target_table_name or "")) or table_by_resolved.get(target_resolved)
                ddl_columns = parse_ddl_columns(str((resolved_table or table or {}).get("ddl", "")))
                for field in field_list:
                    field_name = field.get("name")
                    field_type = field.get("type")
                    if field_type == "childrenTable":
                        continue
                    if field_name:
                        names.append(field_name)
                        if len(str(field_name)) > 128:
                            issue(f"{scope_label}: field name too long: {field_name}")
                        if not db_name_re.match(str(field_name)):
                            issue(f"{scope_label}: non-standard db field name: {field_name}")
                    columns = field.get("columns") or []
                    for col in columns:
                        col_name = col.get("name")
                        if not col_name:
                            continue
                        if col_name in system_columns and col_name != "id":
                            issue(f"{scope_label}: field column conflicts with system column: {col_name}")
                        if ddl_columns and col_name not in ddl_columns:
                            issue(f"{scope_label}: field column {col_name!r} missing from DDL for table {target_resolved!r}")
                    if field_type == "aboutTable":
                        related_fields += 1
                        about_fields.append((scope_label, field))
                        column_names = {col.get("name") for col in columns}
                        if not any(str(name).endswith("_ref_id") for name in column_names if name):
                            warn(f"{scope_label}: aboutTable field {field_name!r} has no *_ref_id helper column")
                for name, count in Counter(names).items():
                    if count > 1:
                        issue(f"{scope_label}: duplicate field/column name {name!r}")

            # Exported child fields can appear twice: nested under childrenTable.children
            # and as childrenField mirrors in form.fields. Mirrors belong to the child DDL.
            main_fields = [field for field in form_fields if not field.get("childrenField")]
            validate_field_list(main_fields, form_label, table_name)
            for field in form_fields:
                if field.get("type") == "childrenTable":
                    child_tables += 1
                    child_name = field.get("name")
                    if not child_name:
                        issue(f"{form_label}: childrenTable missing name/table name")
                        continue
                    child_resolved_name = resolve_string(str(child_name), values)
                    if not db_name_re.match(child_resolved_name):
                        issue(f"{form_label}: non-standard child table name: {child_name}")
                    child_table = table_by_raw.get(str(child_name)) or table_by_resolved.get(child_resolved_name)
                    if not child_table:
                        issue(f"{form_label}: child table {child_name!r} has no top-level tables[] DDL")
                    validate_field_list(field.get("children") or [], f"{form_label}/{field.get('comment', child_name)}", child_name)

    def form_ref_exists(ref) -> bool:
        if not is_present(ref):
            return False
        raw = str(ref)
        resolved = resolve_string(raw, values)
        return raw in form_by_ref or resolved in form_by_ref

    def fields_for_ref(ref) -> set[str]:
        if not is_present(ref):
            return set()
        raw = str(ref)
        resolved = resolve_string(raw, values)
        return fields_by_form_ref.get(raw) or fields_by_form_ref.get(resolved) or set()

    form_ref_keys = {
        "formId", "formKey", "refFormId", "refFormKey", "referenceFormId", "referenceFormKey",
        "targetFormId", "targetFormKey", "aboutTableId", "aboutTableFormId", "aboutPluginFormId",
        "clickRefFormId", "mainFormId", "subFormId", "sourceFormId", "sourceFormKey",
    }
    field_ref_keys = {
        "fieldName", "fieldKey", "sourceFieldName", "targetFieldName", "refFieldName",
        "fieldValue", "valueFieldName", "displayFieldName",
    }

    for scope_label, field in about_fields:
        refs = []
        for item in flatten_dicts(field):
            for key, value in item.items():
                if key in form_ref_keys and is_present(value):
                    refs.append(value)
        if not refs:
            warn(f"{scope_label}: aboutTable field {field.get('name')!r} has no visible target form metadata; verify selector in runtime")
        for ref in refs:
            if not form_ref_exists(ref):
                warn(f"{scope_label}: aboutTable field {field.get('name')!r} references unknown form {ref!r}")

    for form_label, meta_key, item in association_items:
        if not isinstance(item, dict):
            continue
        for sub in flatten_dicts(item):
            for key, value in sub.items():
                if key in form_ref_keys and is_present(value) and not form_ref_exists(value):
                    warn(f"{form_label}: {meta_key} references unknown form {value!r}")
                if key in field_ref_keys and is_present(value) and str(value) not in all_field_names and not str(value).startswith("@@{"):
                    warn(f"{form_label}: {meta_key} references unknown field {value!r}")

    def validate_rule_steps(rule_label: str, step_items: list, target_ref, source_ref) -> None:
        target_fields = fields_for_ref(target_ref)
        source_fields = fields_for_ref(source_ref)
        for step_index, step in enumerate(step_items):
            if not isinstance(step, dict):
                continue
            target_field = pick_first(step, ["fieldName", "targetFieldName", "fieldKey"])
            source_field = pick_first(step, ["fieldValue", "sourceFieldName", "valueFieldName"])
            if target_field and target_fields and str(target_field) not in target_fields:
                warn(f"{rule_label}: step[{step_index}] target field {target_field!r} not found on target form")
            if source_field and source_fields and str(source_field) not in source_fields and not str(source_field).startswith(("@@{", "$", "{")):
                assign_type = str(step.get("assignType") or step.get("valueType") or "")
                if "TRIGGER" in assign_type.upper() or not assign_type:
                    warn(f"{rule_label}: step[{step_index}] source field {source_field!r} not found on trigger form")
            if target_field and not pick_first(step, ["componentTypeCode", "fieldComponentTypeCode", "targetComponentTypeCode"]):
                warn(f"{rule_label}: step[{step_index}] missing target componentTypeCode for field {target_field!r}")

    for rule_index, (form_label, form, rule) in enumerate(judge_rules):
        rule_label = f"{form_label}/judgeRules[{rule_index}]"
        if not isinstance(rule, dict):
            issue(f"{rule_label}: rule entry must be an object")
            continue
        source_ref = pick_first(rule, ["formId", "formKey"]) or form.get("id") or form.get("formKey")
        if not pick_first(rule, ["formId", "formKey"]):
            issue(f"{rule_label}: missing formId/formKey")
        elif not form_ref_exists(source_ref):
            issue(f"{rule_label}: references unknown trigger form {source_ref!r}")
        if not is_present(rule.get("triggers")) and not is_present(rule.get("triggerType")):
            issue(f"{rule_label}: missing triggers/triggerType")
        actions = as_list(rule.get("actions"))
        if not actions:
            issue(f"{rule_label}: missing actions")
        for action_index, action in enumerate(actions):
            if not isinstance(action, dict):
                issue(f"{rule_label}/actions[{action_index}]: action entry must be an object")
                continue
            action_label = f"{rule_label}/actions[{action_index}]"
            action_type = pick_first(action, ["updateType", "actionType", "type", "operateType", "operationType"]) or rule.get("updateType")
            action_type_text = str(action_type or "").upper()
            target_ref = pick_first(action, ["formId", "formKey", "targetFormId", "targetFormKey", "refFormId", "refFormKey"])
            if not action_type_text:
                warn(f"{action_label}: missing action type; verify rule in designer")
            if not target_ref:
                issue(f"{action_label}: missing target form reference")
            elif not form_ref_exists(target_ref):
                issue(f"{action_label}: target form {target_ref!r} not found in this package")
            filters = as_list(action.get("filters") or action.get("filterItems") or action.get("conditions") or action.get("where"))
            steps = as_list(action.get("steps"))
            else_steps = as_list(action.get("elseSteps"))
            child_steps = as_list(action.get("childSteps"))
            if action_type_text in {"UPDATE", "DELETE", "UPDATE_OR_INSERT"} and not filters:
                issue(f"{action_label}: {action_type_text} requires filters")
            if action_type_text in {"INSERT", "UPDATE", "UPDATE_OR_INSERT"} and not steps:
                issue(f"{action_label}: {action_type_text} requires steps")
            if action_type_text == "UPDATE_OR_INSERT" and not else_steps:
                issue(f"{action_label}: UPDATE_OR_INSERT requires elseSteps for first-time insert branch")
            if child_steps or is_present(action.get("batchAction")) or is_present(action.get("descartesAction")):
                warn(f"{action_label}: childSteps/batchAction/descartesAction must be proven by runtime child-row execution tests")
            validate_rule_steps(action_label, steps + else_steps + child_steps, target_ref, source_ref)

    for flow_index, (form_label, form, flow) in enumerate(workflow_models):
        flow_label = f"{form_label}/flowModels[{flow_index}]"
        if not isinstance(flow, dict):
            issue(f"{flow_label}: flow model entry must be an object")
            continue
        flow_form = flow.get("form") or {}
        form_process_key = form.get("processKey")
        flow_process_key = pick_first(flow_form, ["processKey", "processDefinitionKey"]) or pick_first(flow, ["processKey", "processDefinitionKey"])
        if form_process_key and flow_process_key and form_process_key != flow_process_key:
            warn(f"{flow_label}: form.processKey and flow processKey differ")
        for required_key in ["authorityRule", "nodeSettings", "definition"]:
            if not is_present(flow.get(required_key)):
                issue(f"{flow_label}: missing {required_key}")
        if not (is_present(flow.get("bpmnXml")) or is_present(flow.get("bpmnXmlId")) or is_present(flow.get("bpmnXmlFileId"))):
            warn(f"{flow_label}: missing bpmnXml/bpmnXmlId; actual workflow start may fail")
        if not (is_present(flow.get("processImage")) or is_present(flow.get("processImageId")) or is_present(flow.get("processImageFileId"))):
            warn(f"{flow_label}: missing processImage/processImageId; designer/workflow preview may fail")
        if not (is_present(flow.get("id")) or is_present(flow.get("modelId"))):
            warn(f"{flow_label}: missing model id")
        definition = flow.get("definition") or {}
        if isinstance(definition, dict) and not (is_present(definition.get("id")) or is_present(definition.get("processDefinitionId")) or is_present(definition.get("key"))):
            warn(f"{flow_label}: definition missing id/key")
        node_settings = as_list(flow.get("nodeSettings"))
        if not node_settings:
            issue(f"{flow_label}: nodeSettings is empty")
        node_button_count = 0
        for node_index, node in enumerate(node_settings):
            if not isinstance(node, dict):
                continue
            node_id = pick_first(node, ["nodeId", "id", "taskKey", "activityId"])
            node_name = pick_first(node, ["nodeName", "name", "taskName", "activityName"])
            if not node_id:
                warn(f"{flow_label}: nodeSettings[{node_index}] missing node id")
            if not node_name:
                warn(f"{flow_label}: nodeSettings[{node_index}] missing node name")
            node_buttons = as_list(node.get("buttons") or node.get("formButtons") or node.get("buttonSettings"))
            node_button_count += len(node_buttons)
            node_type = str(node.get("nodeType") or node.get("type") or "").lower()
            has_subjects = any(is_present(node.get(key)) for key in ["flowSubjects", "subjects", "assignees", "handlers", "users", "roles"])
            if node_type and "start" not in node_type and "end" not in node_type and not has_subjects:
                warn(f"{flow_label}: nodeSettings[{node_index}] has no visible assignee/subject config")
        if node_settings and node_button_count == 0:
            warn(f"{flow_label}: nodeSettings contain no node-level buttons/actions")

    if related_fields == 0 and len(forms) > 3:
        warn("no aboutTable related-record fields found; cross-module business flow may be text-linked only")
    if len(forms) > 3 and association_metadata_count == 0 and related_fields == 0 and judge_rule_count == 0:
        warn("multi-form app has no related-record fields, association metadata, or business rules; module data flow is likely not native")
    if workflow_forms and not any((form.get("flowModels") or []) for form in forms):
        warn("workflow form counter mismatch")

    def embedded_json(value, label):
        if isinstance(value, dict):
            return value
        if value in (None, ""):
            return {}
        if not isinstance(value, str):
            issue(f"{label}: expected JSON object or JSON string")
            return {}
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as exc:
            issue(f"{label}: invalid embedded JSON: {exc}")
            return {}
        if not isinstance(parsed, dict):
            issue(f"{label}: embedded JSON must decode to an object")
            return {}
        return parsed

    def safe_dashboard_alias(value) -> bool:
        text = str(value or "")
        return bool(text) and (text[0] == "_" or text[0].isalpha()) and all(
            char == "_" or char.isalnum() for char in text
        )

    datam = embedded_json(obj.get("datamConfig"), "datamConfig")
    dashboards = datam.get("dashBoardList") or []
    if dashboards and not isinstance(dashboards, list):
        issue("datamConfig.dashBoardList: expected a list")
        dashboards = []
    dashboard_count = len(dashboards)
    for dashboard_index, dashboard in enumerate(dashboards):
        if not isinstance(dashboard, dict):
            issue(f"datamConfig.dashBoardList[{dashboard_index}]: dashboard must be an object")
            continue
        dashboard_label = dashboard.get("name") or f"dashboard[{dashboard_index}]"
        for view_index, view in enumerate(dashboard.get("views") or []):
            if not isinstance(view, dict):
                continue
            model = embedded_json(view.get("model"), f"{dashboard_label}/views[{view_index}].model")
            for alias in model:
                if not safe_dashboard_alias(alias):
                    issue(
                        f"{dashboard_label}/views[{view_index}]: unsafe DataM result alias {alias!r}; "
                        "use letters, numbers, underscores, or ordinary Chinese text"
                    )
        for widget_index, widget in enumerate(dashboard.get("widgets") or []):
            if not isinstance(widget, dict):
                continue
            config = embedded_json(widget.get("config"), f"{dashboard_label}/widgets[{widget_index}].config")
            aliases = set((config.get("model") or {}).keys())
            for column in config.get("cols") or []:
                if not isinstance(column, dict):
                    continue
                aliases.update(value for value in [column.get("name"), column.get("alias")] if value)
            for alias in aliases:
                if not safe_dashboard_alias(alias):
                    issue(
                        f"{dashboard_label}/widgets[{widget_index}]: unsafe DataM result alias {alias!r}; "
                        "use letters, numbers, underscores, or ordinary Chinese text"
                    )

    result = {
        "path": str(path),
        "issues": issues,
        "warnings": warnings,
        "stats": {
            "groups": len(app.get("groups") or []),
            "forms": len(forms),
            "field_count": fields_total,
            "tables": len(tables),
            "symbols": len(values),
            "related_fields": related_fields,
            "child_tables": child_tables,
            "workflow_forms": workflow_forms,
            "association_metadata": association_metadata_count,
            "judge_rules": judge_rule_count,
            "dashboards": dashboard_count,
        },
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, "utf-8")
        print(out)
    else:
        print(text)
    return 1 if issues else 0


def resolve_cmd(json_path: Path, out: Path, pretty: bool) -> None:
    obj = read_json(json_path)
    resolved = resolve_any(obj, symbol_values(obj))
    write_json(out, resolved, pretty=pretty)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect, unpack, pack, summarize, and validate zlib JSON .dba packages.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("inspect")
    p.add_argument("input", type=Path)

    p = sub.add_parser("unpack")
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--pretty", action="store_true")

    p = sub.add_parser("pack")
    p.add_argument("json", type=Path)
    p.add_argument("--out", type=Path, required=True)

    p = sub.add_parser("resolve")
    p.add_argument("json", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--pretty", action="store_true")

    p = sub.add_parser("summary")
    p.add_argument("json", type=Path)
    p.add_argument("--out", type=Path, required=True)

    p = sub.add_parser("validate")
    p.add_argument("input", type=Path, help=".dba or unpacked app.json")
    p.add_argument("--out", type=Path)

    args = parser.parse_args()
    if args.cmd == "inspect":
        inspect_file(args.input)
    elif args.cmd == "unpack":
        unpack(args.input, args.out, pretty=args.pretty)
    elif args.cmd == "pack":
        pack_json(args.json, args.out)
        print(args.out)
    elif args.cmd == "resolve":
        resolve_cmd(args.json, args.out, pretty=args.pretty)
    elif args.cmd == "summary":
        summarize(args.json, args.out)
    elif args.cmd == "validate":
        sys.exit(validate_package(args.input, args.out))
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
