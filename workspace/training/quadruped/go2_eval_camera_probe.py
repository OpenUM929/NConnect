"""Read-only camera probe for a Go2 video replay (G-A056, 2026-09-28).

Plan: upload/plan/GO2_G_A056_A043_DIAG_REPLAY_PLAN_20260928.md section 4-2.

Question it answers: did the camera that produced the video actually follow the env we asked for
(``env.viewer.env_index=<k>``)?  A matching steps.csv says the rollout is the same; it does not say what
the camera looked at.  So after every ``env.step`` this module writes one row to ``camera.csv``:

  cfg_env_index      viewport_camera_controller.cfg.env_index        (Isaac Lab v2.3.1 ViewerCfg)
  origin_type        viewport_camera_controller.cfg.origin_type      ("asset_root" in this task, env_cfg.py L84)
  viewer_origin_*    viewport_camera_controller.viewer_origin        (root_pos_w[env_index] at its last update)
  prim_*             world translation of the USD camera prim cfg.viewer.cam_prim_path ("/OmniverseKit_Persp"),
                     the prim ManagerBasedRLEnv.render() records frames from; read with
                     UsdGeom.Xformable.ComputeLocalToWorldTransform
  target_root_*      robot.data.root_pos_w[expected env]
  implied_origin_*   prim - default_cam_eye (the controller places the camera at origin + eye)
  target_dist_xy     |implied_origin - target_root| in xy
  nearest_env / nearest_dist_xy      env whose root is closest (xy) to implied_origin
  other_near_dist_xy distance from implied_origin to the closest root of any other env

The controller updates the camera on the app post-update event (every render), and this probe runs inside
env.step before the recorder's render of that step, so a row can lag the target by one step.  The local
verifier compares against the target root of this row and of the previous row.  Nothing is written to the
simulation or the stage.  Failures are recorded in camera_meta.json "unavailable", never guessed.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Callable

SCHEMA = "go2_eval_camera_probe_v1"
FIELDS = ["step", "cfg_env_index", "origin_type",
          "viewer_origin_x", "viewer_origin_y", "viewer_origin_z",
          "prim_x", "prim_y", "prim_z",
          "target_root_x", "target_root_y", "target_root_z",
          "implied_origin_x", "implied_origin_y", "implied_origin_z",
          "target_dist_xy", "nearest_env", "nearest_dist_xy", "other_near_dist_xy"]


def _t(value: Any) -> Any:
    return getattr(value, "torch", value)


def _fmt(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return f"{value:.6g}" if math.isfinite(float(value)) else ""


def usd_translation(path: str) -> list[float]:
    import omni.usd
    from pxr import Usd, UsdGeom

    prim = omni.usd.get_context().get_stage().GetPrimAtPath(path)
    if not prim or not prim.IsValid():
        raise RuntimeError(f"camera prim {path} not found")
    m = UsdGeom.Xformable(prim).ComputeLocalToWorldTransform(Usd.TimeCode.Default())
    t = m.ExtractTranslation()
    return [float(t[0]), float(t[1]), float(t[2])]


class CameraProbe:
    def __init__(self, output: Path, max_steps: int, expected_env: int,
                 read_prim: Callable[[str], list[float]] = usd_translation) -> None:
        self.output = Path(output)
        self.max_steps = max_steps
        self.expected = int(expected_env)
        self.read_prim = read_prim
        self.step = 0
        self.closed = False
        self.handle = None
        self.meta: dict[str, Any] = {"schema": SCHEMA, "expected_env_index": self.expected, "unavailable": {},
                                     "read_only": True}

    def _disable(self, group: str, exc: BaseException | str) -> None:
        self.meta["unavailable"].setdefault(group, exc if isinstance(exc, str) else f"{type(exc).__name__}: {exc}")

    def attach(self, base: Any) -> None:
        self.meta["num_envs"] = int(base.num_envs)
        self.ctrl = getattr(base, "viewport_camera_controller", None)
        if self.ctrl is None:
            self._disable("controller", "env.viewport_camera_controller is None (no render mode for the viewport)")
        viewer = getattr(getattr(base, "cfg", None), "viewer", None)
        self.prim_path = getattr(viewer, "cam_prim_path", None) or "/OmniverseKit_Persp"
        self.meta["cam_prim_path"] = self.prim_path
        self.meta["resolution"] = list(getattr(viewer, "resolution", []) or [])
        self.eye = None
        if self.ctrl is not None:
            try:
                self.eye = [float(x) for x in list(self.ctrl.default_cam_eye)]
                self.meta["default_cam_eye"] = self.eye
                self.meta["cfg_env_index_at_attach"] = int(self.ctrl.cfg.env_index)
                self.meta["origin_type_at_attach"] = str(self.ctrl.cfg.origin_type)
                self.meta["asset_name"] = str(self.ctrl.cfg.asset_name)
            except Exception as exc:  # noqa: BLE001
                self._disable("controller", exc)
        self.output.mkdir(parents=True, exist_ok=True)
        self.handle = (self.output / "camera.csv").open("w", encoding="utf-8", newline="")
        self.handle.write(",".join(FIELDS) + "\n")

    def record(self, env: Any) -> None:
        if self.closed:
            return
        base = getattr(env, "unwrapped", env)
        if self.handle is None:
            self.attach(base)
        row: dict[str, Any] = {k: None for k in FIELDS}
        row["step"] = self.step + 1
        try:
            roots = _t(base.scene["robot"].data.root_pos_w).detach().cpu().tolist()
            row.update(target_root_x=roots[self.expected][0], target_root_y=roots[self.expected][1],
                       target_root_z=roots[self.expected][2])
        except Exception as exc:  # noqa: BLE001
            roots = None
            self._disable("robot_root", exc)
        if self.ctrl is not None and "controller" not in self.meta["unavailable"]:
            try:
                row["cfg_env_index"] = int(self.ctrl.cfg.env_index)
                row["origin_type"] = str(self.ctrl.cfg.origin_type)
                vo = getattr(self.ctrl, "viewer_origin", None)
                if vo is not None:
                    v = _t(vo).detach().cpu().tolist()
                    row.update(viewer_origin_x=v[0], viewer_origin_y=v[1], viewer_origin_z=v[2])
            except Exception as exc:  # noqa: BLE001
                self._disable("controller", exc)
        if "prim" not in self.meta["unavailable"]:
            try:
                p = self.read_prim(self.prim_path)
                row.update(prim_x=p[0], prim_y=p[1], prim_z=p[2])
            except Exception as exc:  # noqa: BLE001
                self._disable("prim", exc)
        if row["prim_x"] is not None and self.eye is not None:
            io_ = [row["prim_x"] - self.eye[0], row["prim_y"] - self.eye[1], row["prim_z"] - self.eye[2]]
            row.update(implied_origin_x=io_[0], implied_origin_y=io_[1], implied_origin_z=io_[2])
            if roots is not None:
                d = [math.hypot(r[0] - io_[0], r[1] - io_[1]) for r in roots]
                k = min(range(len(d)), key=d.__getitem__)
                row.update(target_dist_xy=d[self.expected], nearest_env=k, nearest_dist_xy=d[k],
                           other_near_dist_xy=min(x for i, x in enumerate(d) if i != self.expected)
                           if len(d) > 1 else None)
        self.handle.write(",".join(_fmt(row[k]) for k in FIELDS) + "\n")
        self.step += 1
        if self.step >= self.max_steps:
            self.close(True)

    def close(self, completed: bool) -> None:
        if self.closed:
            return
        self.closed = True
        if self.handle is not None:
            self.handle.close()
        self.meta.update(completed=completed, steps=self.step, fields=FIELDS)
        (self.output / "camera_meta.json").write_text(json.dumps(self.meta, indent=1, sort_keys=True),
                                                      encoding="utf-8")
        status = "CAMERA_PROBE_COMPLETE" if completed and not self.meta["unavailable"] else (
            "CAMERA_PROBE_PARTIAL" if completed else "CAMERA_PROBE_INCOMPLETE")
        (self.output / "CAMERA_STATUS.txt").write_text(f"CAMERA_STATUS={status}\nSTEPS={self.step}\n",
                                                        encoding="utf-8")
