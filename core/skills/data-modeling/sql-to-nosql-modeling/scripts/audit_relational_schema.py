#!/usr/bin/env python3
"""Auditoría heurística de esquemas relacionales (.sql DDL) para migración a MongoDB o Lakehouse Columnar (DuckDB/Parquet).

Uso:
  python3 audit_relational_schema.py path/to/schema.sql [--json]
"""

import argparse
import json
from pathlib import Path
import re
import sys


TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_.\"`]+)\s*\((.*?)\);",
    re.IGNORECASE | re.DOTALL,
)
FK_RE = re.compile(
    r"FOREIGN\s+KEY\s*\(([^)]+)\)\s*REFERENCES\s+([a-zA-Z0-9_.\"`]+)",
    re.IGNORECASE,
)


def analyze_ddl(sql_text: str) -> list[dict]:
  results = []
  for match in TABLE_RE.finditer(sql_text):
    raw_name = match.group(1).strip('"`')
    body = match.group(2)
    fks = [
        {"column": fk.group(1).strip(), "target": fk.group(2).strip('"`')}
        for fk in FK_RE.finditer(body)
    ]
    col_lines = [
        line.strip()
        for line in body.splitlines()
        if line.strip()
        and not line.strip().upper().startswith(
            ("PRIMARY", "FOREIGN", "CONSTRAINT", "UNIQUE", "INDEX", "KEY")
        )
    ]

    recommendation = "ROOT_COLLECTION_OR_SILVER_TABLE"
    if len(fks) == 2 and len(col_lines) <= 5:
      recommendation = "JUNCTION_TABLE_EMBED_AS_ARRAY_OR_EXTENDED_REF"
    elif any(fk["target"] == raw_name for fk in fks):
      recommendation = "SELF_REFERENCING_HIERARCHY_USE_MATERIALIZED_PATH"
    elif any(
        kw in raw_name.lower()
        for kw in ("log", "hist", "audit", "event", "tx", "movimiento")
    ):
      recommendation = "HIGH_VOLUME_EVENT_TABLE_KEEP_REFERENCED_OR_PARQUET_LAKEHOUSE"
    elif len(col_lines) > 35:
      recommendation = "WIDE_SPARSE_TABLE_CONSIDER_ATTRIBUTE_PATTERN_EAV"

    results.append(
        {
            "table": raw_name,
            "estimatedColumns": len(col_lines),
            "foreignKeys": fks,
            "recommendedPattern": recommendation,
        }
    )
  return results


def main() -> int:
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument("sql_file", type=Path, help="Ruta al archivo .sql con DDL")
  parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
  args = parser.parse_args()

  if not args.sql_file.exists():
    print(f"Error: no existe el archivo {args.sql_file}", file=sys.stderr)
    return 1

  report = analyze_ddl(args.sql_file.read_text(encoding="utf-8", errors="ignore"))
  if args.json:
    print(json.dumps(report, indent=2, ensure_ascii=False))
  else:
    print(f"=== Auditoría SQL -> NoSQL/Lakehouse ({len(report)} tablas detectadas) ===")
    for item in report:
      print(
          f"- {item['table']} (cols≈{item['estimatedColumns']}, FKs={len(item['foreignKeys'])}) "
          f"-> {item['recommendedPattern']}"
      )
  return 0


if __name__ == "__main__":
  sys.exit(main())
