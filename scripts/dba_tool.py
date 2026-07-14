#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path


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
                "association_count": len(form.get("associationOptions") or []),
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

    for path in ["summary.md", "forms.csv", "fields.csv", "buttons.csv", "workflows.csv", "tables.csv"]:
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


def resolve_cmd(json_path: Path, out: Path, pretty: bool) -> None:
    obj = read_json(json_path)
    resolved = resolve_any(obj, symbol_values(obj))
    write_json(out, resolved, pretty=pretty)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect, unpack, pack, and summarize zlib JSON .dba packages.")
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
    else:
        parser.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
