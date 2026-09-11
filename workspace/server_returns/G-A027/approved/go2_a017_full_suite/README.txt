GO2 G-A017 FULL SUITE  (work id G-A027)
=========================================

This package trains NOTHING.  It measures.

WHY
  G-A017 is Pilot-01 with one reward dial moved: track_lin_vel_xy_exp
  1.2 -> 1.4.  On 260904 it was recorded as a tier-1 failure.  The 260907
  re-audit found that verdict was produced by a defective gate:

    total points          +3.707916 / 70   (candidate over baseline)
    scenario products     6 of 7 improved, 0 regressed
    kill clause fired on  G4 survival factor -0.21875
    but G4's own product  +0.015871   (tracking gained more than survival lost)

  Engine 1.5.0 gates the scenario product, which is what the official form
  scores (시나리오 점수 = 생존율 x 추종 점수).  Re-adjudicating the stored
  G-A017 artifacts under the repaired gate returns INTERNAL_EARLY_KILL_PASS
  with both arms measured by the same evaluator and both arms walking.

  Because the run was killed at tier-1 it never received seeds 202/303 and
  never ran the 69-case suite.  It has a tier-1 absolute score
  (50.199157/70, against Pilot-01's 46.491241/70 on that same 7-case scale);
  what it lacks is a score on the 69-case worst-case scale that Pilot-01's
  33.793106/70 comes from.  The two scales are not comparable with each other.
  This run produces the missing one, for both policies, on the same day.

WHAT IT DOES
  1  frozen G-A017, all 69 G1-G7 case-runs (23 cases x seeds 101/202/303),
     posture-gated, with real domain randomization on G7
  2  frozen Pilot-01, the same 69 case-runs on the same evaluator binary
  3  one video per scenario G1-G7, so the numbers have a witness
  4  one-file result ZIP

  No training happens and no reward file is edited, so no submission candidate
  and no training artifact can change.  The one thing this run can destroy is
  its own previous output: launching it again writes to the same KEEP tree, so
  it refuses to start when results are already there unless you pass
  GO2_RESUME=1 or GO2_DISCARD_PREVIOUS=1.

RUN
  unzip go2_a017_full_suite.zip -d /workspace
  bash /workspace/go2_a017_full_suite/server_run_go2_a017_full_suite.sh

  It starts inside tmux and returns immediately.
  Finish marker:  [DONE] GO2_A017_FULL_SUITE_RESULT_READY

  Estimate ~1h45m from prior wall time.  It is an estimate, not a cap: nothing
  in the script stops the run when it is exceeded.

DOWNLOAD
  /workspace/_keep/GO2_A017_FULL_SUITE_RESULT.zip
  /workspace/_keep/GO2_A017_FULL_SUITE_RESULT.zip.sha256

GATES BUILT INTO THE RUNNER
  - each staged policy SHA must equal its frozen SHA, or the run aborts
  - every case summary must carry survival_proxy_source = posture_gate_v2,
    or that case FAILS rather than being banked on the old metric
  - a case FAILS if its posture was only partly observed, and also if the
    unobserved rows could have changed which robots counted as fallen: a
    missing frame is not evidence that the robot was standing
  - a case FAILS if any row carried a non-finite position or velocity.  inf
    clears every threshold in the gate, so an exploded step would otherwise
    read as a perfectly upright robot
  - all 69 case-runs per policy and all 7 videos must exist before packaging
  - a resume re-runs any case whose policy, case, seed, argv, step count or
    evaluator hash differs from what produced the stored summary
  - a second default launch refuses to overwrite an undownloaded result

PRE-REGISTERED READING (fixed before the run, not renegotiated after)
  Two questions are answered separately, because a screening result and a
  submission decision are not the same judgement and were previously conflated.

  Q1 SCREENING -- is the dial worth keeping?
     Compare the two 69-case scorecards.  A higher weighted total with no
     scenario product regression past the gate means the dial is kept and
     G-A017 becomes the frozen baseline that later single-variable runs are
     measured against.  This is a relative judgement between two policies on
     one ruler, and it is all this run can settle.

  Q2 SUBMISSION -- may either policy be submitted as our Go2 entry?
     Judged only by the registry's own bar in go2_self_eval_registry.json
     (score.internal_gates), which is stricter than Q1 and is not renegotiated
     here: every scenario needs survival >= 0.95 AND tracking >= 0.70, the
     weighted proxy needs >= 0.70, the self-assessment total needs >= 70, and
     seeds 101/202/303 must all be present.  On the tier-1 data BOTH policies
     are INTERNAL_GATE_FAIL, so the expected outcome of this run is a better
     relative number and a still failing absolute one.  Which factor fails
     matters and was previously stated wrongly: on the candidate G3 misses both
     floors, G4 and G5 miss on SURVIVAL with tracking already above 0.70
     (0.7286 and 0.7217), and G7 misses on tracking alone.  The next dial is
     chosen from that breakdown, so getting it backwards would send the search
     after the wrong factor.  A policy that wins Q1 and loses Q2 is the new
     screening baseline, not the entry.

  Three outcomes for Q1, decided in advance:

    candidate total above Pilot-01, no scenario product regression past the limit
        -> dial kept; G-A017 becomes the frozen screening baseline
    candidate total above Pilot-01 but a scenario product regressed past gate
        -> record both, keep Pilot-01 as the screening baseline, and read the
           videos before promoting anything
    candidate total at or below Pilot-01
        -> the tier-1 gain did not survive the wider case set.  Pilot-01 stays
           the screening baseline.  This is one training run at one value, so
           it closes 1.4 as a value, not the direction as a whole.

  This run does not itself select a next reward variable.  The three evaluation
  seeds are three replays of one trained policy, not three independent training
  seeds, so they bound measurement noise and not training variance.
  Official evaluator and official results remain OFFICIAL_RESULT_UNMEASURED.
