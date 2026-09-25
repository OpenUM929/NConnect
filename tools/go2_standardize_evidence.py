"""Lossless, explicitly typed view of legacy aggregates; never edits inputs."""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DICTIONARY = ROOT / "workspace/training/quadruped/config/go2_evidence_data_dictionary.json"
OUTPUT = ROOT / "workspace/training/quadruped/reports/evidence/go2_standardized_v1/standardized.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_dictionary() -> dict:
    return json.loads(DICTIONARY.read_text(encoding="utf-8"))


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        if not headers or len(headers) != len(set(headers)):
            raise ValueError(f"missing/duplicate headers: {path}")
        return list(reader)


def validate_spec(spec: dict) -> None:
    """Reject missing semantics, without claiming the supplied prose is true."""
    def require_text(mapping: dict, fields: tuple[str, ...]) -> None:
        for field in fields:
            value = mapping.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"missing/empty semantic field: {field}")

    require_text(spec, ("source", "producer", "population", "window",
                        "aggregation", "limitations", "identity_status"))
    keys, metrics = spec.get("keys"), spec.get("metrics")
    if (not isinstance(keys, list) or not keys
            or any(not isinstance(k, str) or not k.strip() for k in keys)
            or len(keys) != len(set(keys))):
        raise ValueError("nonempty unique dimension names required")
    if not isinstance(metrics, dict) or not metrics or set(keys) & set(metrics):
        raise ValueError("metrics required; dimensions cannot also be metrics")
    for definition in metrics.values():
        if not isinstance(definition, dict):
            raise ValueError("metric definition must be an object")
        require_text(definition, ("canonical_name", "unit", "formula", "kind",
                                 "population", "window", "aggregation",
                                 "limitations", "missing_reason"))
        if definition["kind"] not in {
                "MEASURED", "DERIVED", "SURROGATE", "COUNTERFACTUAL", "HYPOTHESIS"}:
            raise ValueError("unknown evidence kind")


def normalize(spec: dict, rows: list[dict]) -> list[dict]:
    validate_spec(spec)
    expected = set(spec["keys"]) | set(spec["metrics"])
    names = [m["canonical_name"] for m in spec["metrics"].values()]
    if len(names) != len(set(names)):
        raise ValueError("duplicate canonical metric names")
    seen = set()
    result = []
    for row in rows:
        if set(row) != expected or any(v is None for v in row.values()):
            raise ValueError("schema/header or row width mismatch")
        key = tuple(row[k] for k in spec["keys"])
        if key in seen or any(v == "" for v in key):
            raise ValueError("duplicate or empty dimension key")
        seen.add(key)
        values = {}
        for column, definition in spec["metrics"].items():
            raw = row[column]
            value = None if raw == "" else float(raw)
            if value is not None and not math.isfinite(value):
                raise ValueError("nonfinite value is not an explicit missing value")
            values[definition["canonical_name"]] = {
                "legacy_column": column, "raw_value": raw, "value": value,
                "status": "MISSING" if value is None else "PRESENT",
                "reason": definition["missing_reason"] if value is None else "",
            }
        result.append({"dimensions": dict(zip(spec["keys"], key)), "metrics": values})
    return result


def build() -> dict:
    dictionary = load_dictionary()
    datasets = []
    for name, spec in dictionary["datasets"].items():
        validate_spec(spec)
        source = ROOT / spec["source"]
        producer = ROOT / spec["producer"].split("::")[0]
        datasets.append({
            "id": name, "source_sha256": sha(source), "producer_sha256": sha(producer),
            "records": normalize(spec, read_rows(source)),
        })
    return {"schema_version": dictionary["schema_version"], "dictionary_sha256": sha(DICTIONARY),
            "normalizer_sha256": sha(Path(__file__)),
            "validation_scope": "legacy-cell preservation and explicit semantics; NOT raw recomputation or causal validation",
            "dictionary": dictionary, "datasets": datasets}


if __name__ == "__main__":
    data = build()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"{OUTPUT}: {sum(len(d['records']) for d in data['datasets'])} rows; inputs unchanged")
