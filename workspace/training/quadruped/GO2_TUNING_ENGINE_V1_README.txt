GO2 TUNING ENGINE V1.3 — fixed engine + validated experiment JSON

WHAT CHANGED IN V1.3 (engine_version 1.2.0)
- The tier-1 promotion gate now scores the WEIGHTED TOTAL, not one pinned scenario.
  Reason: on all four measured runs the pinned-scenario clause disagreed with the
  weighted total. It killed G-A011 (+3.0903/70) and G-A010 (+2.2572/70), both of
  which regressed no scenario's survival beyond tolerance, and it passed only
  G-A013 (-1.4278/70), the one candidate that was actually worse. The official rule
  scores the weighted sum of scenario scores, so that is what the gate scores.
  evaluation.gates.min_total_points_delta is now required and must be positive;
  target_scenario/target_min_proxy_delta are optional and recorded as an observation
  under tier1 decision key "target_scenario_observation". Decision schema_version 3.
- The frozen baseline is now selectable: Default-01 or Pilot-01.
  Reason: the 69-case posture_gate_v2 suite measures Default-01 at 17.90697/70 and
  the frozen Pilot-01 at 33.79311/70. Screening single variables against Default-01
  optimises a policy that would never be submitted. Both baselines, their env.yaml
  and their verified seed-101 tier-1 case evidence now ship in the engine ZIP under
  baseline/default/ and baseline/pilot/; the experiment's baseline.name selects one
  and the validator pins that baseline's reward set and model/env SHA-256.
- Engine archive renamed to go2_tuning_engine_v1_3.zip. v1_1 and v1_2 are
  SUPERSEDED_DO_NOT_REUSE; an engine_version mismatch is rejected at validate time,
  before any training starts.

PURPOSE
- The engine ZIP contains runner/evaluator/reporter/source template and both frozen baselines.
- It contains no experiment. Reward/seed/iteration/gates/output names come from the JSON.
- The runtime validator rejects anything other than exactly one reward change against the
  frozen baseline the experiment names.

G-A015 UPLOADS
1. /workspace/go2_tuning_engine_v1_3.zip
2. /workspace/G_A015_pilot_feet_air_time_035.json

G-A015 IDENTITY
- baseline: Pilot-01 iter 1000 (1.2 / 0.2 / -2.0 / -0.05 / -0.01 / 0.0), 33.79311/70 over 69 cases
- single change: feet_air_time  0.20 -> 0.35   (all five other weights stay at Pilot-01)
- training: from scratch, seed 42, 4096 envs, 1000 iterations
- tier-1 gate: weighted total delta >= +1.0/70, no scenario survival regression beyond 0.10
- experiment SHA-256: f2ac4d7fb68da95ec982c708f95664a31ec46af8d38d7a9721dbc29c8c8ca693
  (this README ships inside the engine ZIP, so the engine's own SHA is recorded in
   go2_tuning_engine_v1_3.VERIFICATION.md and SERVER_SESSION_RUNBOOK.md, not here)

ONE-LINE RUN
cd /workspace && unzip -oq go2_tuning_engine_v1_3.zip && cd /workspace/go2_tuning_engine_v1_3 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A015_pilot_feet_air_time_035.json

MONITOR
tmux attach -t go2_g_a015

DONE MARKER
[DONE] GO2_PILOT_FEET_AIR_TIME_035_RESULT_READY

DOWNLOAD BOTH
/workspace/_keep/GO2_PILOT_FEET_AIR_TIME_035_RESULT.zip
/workspace/_keep/GO2_PILOT_FEET_AIR_TIME_035_RESULT.zip.sha256

RESULT CONTRACT
- FULL or PARTIAL result status
- engine version, engine archive SHA when the uploaded ZIP remains at the canonical path
- experiment JSON, experiment SHA, schema
- training checkpoint/env/log/tfevents/params/source/reward diff
- candidate tier-1 telemetry, baseline telemetry, conditional representative telemetry
- G1 forward-fast seed-101 video
- exported policy and actor-tensor lineage
- a single result ZIP plus SHA companion

LIMITS
- INTERNAL_* results are internal gates, not official results.
- One training seed is exploratory and cannot establish optimality or official qualification.
- Do not run two 4096-env trainings concurrently on the confirmed single RTX 5080.
- G7 is not independent evidence: G-A012 found dr_seed_* steps.csv byte-identical to the same
  seed's rough_forward. Do not cite a G7 delta as separate from G3 until the DR case is fixed.
- config/experiments/G_A010_lin_vel_z_m2.json and G_A013_flat_orientation_m1.json are pinned to
  older engine versions and no longer validate. They are kept as records of completed runs.
