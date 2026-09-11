# G-A027 A017 Independent Video Review

- Evidence layer: visual observation only. No survival rate, tracking proxy, internal score, or official score was adjudicated.
- Policy-mapping limit: mapping uses the `evaluation/a017/videos/` path and the colocated case `metadata.json` `scenario_id`. Policy hash embedding in the MP4 itself was not verified.
- Common sampling: 2%, 15%, 30%, 50%, 70%, 85%, and 98% of each video. G3-G6 were additionally reviewed every 0.5 seconds from 0.5 to 9.5 seconds.

| Scenario | Video verdict | Observation | Limitation | SHA256 |
|---|---|---|---|---|
| G1 | VIDEO_OBSERVED | Multiple robots changed position on flat terrain in the commanded forward direction. No clearly prone body posture was visible in sampled frames from 0.2 to 9.8 seconds. | Exact velocity tracking, survival of all 32 environments, and transient events between sampled frames were not adjudicated. | `0f3524eafa070b08993df67efc752e8e707ea38e0e76d6f763aa6df3c3fe20cb` |
| G2 | VIDEO_OBSERVED | Multiple robots displayed locomotion and upright gait on flat terrain. No clearly prone posture was visible in sampled frames from 0.2 to 9.8 seconds. | Camera perspective and arrows do not permit quantitative diagonal-left tracking or survival adjudication for every environment. | `86c1f1628d0cc162ecc4b9231e3e4adc2418c9ae01c3035da63da31c8f18a5d1` |
| G3 | VIDEO_OBSERVED | Robots moved over visibly rough terrain. No clearly prone body posture was visible in frames sampled every 0.5 seconds from 0.5 to 9.5 seconds. | Only the visible robots can be observed. Rough-terrain completion, tracking accuracy, and all 32 environment states were not adjudicated. | `6dfcbf6bbd2679cf0cd97faf06ea416798712614eb57ca0e0dfcd6bc45b7cff0` |
| G4 | VIDEO_OBSERVED | Robot movement was visible on a slope or ramp surface. No clearly prone posture was visible in frames sampled every 0.5 seconds from 0.5 to 9.5 seconds. | Camera perspective cannot establish the exact +20-degree angle, successful completion, or quantitative tracking. | `64f07eb5bccc5b914ae73a0d2e6f49deb55ceb77a3d7807ef526f6754fa53c1f` |
| G5 | VIDEO_UNKNOWN | Stair structures and robots moving on nearby flat ground were visible, but sampled frames from 0.5 to 9.5 seconds did not show a robot contacting and climbing the stair steps. The visible robots were not clearly prone. | This video cannot establish successful or failed 15 cm stair ascent. Robots appear to remain in flat corridors between stair structures, and other environments may be outside the camera view. | `5b56ffb9e7d739d34c314f16be10b43146b439cff8184e77a66fa8132cc9413a` |
| G6 | VIDEO_UNKNOWN | Blue spheres moved around robots on flat terrain. The visible robots were not clearly prone in frames sampled every 0.5 seconds from 0.5 to 9.5 seconds. | The distant multi-environment view does not resolve direct sphere-body impact and the immediate recovery sequence. Push-recovery success cannot be adjudicated. | `f10665150ee4b4a01be9e64f8c2079381aaf71f39a8b513d6772b494255f7d61` |
| G7 | VIDEO_UNKNOWN | Robot movement and gait were visible on rough terrain, with no clearly prone posture in sampled frames from 0.2 to 9.8 seconds. | Domain-randomization parameters and application cannot be verified from pixels. G7 DR execution, all-environment survival, and tracking were not adjudicated. | `8fe4fc062d768e942334251a7737a4abc9360540f1fc21fe55278bdf8da21192` |

## Decision Boundaries
- G3: rough-terrain movement and non-prone posture at sampled times are `VIDEO_OBSERVED`; all-environment survival and tracking remain unmeasured here.
- G4: slope-surface movement and non-prone posture at sampled times are `VIDEO_OBSERVED`; +20-degree completion and quantitative tracking remain unmeasured here.
- G5: stair structures are visible, but no stair ascent was confirmed; verdict remains `VIDEO_UNKNOWN`.
- G6: moving blue spheres and non-prone postures are visible, but direct impact and recovery were not resolved; verdict remains `VIDEO_UNKNOWN`.
- G7: rough-terrain movement is visible, but DR application cannot be established visually; the G7 condition verdict remains `VIDEO_UNKNOWN`.
