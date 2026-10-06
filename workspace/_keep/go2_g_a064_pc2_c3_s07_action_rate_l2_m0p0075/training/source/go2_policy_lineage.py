"""Verify that an exported TorchScript actor contains checkpoint actor tensors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch


def verify(checkpoint: Path, policy: Path) -> dict:
    raw = torch.load(checkpoint, map_location="cpu", weights_only=False)
    actor = raw.get("actor_state_dict") or raw.get("model_state_dict")
    if not isinstance(actor, dict):
        raise RuntimeError("checkpoint actor state_dict missing")
    actor_items = [
        (name, value.detach().cpu()) for name, value in actor.items()
        if hasattr(value, "shape") and "std" not in name.lower()
    ]
    scripted = torch.jit.load(str(policy), map_location="cpu")
    policy_items = [(name, value.detach().cpu()) for name, value in scripted.state_dict().items()]
    unmatched = list(policy_items)
    matched = []
    for actor_name, actor_value in actor_items:
        candidates = [
            (index, name, value) for index, (name, value) in enumerate(unmatched)
            if tuple(value.shape) == tuple(actor_value.shape) and torch.equal(value, actor_value)
        ]
        if not candidates:
            continue
        index, policy_name, _ = candidates[0]
        unmatched.pop(index)
        matched.append({"checkpoint": actor_name, "policy": policy_name, "shape": list(actor_value.shape)})
    ok = len(matched) == len(actor_items) == len(policy_items)
    return {
        "schema_version": 1,
        "status": "ACTOR_TENSORS_MATCH" if ok else "ACTOR_TENSORS_MISMATCH",
        "checkpoint_actor_tensor_count": len(actor_items),
        "policy_tensor_count": len(policy_items),
        "matched_tensor_count": len(matched),
        "matches": matched,
        "unmatched_policy": [name for name, _ in unmatched],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("policy", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    report = verify(args.checkpoint, args.policy)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    print(report["status"])
    return 0 if report["status"] == "ACTOR_TENSORS_MATCH" else 3


if __name__ == "__main__":
    raise SystemExit(main())

