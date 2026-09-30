# NConnect 파일·artifact 운영 정본

## GO2-EXTERNAL-FIRST-STUDY-20260930 — C1 정정 추가 기록
- 기존 작업의 로컬 문서 정정: C1 우선 선정 철회, 연구 정본 §11 및 Go2 상태·일정 원장 동기화. 이전 선정 완료 문구는 정정 전 이력이다.
- 근거: 기존 원인 기록·9월 29일 체공 판독·G-A057 사전등록 대조. 새 실험 결과가 아니다. 신규 최적값 선정은 미완료다.
- 원자료·외부 E0·발행 ZIP·사전등록 판정 보존. 서버 실행·다운로드·병합·새 정책 생성 없음.

## GO2-EXTERNAL-FIRST-STUDY-20260930 — 외부 우선 조사·기존 증거 대조
- 상태: PLANNED → RUNNING(로컬 문서 작성·기존 회수물 읽기). 새 서버 실행·다운로드·병합 없음.
- 사용자 범위: Go2 사족, Isaac Sim 5.1 기준 계단·우회전·험지·밀침 사례/강좌를 먼저 조사하고 외부 기준을 고정한 뒤 A043/A048 및 전체 실험과 대조.
- 산출물: `workspace/training/quadruped/upload/plan/GO2_EXTERNAL_FIRST_TUNING_STUDY_20260930.md`.
- 기존 회수물은 읽기만 하며 원본·사전등록·배포 코드를 변경하지 않는다. 새 정책/영상 없음(VIDEO_NOT_REQUIRED: 문헌·기존 증거 연구). 실행 패키지 발행·성능 승급을 뜻하지 않는다.
- 연구 문서 작성·제한 범위 증거 검토 완료. E0 SHA·참조 파일·문서 차분 확인. 사용자 요청의 신규 최적값 선정은 미완료이며 전체 튜닝 완료로 보고하지 않는다. 새 회수/병합 상태 전이는 없다.
- 후속 사용자 정정 반영: 같은 정본 §10에 C1(A048 + feet_air_time .15) 연구값 선정·경쟁 후보 비교 완료. 위 '값 미선정'은 이전 상태다. 성능 검증·실행 ZIP·학습은 미수행이고 회수물은 변경하지 않았다.

## G-A053-PACKAGE-20260928 — A048 보상 위 목록 밖 항 `dof_acc_l2 −2.5e−7→−3.0e−7` 전수 수집 패키지
- 상태: PLANNED → RUNNING(로컬 제작·검증) → 발행 v1 → **실행 권고 철회(Codex·메인 루프, 2026-09-28), 사용자 처분 미정.** 사용자 원칙 '근본 원인 → 강좌 보상 예측'을 두 단계 모두 충족하지 않는다(경위 `workspace/training/quadruped/reports/GO2_G_A053_PRINCIPLE_REVIEW_20260928.md`). ZIP·사양·판정은 불변 보존하고, 서버에 올린 기록은 없다. 회차 G-A053은 upload·사양·원장에 미사용임을 확인했다.
- 결정:
  - Codex 후보 선택(사용자 중계): G-D-A053-DOFACC-20260928
  - 목록 밖 항 허용(사용자): G-D-U1-APPROVED-20260928. 열린 결정 U1-R6-ENV-REWARD-20260918 → APPROVED.
  - 계획: `workspace/training/quadruped/upload/plan/GO2_G_A053_PLAN_20260928.md`
- 발행: `workspace/training/quadruped/upload/G-A053/current/GO2_G_A053_a048_dof_acc_m3e7_full69_v1.zip` SHA256 `52d99463217cb001a156d3658b24a7b99ae1ee03f6c9e4fb2d2f1eda414f89ea`(release `20260928_a048_dof_acc_m3e7_full69_v1`).
  - 후보 보상은 A048 학습 보상 6개에 `"dof_acc_l2": -3e-07` 한 줄을 더한 것이다. A033 대비로는 `lin_vel_z_l2 −1.25`와 이 줄이 다르다.
  - 러너·평가기는 A051과 같은 저장소 러너다.
- 로컬 검증:
  - 사양 발행 검증 통과(detectability·정본 정합성 관문 포함), 재빌드 일치, LF, `bash -n`, 내부 SHA 일치
  - 계약 `tools/test_go2_g_a053_package_contract.py` 16/16
  - 서버 env-rewards 검사가 A048 학습 env.yaml(−2.5e−7)은 거부하고 −3e−7은 통과함을 패키지 안의 검사기로 확인
- 빌더 확장:
  - `tools/build_go2_a033_reward_package.py`가 보상 기준(reward_base)과 목록 밖 항을 함께 쓰는 회차를 허용한다. 목록 6개가 보상 기준 값 그대로일 때만이다.
  - 그 회차의 `expected_rewards.json` candidate에 목록 밖 항을 넣어 서버가 대조하게 했다.
  - 이전 회차 바이트는 불변이다(A051 재빌드 일치 확인).
- 배포 report.html 한계: `go2_task/_finalize.py`는 이 항을 표시하지 않는다. 적용 증거는 학습 env.yaml과 `training/ENV_REWARD_CHECK.txt`다.
- 판정: 채택은 A033 대비 `fact_rules_v1` + `g3_guard_margin_v1`(문턱 불변), 효과는 A048 대비(G-A051과 같은 규칙).
  - 가설: 험지 옆걸음 낙상 ≤8이면 지지, ≥16이면 미지지.
  - 비용만 줄고 감속·정지하면 기각한다.
  - 낙상이 줄어도 계단·저자세 회복이 악화하면 채택하지 않는다.
  - 인접값을 자동으로 반복하지 않는다.
- 영상 사전 판정: **필수.** 후보 10편(G-A051과 같은 목록), 기준선 대응 10편은 저장본 SHA를 재사용한다.
- 판독 시 구분(Codex 사양 검토, 계획 §7):
  - 가중 비용이 아니라 가중치로 나눈 값으로 비교한다(학습 로그만). 평가 조건의 관절 가속도는 이 패키지로 `[미측정]`이다(평가 telemetry에 관절 열 없음).
  - 저자세 회복은 첫 episode `height_rel` 경로로 직접 읽는다. 판독할 수 없으면 보호 확인 미완료다.
  - A033 보호 충족은 A048 이득 보존이 아니다. REVIEW_CANDIDATE는 최종 채택이 아니다.
- 회수 필수 목록:
  - 학습 bundle, iter900 checkpoint
  - `_keep/go2_g_a053_a048_dof_acc_m3e7/exported/report.html` 원본
  - 69 case telemetry, sentinel 5, 영상 10
  - SHA 목록, 지형 레벨, `training/ENV_REWARD_CHECK.txt`
- 실행: `unzip -oq /workspace/GO2_G_A053_a048_dof_acc_m3e7_full69_v1.zip -d /workspace && bash /workspace/go2_g_a053/server_run_go2_candidate_iter_pinned.sh`
  - 예상 약 95분, 회수 포함 120~150분
  - 결과 `/workspace/_keep/GO2_G_A053_RESULT.zip`, 완료 표식 `[DONE] GO2_G_A053_RESULT_READY`

## G-A055-PACKAGE-20260929 — A043 보상 위 `ang_vel_xy_l2 −0.05→−0.08` 전수 수집 패키지 (조건부 준비)
- **회수·판독 2026-09-29 (RECEIVED → VERIFIED → ANALYZED → REPORTED):** 결과 `workspace/_keep/GO2_G_A055_RESULT.zip` SHA `bc90ff9117d0fb6fc068f4960d638ee1e99046ea97c4512f15ebf5bd1dde3a60`(sidecar 일치), FULL_69_COMPLETE, REPORT_ACQUIRED, 영상 10편, 판독기 결손 없음. 채택 FAIL · screening INTERNAL_GATE_FAIL · 가설 NOT_SUPPORTED(험지 옆걸음 50) · A043 대비 NOT_REVIEW_CANDIDATE(44.62454→40.47516). 우회전 29→0(속도·점수 상승), 험지 옆걸음 24→50, 밀침 3방향 WORSE, 계단 15cm ≥2단 77→0. 판독 `workspace/training/quadruped/reports/GO2_G_A055_READOUT.md`.
- (이전) 상태: 실행 선택 — 사용자 서버 실행 대기(Codex 결정 G-D-A055-SELECTED-20260929). 설정 확정: A043 기준 flat_orientation_l2=0 유지, ang_vel_xy_l2 −0.05→−0.08만 변경. 발행 v2 ZIP과 사전등록을 그대로 쓴다(재발행·새 조합 패키지·추가 분석 없음). 근거: flat 강화는 A047에서 자세 수평화는 얻었으나 험지 낙상 미개선·감속·추종 손실이 동반된 직접 반대 관측이 있고, ang 강화는 G-A038 험지 옆걸음 자세 낙상 59→18(A033 기준 1단계) 지지 관측이 있다. 판독: 우회전·험지·밀침 1순위, 계단은 기존 보호 기준. 낙상 감소가 감속·추종 포기로 얻어진 것인지 반드시 함께 판독(1순위 case마다 case 점수·속도를 낙상과 나란히). 성공해도 초기 기울기·재접지 실패의 원인이 증명됐다고 기록하지 않는다.
- (이전) 상태: 조건부 준비본 보존 / 실행 비권고(Codex 결정 G-D-A055-NOT-RECOMMENDED-20260929). 패키지·사전등록은 수정하지 않는다. 근거: G-A056은 실패 기전을 좁혔지만(몸의 이동에 지지점 갱신이 따라가지 못함), 준비한 G-A055를 선택할 근거는 확보하지 못했다. 발 재배치 실패의 발생 이유는 미확정이다.
- (이전) 상태: 조건부 준비 / 실행 미승인(Codex 2026-09-29). G-A056 회수·판독 뒤 Codex가 실행 여부를 정한다. G-A056과 연결하지 않는다.
- 발행: `workspace/training/quadruped/upload/G-A055/current/GO2_G_A055_a043_ang_vel_xy_m008_full69_v2.zip` SHA256 `5a0efce583dc6b30da83d83ccac6a7c275a97566d255508844b410f320b0a75c`(release `20260929_a043_ang_vel_xy_m008_full69_v2`). v1 `592fc332f90f…`은 실행 전 대체(history 보존).
- 실행(승인 시): `unzip -oq /workspace/GO2_G_A055_a043_ang_vel_xy_m008_full69_v2.zip -d /workspace && bash /workspace/go2_g_a055/server_run_go2_candidate_iter_pinned.sh`. 결과 `/workspace/_keep/GO2_G_A055_RESULT.zip`.
- 사양 `workspace/training/quadruped/config/experiments/G_A055_a043_ang_vel_xy_m008.json`, 사전등록 `workspace/training/quadruped/upload/plan/GO2_G_A055_PLAN_20260928.md`.
- 판독 다섯 줄(안내문 §5): 채택 검증기, screening, 가설, A043 대비 효과, `tools/go2_g_a055_readout.py`(§4 1순위 case).
- 로컬 검증: 발행 검증(detectability·정본 정합성) 통과, 재빌드 일치, 관문 `tools/test_go2_g_a055_package_contract.py` 11개 통과. 발행 모듈에 안내문 선택 필드(status_ko·extra_readers)를 더했고, 기존 회차 안내문 8개는 재생성 바이트가 같다.
- 시간: 실행 약 95분, 세션 120~150분. G-A056과 같은 세션이면 합계 약 3~4시간(추정). 잔여 TTL·예산이 G-A055 세션 150분 이상이고 사용자 승인이 있을 때만 이어서 한다.

## G-A056-A043-DIAG-REPLAY-20260928 — A043 진단 재생 (학습 없음 · 보상 변경 없음)
- 상태: PLANNED → 발행 v1(`7d4d6fe7…8398`, 실행 전 대체) → **발행 v2 ARTIFACT_VERIFIED, 서버 실행 승인 대기**(2026-09-28). 서버 실행 없음. 2026-09-29 Codex 검토: ZIP SHA 일치·계약 테스트 23개 재현 통과, v2 실행 권고(재발행 없음). 카메라 판정 설명을 구현에 맞춰 정정(카메라 prim − eye 오프셋으로 되짚은 원점과 대상 몸통의 수평 거리).
- 요청: Codex 2026-09-28 「승인 요청용 준비 지시」·「제작·검증 지시」. 계획 `workspace/training/quadruped/upload/plan/GO2_G_A056_A043_DIAG_REPLAY_PLAN_20260928.md`.
- 발행: `workspace/training/quadruped/upload/G-A056/current/GO2_G_A056_a043_diag_replay_v2.zip` SHA256 `6f82da12d56ca511f0748dd897ff7c8152aae034dc64950d08a6fa10ed19c17e`(release `20260928_a043_diag_replay_v2`). 빌더 `tools/build_go2_a043_diag_replay_package.py`(`--check` 재빌드 동일).
- 실행: `unzip -oq /workspace/GO2_G_A056_a043_diag_replay_v2.zip -d /workspace && bash /workspace/go2_g_a056/server_run_go2_a043_diag_replay.sh`
- 범위: A043 iter 900(model `4d923681…bd6b`, env `9af8f18a…a06d`, 평가기 `353614…0d84`) · rough_lateral·combined_yaw_right seed 202 · plain+diag 4회(관절 채널 포함) + 로봇 지정 영상 4회(험지 env 5·11, 우회전 env 3·16, 카메라 계측 포함).
- 회수 필수: `/workspace/_keep/GO2_G_A056_RESULT.zip`(+.sha256). 종료 게이트: 로컬 `tools/verify_go2_a043_diag_replay_harvest.py <ZIP>` — 0 끈다 / 3 켠 채 복구 판단, 복구 불가면 exception_evidence 확인 후 이 항목에 예외 종료 결정(미완료 항목·사유·받은 것·unknown 질문)을 적고 끈다('회수 완결'·'진단 성공' 아님) / 1 끄지 않고 재회수.
- 시간: 서버 켜진 시간 추정 25~35분, 계획 예산 45분(추정; 32 env 카메라 실행 미측정).
- 판독: `tools/go2_a043_diag_readout.py`(첫 episode만, 축 A·B, t_act). 관문 `tools/test_go2_g_a056_diag_contract.py` 23개 통과. A052 발행물·모듈 보존(A052 `--check` 동일).
- **G-A056 회수 2026-09-29 → RECEIVED → VERIFIED → ANALYZED → REPORTED.** 결과 `workspace/_keep/GO2_G_A056_RESULT.zip` SHA `ad6268407a91e4b8645cac08ce0f4a2d6681f7f13def3f88c771c774f3d25605`, 검증기 종료코드 0(Codex 직접 실행: ARTIFACT_VERIFIED · DIAG_CHANNELS_COMPLETE · 영상 4편 VIDEO_ENV_MATCHED). plain·diag·영상 모두 저장 A043과 차이 0.
  - 판독 `workspace/training/quadruped/reports/GO2_G_A056_DIAG_READOUT_20260929.md`. 증거 `reports/evidence/go2_g_a056_diag_20260928/`(사전등록 출력 + 사후 탐색 SUPPORT_*.csv, 생성 `tools/go2_a056_support_sequence.py`).
  - 판독기 결함 수정: 토크 비율 분모가 PhysX 관절 effort 한계(명시 actuator에서 1e9)라 전부 0.0이었다. 분모를 actuator effort_limit 23.5로 바꾸고 관문 test_12를 추가했다.
  - 결론 요약: 사전등록 축 A·B는 생존 로봇에서도 같은 신호가 잡혀 낙상을 가르지 못했다. 사후 탐색에서 험지는 넘어지는 쪽 발 안쪽 배치 → 반대쪽 하중 상실 → 옆 구름 순서, 우회전은 처음부터 회전 안쪽 기울기 → 바깥 다리 하중 상실·안쪽 앞다리 무릎 끝 편 채 하중 → 구름. 모터 한계는 주원인이 아니다. 발 안쪽 배치의 이유와 우회전 초기 기울기의 이유는 설명하지 못했다. G-A055 실행 결정은 Codex.
  - 발 위치 확인(Codex 지시, 같은 날): `tools/go2_a056_foot_position_check.py` → FOOT_WINDOWS·FOOT_EVENTS·TOUCHDOWNS.csv, 판독 문서 §2-3. 하중 발이 수평으로 몸 밑에 남음 = 확인됨. 다리가 먼저 안쪽으로 움직임 = 반대 관측(발은 거의 제자리, 몸이 옆 이동, hip 목표는 실제보다 바깥). 새 발이 몸 바깥에 놓이지 않음(험지 재착지가 몸 밑, 우회전 안쪽 앞다리가 1 s 넘게 재착지 없음) = 확인됨. 지지 다각형 이탈 = 구분 불가(무게중심 미계측).
  - 변수별 강좌 대조(사용자 질문 답)를 판독 문서 §9에 보존했다. 강좌상 가능한 예측과 실측 효과를 나눴고, 종료/낙상 혼용과 과한 표현을 정정했다. 같은 답의 실행 추천(G-A055 1순위, track 1.4 2순위)은 Codex가 채택하지 않았다.

## G-A052-DIAG-REPLAY-20260928 — A048 진단 재생 (학습 없음 · 보상 변경 없음)
- 상태: PLANNED → 발행 v1 → v2로 대체(실행 전) → RUNNING → RECEIVED → VERIFIED → ANALYZED → **REPORTED**(2026-09-28). 결과 ZIP `workspace/_keep/GO2_G_A052_RESULT.zip` SHA `8427587c9229c21cd1f921f03e62155c96fa5006ee822b3d5a5d72f67a59ebdf`(sidecar 일치), 검증기 종료코드 0 (ARTIFACT_VERIFIED / DIAG_CHANNELS_COMPLETE), 재현 네 쌍 NO_DIFFERENCE_IN_STORED_CHANNELS → **서버 종료 가능**. 판독 정본 `workspace/training/quadruped/reports/GO2_G_A052_DIAG_READOUT_20260928.md`, Codex 분석 `workspace/server_returns/G-A052_CODEX_VERIFY_20260928/DIAGNOSTIC_ANALYSIS.md`. 새 결함 C-39(fall_channel 이름이 reset 뒤 자료를 봄, 경미 OPEN).
- 요청: Codex 2026-09-28 검토(GO2-FAILURE-DATA-20260928 2단계). 계획 `workspace/training/quadruped/upload/plan/GO2_G_A052_DIAG_REPLAY_PLAN_20260928.md`.
- 발행: `workspace/training/quadruped/upload/G-A052/current/GO2_G_A052_a048_diag_replay_v2.zip` SHA256 `828c18cd21bed8b4ce9683480cdf88fb5aa8dc2e1d72871fb549580718cbde62`(release `20260928_a048_diag_replay_v2`). 빌더 `tools/build_go2_diag_replay_package.py`(`--check` 재빌드 동일).
- v1(`09973af1a5b9…`)은 실행 전 대체(Codex 검토 2026-09-28): 판독기가 접촉 결측을 0 지지로 읽음, 검증기 종료코드 0이 필수 파일·키·채널 완결을 보장하지 않음, 접촉 버퍼 갱신 여부 미기록. v2는 계측에 `contact_fresh`·`contact_age_s`를 더했고 판독기·검증기·안내문·계획서를 고쳤다. v1은 history에 불변 보존, 서버에 올린 적 없다.
- 내용: G-A048 iter 900(model `984e6149…`, env `a19077a9…`) · 평가기 schema 6 `353614…` 바이트 그대로 + 읽기 전용 계측 `go2_eval_diag.py`. play.py 4회(plain rough_lateral 202 / diag rough_lateral 202 · stairs_10_down 101 · stairs_15_down 101). 명령은 G-A048 러너 명령과 글자 단위 동일.
- 영상 사전 판정: **NOT_RECORDED** — 이번 진단은 수치 계측으로 제한한다. 녹화기는 별도 4 env 재생이라 이 32 env 재생과 같은 조건이 아니고 env_id와 묶을 수 없다. 충돌 형상은 미확정. 학습 report: 비해당(학습 없음).
- 회수 필수: `/workspace/_keep/GO2_G_A052_RESULT.zip`(+.sha256). 안에 네 실행 steps.csv·summary·STATUS, diag 세 case diag.csv.gz·diag_meta.json·DIAG_STATUS, meta/identity.json·RUN_TIMES·REPRO_STATUS, logs, SHA256SUMS. 종료 게이트: 로컬 `tools/verify_go2_diag_replay_harvest.py` — 0 끈다 / 3(artifact 통과·채널 미확보) 켠 채 복구 판단, 복구 불가면 이 항목에 예외 종료 결정(결측 채널·case·사유·부분 회수분·unknown 질문)을 적고 끈다 / 1 끄지 않고 재회수.
- 판독: `tools/go2_diag_replay_readout.py`(정의는 계획 §4에 결과 전 고정). 관문 `tools/test_go2_g_a052_diag_contract.py`(26/26 — 가짜 회수물로 두 판독기 실행, Codex 재현 입력 두 개 회귀, 검증기 누락·중복·채널 결측 경로 포함).
- 검증기 보완(2026-09-28 Codex 3차 검토, ZIP 불변): 필수 열을 앞왼발 몇 개에서 판독기가 읽는 열 전부(네 발 접촉 시간·수평 속도·높이·주변 지형, roll·pitch 각속도, contact_fresh, action·prev_action 12개씩, diag_meta reward_weights에 등록된 보상 항마다 rew_<항> 열)로 넓혔다. reset 행이 아닌 모든 행의 빈칸·NaN·Infinity를 열마다 건수·첫 위치로 기록하고 하나라도 있으면 종료코드 3. 보완 전 판(RR_contact_time 전체 결측도 0)은 서버 종료 근거로 쓰지 않는다.
- 한계: Isaac Lab 실물 미실행. API 이름은 v2.3.1 원문 대조(`reports/evidence/go2_g_a052_isaaclab_api_20260928/`).

## GO2-FAILURE-DATA-20260928 — 험지 옆걸음 낙상 직전 사건표 (로컬 1단계)
- 상태: PLANNED → ANALYZED → REPORTED(로컬 자료만, 서버 없음). 작업 키 중복 없음 확인.
- 계획: Codex `workspace/training/quadruped/upload/plan/GO2_FAILURE_DATA_REQUEST_CODEX_20260928.md` §4. 결과 `workspace/training/quadruped/reports/GO2_FAILURE_DATA_FINDINGS_20260928.md`.
- 입력(읽기만): `_keep/go2_g_a048_…`, `_keep/go2_g_a033_…`, `_keep/go2_g_a038_…`의 `rough_lateral` steps.csv 9개(경로·SHA는 PROVENANCE.json). 계단은 `go2_stairs_process_20260927/ENV_TIMELINE.csv` 재사용.
- 산출: `workspace/training/quadruped/reports/evidence/go2_failure_data_20260928/`(EVENTS·EVENTS_COUNT_CHECK·FAMILY_SUMMARY·CHANNEL_AVAILABILITY·CANDIDATE_COMPARISON·PROVENANCE). 생성 `tools/go2_failure_events.py`, 관문 `tools/test_go2_failure_events_contract.py`(7/7).
- 2단계 진단 재생: Codex 준비 지시(2026-09-28) → G-A052로 발행(위 항목). 서버 실행은 사용자 결정.

## G-A051-PACKAGE-20260927 — A048 보상 위 `ang_vel_xy_l2 −0.05→−0.06` 전수 수집 패키지
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v3**. 서버 실행은 사용자 결정. 회차 G-A051: upload·사양·원장에 미사용 확인.
- 결정: Codex 후보 선택(사용자 중계) G-D-A051-ANGVEL-20260927, 계획 `workspace/training/quadruped/upload/plan/GO2_G_A051_PLAN_20260927.md`. 선택 책임은 Codex, 사양·패키지·원장은 메인 루프.
- 발행: `workspace/training/quadruped/upload/G-A051/current/GO2_G_A051_a048_ang_vel_xy_m006_full69_v3.zip` SHA256 `21b666ae1d9a4024c657db63353aee3de643836037d7d3fd55f197dbd25446bb`(release `20260927_a048_ang_vel_xy_m006_full69_v2`). 후보 보상은 A048 학습 보상 대비 `ang_vel_xy_l2` 한 줄, A033 대비 두 줄(`lin_vel_z_l2 −1.25` 포함). 러너·평가기·배포 코드는 A050 ZIP과 바이트 동일. LF·`bash -n`·내부 SHA 33건 통과.
- v1(SHA `22d3ea56…53ba`)은 실행 전 대체됐다(결함 C-38): 사양이 발행 경로가 돌리지 않던 관문 둘에 걸렸다 — 원장(`reports/runs/`) 인용 행 없음(test_12), 열 수 없는 경로 표기 셋(test_14). 보상·문턱·러너·코드는 같고 `experiment.json` 문구와 체크섬만 다르다. v1은 history에 불변 보존, 서버에 올린 적 없다. 발행 빌더는 이제 detectability·정본 정합성 관문 전체를 돌려 이 사양 이름이 붙은 실패가 있으면 발행을 거부한다.
- v2(SHA `f0b5b40a…4069`)도 실행 전 대체됐다(외부 검토 2026-09-27): 효과 판독이 확인한 것보다 크게 말했다 — PROGRESS를 진보 판정이라 불렀지만 A048 대비 계단·밀침·복합 회전 손실은 공개만 했고, 속도 하한을 '감속 아님'이라 불렀고, `QUANT_SUCCESS_VIDEO_REVIEW_PENDING`을 '채택 PASS'라 불렀다. v3은 판독 범위만 좁혔다. 보상·문턱·러너·코드는 같다.
- 판정: 채택은 A033 대비 `fact_rules_v1` + `g3_guard_margin_v1`(문턱 불변). 통과 값 `QUANT_SUCCESS_VIDEO_REVIEW_PENDING`은 영상 검토 전 정량 조건 충족이다. 효과는 A048 대비 — 가설 험지 옆걸음 ≤8 지지/≥16 미지지(9~15는 '감소했지만 목표 미달'), 정량 후보 검토 대상(REVIEW_CANDIDATE)은 정량 조건 충족·가설 지지·총점 ≥ A048·험지 옆걸음 속도 크기 ≥0.164(보조 하한) 넷 모두(`tools/go2_reward_base_comparison.py`). **REVIEW_CANDIDATE는 최종 진보 판정이 아니다** — A048 대비 보호 case의 허용 손실은 사전등록하지 않았으므로 사람이 차이를 읽은 뒤에 진보 여부를 정한다.
- 판독 순서(회수 뒤): 채택 검증기 → screening(`--rule-version g3_guard_margin_v1`) → 가설 판독기 → A048 대비 효과 판독기. 정량 조건을 충족해도 NOT_REVIEW_CANDIDATE면 튜닝 진보로 보고하지 않는다. 보호 실패·A048 대비 개선 미확보면 기각, −0.055·−0.065 자동 탐색 없음.
- 영상 사전 판정: **필수.** 후보 10편(G-A050과 같은 목록, seed 101, 4env·500step), 기준선 대응 10편은 저장본 SHA 재사용.
- 회수 필수 목록: 학습 bundle·iter900 checkpoint·`_keep/go2_g_a051_a048_ang_vel_xy_m006/exported/report.html` 원본·69 case telemetry·sentinel 5·영상 10·SHA 목록·지형 레벨(700/800/900/999).
- 실행 `unzip -oq /workspace/GO2_G_A051_a048_ang_vel_xy_m006_full69_v3.zip -d /workspace && bash /workspace/go2_g_a051/server_run_go2_candidate_iter_pinned.sh`, 재개 `GO2_RESUME=1 bash /workspace/go2_g_a051/server_run_go2_candidate_iter_pinned.sh`, 진행 `tmux attach -t go2_g_a051`. 예상 약 95분(G-A044 실측 기반 계획치), 회수 포함 120~150분. 결과 `/workspace/_keep/GO2_G_A051_RESULT.zip`, 완료 표식 `[DONE] GO2_G_A051_RESULT_READY`.

## GO2-GOAL-FIRST-PACKAGE-20260927 — 목표 우선 단일변수 패키지 제작
- 상태: PLANNED → RUNNING(로컬 제작·검증). 사용자 요청: 튜닝 정책 만들어줘. 회차 G-A050 예약: upload·사양에 미사용 확인, 과거 seed43 미래 계획 번호는 실제 발행이 아니며 해당 계획은 추후 재번호 부여.
- 계획: `workspace/training/quadruped/upload/plan/GO2_GOAL_FIRST_POLICY_RESET_20260927.md`. A033 위 lin_vel_z_l2 −2.0→−1.375, seed42/1000iter/eval900. 중간 성능을 예측하지 않는 한 회차 공동충족 탐색이다.
- 영상 필수: 후보10편(좌우 복합회전·험지2·계단2·밀침4), seed101·4env·500step; 대응 기준선10편 SHA 재사용. 정량은 3seed·32env, full69+sentinel5.
- 필수 회수: 원 학습 report.html(평가 export 전 보존), 학습 로그·env·checkpoint900 및 best·identity·telemetry·영상·manifest·결과 ZIP/SHA. 로컬 검증 전에 서버 종료하지 않는다.
- 예산: 실행 약95분/회수 포함120~150분 계획치. 잔여 서버·팀 예산 미측정. 서버 실행·GPU 소비 없음. 기존 ZIP·회수물 불변.

## G-A050-PACKAGE-20260927 — A033 위 `lin_vel_z_l2 −2.0→−1.375` G3 표적 전수 수집 패키지 (계단은 보호만)
- 상태: PLANNED → RUNNING → 발행 v2 → 사용자 실행 → RECEIVED(`workspace/_keep/go2_g_a050_a033_lin_vel_z_m1375/`) → VERIFIED(Codex 격리 검토 `workspace/server_returns/G-A050_REVIEW_20260927/`, ZIP SHA `ba6d6c3f…63b1`, 536건 일치, 영상 10·재사용 10) → **ANALYZED**(메인 루프 재계산 일치). MERGED 없음. 결과: INTERNAL_GATE_FAIL, 총점 47.25453. 다음 변수 분석 `workspace/training/quadruped/upload/plan/GO2_NEXT_REWARD_LEVER_20260927.md`. 사용자 결정 G-D-G3-FIRST-20260927, 계획 `workspace/training/quadruped/upload/plan/GO2_G3_FIRST_20260927.md`.
- 발행: `workspace/training/quadruped/upload/G-A050/current/GO2_G_A050_a033_lin_vel_z_m1375_full69_v2.zip` SHA256 `5f825566d02098c9f6719087bbecb03b01a645fe9f746a3e6e7fc71d1e0dfe0f`(release `20260927_a033_lin_vel_z_m1375_full69_v2`). 보상 파일 차이는 `lin_vel_z_l2` 한 줄, 러너는 저장소 러너, LF·`bash -n` 통과. 관문 `tools/test_go2_g_a050_package_contract.py` 12/12(안내문 명령 세 줄 실행·검증기 대역 경로·보호 14검사만 판정 포함).
- v1(SHA `02c68b1e…87a811`)은 실행 전 대체됐다. 외부 검토 3건 때문이다: 밀침 보호 설명이 옛 판 문구였고, 계단 역할에 옛 수직 벌점 가설 문장이 남아 있었고, 걷기 예측("rules out a standing policy")이 과했다. 문턱·값·코드는 같고 v1은 history에 불변으로 남는다.
- 이전 초안: 같은 번호의 계단 공동충족 초안(Codex 제작, 한글이 `?`로 손상되고 경로 치환 오류 `m137525` 등)은 발행 전에 폐기하고 A049 사양에서 다시 만들었다. 그 초안의 ZIP은 검증된 발행본이 아니다.
- 채택: `fact_rules_v1`(문턱 불변) + 계획 screening `g3_guard_margin_v1`(새 판: 계단 개선·정체 묶음 없음, 보호 14검사 허용 손실은 `post_a048_guard_margin_v1`과 같음). 향후 사양 전용이며 A048·A049를 재판정하지 않는다.
- 판독 순서(회수 뒤): 채택 검증기 → screening(`--rule-version g3_guard_margin_v1`) → 가설 판독기(`tools/go2_dial_hypothesis.py G-A050`). **A048 대비 변화량을 필수로 공개한다.** 대상은 총점, G1~G7, 험지 옆걸음, 계단 두 높이, 밀침 네 방향, 복합 우회전이다. 새 판에서 PASS가 나와도 그것만으로 진보라고 보고하지 않는다. 험지 가설이 미지지이거나 불충분하면 수치를 조금 바꾼 자동 재실험은 없다.
- 영상 사전 판정: **필수.** 후보 10편(G-A049와 같은 목록, seed 101), 기준선 대응 10편은 저장본 SHA 재사용.
- 회수 필수 목록: 학습 bundle·iter900 checkpoint·`_keep/go2_g_a050_a033_lin_vel_z_m1375/exported/report.html` 원본·69 case telemetry·sentinel 5·영상 10·SHA 목록.
- 실행 `unzip -oq /workspace/GO2_G_A050_a033_lin_vel_z_m1375_full69_v2.zip -d /workspace && bash /workspace/go2_g_a050/server_run_go2_candidate_iter_pinned.sh`, 재개 `GO2_RESUME=1 bash /workspace/go2_g_a050/server_run_go2_candidate_iter_pinned.sh`, 진행 `tmux attach -t go2_g_a050`. 예상 95분, 서버 세션 120~150분. 결과 ZIP·`.sha256`을 받은 뒤 로컬 회수 검증이 끝날 때까지 서버를 끄지 않는다.

## G-A049-PACKAGE-20260927 — A033 위 `lin_vel_z_l2 −2.0→−1.0` 전수 수집 패키지 제작 (분기 B 탐색)
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v3**. 서버 실행·회수·병합은 없다 — 실행은 사용자가 한다.
- 발행: `upload/G-A049/current/GO2_G_A049_a033_lin_vel_z_m1_full69_v1.zip` SHA256 `c7df9b6f6bdb0e73a557d45f248305accc7b37a0f2b5c1356a22f644e0bf0863`(release `20260927_a033_lin_vel_z_m1_full69_v1`). 러너는 저장소 러너, 보상 파일 차이는 `lin_vel_z_l2` 한 줄, `run_config.env`·러너 LF, `bash -n` 통과. 계약 테스트 12/12(안내문 명령 세 줄 실행·검증기 대역 경로 포함).
- 판독 순서(회수 뒤): 채택 검증기 → screening(`--rule-version post_a048_guard_margin_v1`) → 가설 판독기(`tools/go2_dial_hypothesis.py G-A049`). 회수물을 추가·교체하면 채택 검증기부터 다시 돌린다.
- 영상 사전 판정: **필수.** 후보 10편(G-A048과 같은 목록, seed 101, 4env×500step), 기준선 대응 10편은 저장본 SHA 재사용.
- 회수 필수 목록: 학습 bundle·iter900 checkpoint·`_keep/go2_g_a049_a033_lin_vel_z_m1/exported/report.html` 원본·69 case telemetry·sentinel 5·영상 10·SHA 목록. 누락은 `REPORT_REQUIRED_NOT_ACQUIRED` / `VIDEO_REQUIRED_NOT_ACQUIRED`.
- 예상 95분, 서버 세션 120~150분. 잔여 GPU 미측정.
- 판독 규칙(2026-09-27 외부 검토): 우회전 PRESENT/ABSENT는 후보 표본의 발생 여부이지 인과 비용이 아니다. 15cm 기록만은 가설 판정에만 해당하고 채택 조건은 그대로다. G6는 가설 문턱이 없어 보호 충족·변화량으로만 보고한다. 재개는 `GO2_RESUME=1 bash /workspace/go2_g_a049/server_run_go2_candidate_iter_pinned.sh`(재압축 해제 없이), 끊김이면 먼저 `tmux attach -t go2_g_a049`.
- 서버 유지: 결과 ZIP·`.sha256` 다운로드 뒤 **로컬 회수 검증이 끝날 때까지** 서버를 끄지 않는다.

## GO2-GUARD-DESIGN-20260926 — 보호 설계 비교(현재 + 대안 둘), 사용자 결정 대기
- 정의(계산 전 고정): 놓치면 안 되는 악화 = 보호 case 하나에서 seed마다 낙상 +3대 또는 추종 −0.02. 허용 손실 = 그 절반 내림(+1대/seed, −0.01). G-A048에는 어느 설계도 적용하지 않았고 판정은 보존된다.
- 결과(저장 G-A033 조건부 재표집): current 거짓 실패 `0.9975`·놓침 평균 `0.012` / margin `0.7415`·`0.054`(최악 `0.314`) / resample 1% `0.1045`·`0.245`(최악 `0.91`). 대안 둘 다 두 오류를 함께 낮추지 못한다. 막는 것은 잡음이 큰 세 case(10cm 오르기, 험지 옆걸음, 험지 전진 추종)다. 밀침은 margin으로 충분하다.
- 15cm는 기준선이 바닥(`90`/96)이라 상대 보호가 거의 작동하지 않는다. 절대 부족(G5)은 별개로 남는다.
- **사용자 선택(2026-09-26): ①.** 계산 결과 margin_split 거짓 실패 `0.548`, 자기 정의 악화 놓침 평균 `0.033`(최악 `0.218`). 선택 당시 보지 못한 수치라 사전등록은 재확인 뒤에 한다. 재확인에서 사용자가 중복 검사 제거 재계산을 골랐고, 결과는 14검사 거짓 실패 `0.519`·놓침 평균 `0.035`(최악 `0.218`)다. 중복 제거 효과는 작았다(§7). **사용자 선택으로 14검사판을 `post_a048_guard_margin_v1`로 사전등록했다**(`tools/go2_screening_gate.py`, 관문 `tools/test_go2_guard_margin_rule_contract.py`). 향후 사양 전용이며, 기존 판과 G-A048 판정은 그대로다(§8).
- **결정 요청:** ① margin + 잡음 큰 세 case의 악화·허용 손실 따로 정의(권고) ② 세 case 평가 로봇 수 증가 ③ current 유지(FAIL은 참고 신호). 문서 `workspace/training/quadruped/reports/GO2_GUARD_DESIGN_COMPARISON_20260926.md`, 도구 `tools/go2_guard_design_compare.py`.

## GO2-D2-D3-20260926 — 보호 검사 재표집 민감도 · G-A048 영상 판독
- **D2:** screening `post_a043_push4_v1` 보호 22검사(개선 9검사 제외)를 저장된 G-A033 arm의 로봇 궤적 재표집(case·seed별 32대, 2,000회)으로 셌다. 보호 검사 하나 이상 실패 `0.9985`, 회당 실패 수 중앙값 `8`/22. 검사별 `0.09~0.49`. **저장 표본에 조건부인 재표집 민감도이며 서버 재실행 오판율이 아니다.** 문턱·G-A048 판정 불변. 도구 `tools/go2_guard_resampling.py`(원 시행 재계산이 screening 값과 일치할 때만 실행).
- **D3:** G-A048 영상 10편 프레임 판독(전체 VIDEO_UNKNOWN). 15cm 오르기는 3초부터 첫 단 앞에서 앞다리가 접힌 자세로 머묾. 밀침 네 방향은 표본 프레임에서 네 로봇 모두 서 있음. 판단 보류 세 구간(우회전 4.3~5.7초, 좌회전 약 9.5초, 10cm 5.7~9.9초)은 사용자 확인 요청.
- 진행 순서(외부 검토 권고): 메인 루프 D2·D3 완료 → 사용자 D4(제출 이력·마감·잔여 예산)·U2 문의 → 그 결과로 D1 결정. 문서 `workspace/training/quadruped/reports/GO2_D2_D3_GUARD_RESAMPLING_AND_A048_VIDEO_20260926.md`.

## G-D-ROLE-CODEX-READONLY-20260926 — 판독·원장 작성 역할 분리 (사용자 전달 합의)
- **Claude 메인 루프:** 정본 판독·정책 문서·원장을 쓴다.
- **Codex:** 기본은 읽기 전용 검토다. 수정은 명시적으로 맡긴 파일·범위만 한다. 별도 검토 파일이 필요하면 정본과 **다른 경로**를 쓴다.
- 계기: 2026-09-26 G-A048 판독 경로 `workspace/training/quadruped/reports/GO2_G_A048_READOUT.md`를 양쪽이 같은 시각대에 썼다. 메인 루프 판본(미추적)이 덮였고, 고유 분석은 `workspace/training/quadruped/reports/GO2_G_A048_ANALYSIS_SUPPLEMENT.md`로 복원했다. NOW·MASTER에 생긴 중복 항목은 병합했다.
- 용어 정정: 외부 검토의 `STAY`는 **세션 유지 표시**다. 새 서버 작업 금지나 판단 요청(D1~D4) 순서 승인의 뜻이 아니다. U2(학습 seed 반복 결정)는 seed 변경 실험에만 적용된다. D1~D4 순서는 미결이다.

## G-A048-READOUT-20260926 — G-A048 회수물 검증·판독
- 상태: RECEIVED → VERIFIED → ANALYZED → **REPORTED**. MERGED 없음(NO_CANONICAL_MERGE) — 회수물은 `workspace/_keep/go2_g_a048_a033_lin_vel_z_m125/`에 그대로 둔다.
- 결과 ZIP `workspace/_keep/GO2_G_A048_RESULT.zip` SHA256 `89698d3f806e0dd321610148bb36cc6f425e2a3c5752d59ca2e6692bab307389`(`.sha256` 일치), 537 항목 CRC 정상·경로 안전, 내부 `SHA256SUMS.txt` 536건 일치.
- 검증 순서: 채택 검증기(`tools/verify_go2_basic_motion_harvest.py G-A048 --out …/harvest_verification.json`, 기존 JSON 사본과 내용 동일) → screening(`tools/go2_screening_gate.py --rule-version post_a043_push4_v1`, INTERNAL_GATE_FAIL) → 가설 판독기(`tools/go2_dial_hypothesis.py G-A048`, harvest_check verified).
- 영상 판정: 필수 · 생성 10 · 로컬 10(+기준선 재사용 10 SHA 확인) · identity 10 · 행동 판독 VIDEO_UNKNOWN(프레임 4장씩 3 case만 추출, 판정 아님).
- 미측정: G1~G7 영상 행동, 공식 결과, 학습 경로 흔들림.
- 판독 경로는 21:41 외부 검토 판본으로 덮였다(수치 충돌 없음). 메인 루프 판본의 고유 분석은 `workspace/training/quadruped/reports/GO2_G_A048_ANALYSIS_SUPPLEMENT.md`에 보존했다.
- 증거 `workspace/training/quadruped/reports/evidence/go2_g_a048_readout_20260926/`, 판독 `workspace/training/quadruped/reports/GO2_G_A048_READOUT.md`, 정책 평가 `workspace/training/quadruped/upload/plan/GO2_TUNING_POLICY_ASSESSMENT_20260926.md`.

## G-A048-PACKAGE-20260926 — A033 위 `lin_vel_z_l2 −2.0→−1.25` 전수 수집 패키지 제작 (관측 범위 확장 탐색)
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v3**. 서버 실행·회수·병합은 **없다** — 실행은 사용자가 한다.
- 실행 순서: **U2는 이 회차(학습 seed 42)의 선행조건이 아니다** — U2 답을 기다리지 않고 실행할 수 있다(2026-09-26 외부 검토 정정). U2가 나중에 허용되면 v10은 미사용 번호(현재 기준 G-A049·G-A050)로 따로 재발행한다. **두 패키지를 같은 세션에서 돌리지 않는다.** 회수물을 추가·교체하면 채택 검증기부터 다시 돌린다.
- 계획 `workspace/training/quadruped/upload/plan/GO2_A043_YAW_RIGHT_AND_NEXT_20260926.md` §4, 사양 `config/experiments/G_A048_a033_lin_vel_z_m125.json`, 발행 도구 `tools/build_go2_full_collection_release.py`, 가설 판독기 `tools/go2_dial_hypothesis.py`, 관문 `tools/test_go2_g_a048_package_contract.py`(11검사).
- 발행: `upload/G-A048/current/GO2_G_A048_a033_lin_vel_z_m125_full69_v1.zip` SHA256 `bbbfbb258f4101a01e65f51dd6092df7866ff81a39cc9809c8f602efc659f3bc` (release `20260926_a033_lin_vel_z_m125_full69_v1`). 러너는 저장소 러너(바이트 동일), 보상 파일 차이는 `lin_vel_z_l2` 한 줄. ZIP CRC 정상, `run_config.env`·러너 LF, `bash -n` 통과.
- 판정: 채택은 `fact_rules_v1` + `post_a043_push4_v1`, 문턱은 G-A044와 글자 그대로 같다. 가설 판정 세 지표(계단 15cm ≥2단 `50`/`10`, 험지 옆걸음 낙상 `41`/`59`, 복합 우회전 낙상 seed 수 `2`/`0`)는 채택과 별개이며 아무것도 막지 않는다.
- 영상 사전 판정: **필수.** 후보 10개(`combined_yaw_left`·`combined_yaw_right`·`rough_forward`·`rough_lateral`·`stairs_10_down`·`stairs_15_down`·`push_pos_x`·`push_neg_x`·`push_pos_y`·`push_neg_y`, 모두 seed 101, 4env×500step). 기준선 대응 10개는 전부 저장본 SHA·지문 재사용 — 기준선 신규 렌더 0. 영상은 seed 101·4대·500 step이고 정량은 3 seed·각 32대라 같은 표본이 아니다 — 정량에서 우회전 낙상이 나와도 영상에는 안 나올 수 있고, **영상에서 못 봤다는 이유로 정량 결과를 부정하지 않는다**(2026-09-26 외부 검토 정정: 옛 문장은 비용이 재발하면 이 영상이 첫 행동 영상이 된다고 적었으나 그런 보장은 없다).
- 회수 필수 목록(실행 시): 학습 bundle·iter900 checkpoint·`_keep/go2_g_a048_a033_lin_vel_z_m125/exported/report.html` 원본·69 case telemetry·sentinel 5·영상 10·SHA 목록. 누락은 `REPORT_REQUIRED_NOT_ACQUIRED` / `VIDEO_REQUIRED_NOT_ACQUIRED`.
- 예상 95분(G-A044 실측 94분/1팔 기준), 서버 세션 120~150분. 잔여 GPU·팀 시간은 원장에 없어 **미측정** — 사용자가 세션 전에 확인한다.
- **로컬 검증 완료는 성능 판정이 아니다.** 서버 실행·GPU 소비 0.

## G-A047-PACKAGE-20260926 — A033 위 `flat_orientation_l2 0.0→−0.5` 전수 수집 패키지 제작 (G3 험지 생존 탐색)
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v3**. 서버 실행·회수·병합은 **없다** — 실행은 사용자가 한다.
- 실행 순서: U2(seed 변경 허용)가 **허용**이면 동결된 v10(G-A045·G-A046)이 먼저다. 불허·무응답이면 이 회차. **두 패키지를 같은 세션에서 돌리지 않는다.**
- 계획 `workspace/training/quadruped/upload/plan/GO2_G_A047_PLAN_20260926.md`, 사양 `config/experiments/G_A047_a033_flat_orientation_m05.json`, 발행 도구 `tools/build_go2_full_collection_release.py`, 관문 `tools/test_go2_g_a047_package_contract.py`(11검사, 문턱 한 개 이동 조작을 잡음 확인).
- 발행: `upload/G-A047/current/GO2_G_A047_a033_flat_orientation_m05_full69_v2.zip` SHA256 `10dccd6b933f074bbdfd7df6551c59ddbf866785f75491442157229cd00029de` (release `20260926_a033_flat_orientation_m05_full69_v2`). v1(`092793dc…`)은 history에 불변 보존, **실행하지 않는다** — 계획 screening을 통째로 빼 밀침 ±y·−x가 G6 합산 한도로만 판정됐다(v2 사유). 러너는 v10 팔과 같은 저장소 러너(바이트 동일), 보상 파일 차이는 `flat_orientation_l2` 한 줄.
- 판정: `fact_rules_v1`, 문턱은 G-A044와 글자 그대로 같다. 계획 screening은 보호 전용 판 `g3_guard_push4_v1`(신규 판 이름, `post_a043_push4_v1`과 같은 보호 묶음 코드·8 case — 밀침 네 방향 각각 낙상·생존·추종)로 바꿨고, 계단 **개선**·정체 감소 두 묶음만 뺐다(계획 §4 보호 대응표). 등반 수·전진거리·정체시간은 필수 기록.
- 영상 사전 판정: **필수.** 후보 8개(`rough_lateral`·`rough_forward`·`slope_plus_20`·`stairs_10_down`·`stairs_15_down`·`push_pos_x`·`combined_yaw_right`·`forward_fast`, 모두 seed 101, 4env×500step). 기준선 대응 8개는 전부 저장본 SHA·지문 재사용 — 기준선 신규 렌더 0.
- 회수 필수 목록(실행 시): 학습 bundle·iter900 checkpoint·`_keep/go2_g_a047_a033_flat_orientation_m05/exported/report.html` 원본·69 case telemetry·sentinel 5·영상 8·SHA 목록. 누락은 `REPORT_REQUIRED_NOT_ACQUIRED` / `VIDEO_REQUIRED_NOT_ACQUIRED`.
- 예상 95분(G-A044 실측 94분/1팔 기준), 서버 세션 120~150분. 잔여 GPU·팀 시간은 원장에 없어 **미측정** — 사용자가 세션 전에 확인한다.
- **로컬 검증 완료는 성능 판정이 아니다.** 서버 실행·GPU 소비 0.

## G-A045-A046-PACKAGE-20260924 — 학습 seed 43 대칭 쌍(자를 재는 회차) 제작
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v3**. 서버 실행·회수·병합은 **없다** — 실행은 사용자가 한다.
- A044 회수로 `lin_vel_z_l2` 는 걷는 기준선 위에서 세 점이 측정됐는데, **계수기가 서로 다른 말을 한다** — 계단에 오른 로봇 수는 단조로 늘고(10cm ≥2단 `43→62→94`/96, 15cm ≥1단 `4→39→88`/96) 자세 낙상 수는 가운데 값에서만 솟는다(계단10cm `34→65→17`, 험지 옆걸음 `59→80→24`, 밀침 4방향 `22→66→10`/384). 총점 비단조(`42.53→38.89→44.62`)는 낙상 쪽을 따라간 결과다. 이것이 다이얼의 성질인지 학습 경로 갈라짐인지는 **학습 seed 대조군이 0건**이라 가를 수 없고, 회차 간 총점 차이(`−3.63`·`+2.10`)는 승급 문턱(`+2.53`)과 같은 자리에 있다. 그래서 이 회차는 값을 찾지 않고 **자를 잰다**: G-A045 는 G-A033 의 보상 파일 그대로를 학습 seed 43 으로 다시 학습하고(보상 diff 0줄), G-A046 은 같은 seed 위에서 `lin_vel_z_l2 −1.5`(G-A043 과 같은 값)를 걸어 대칭 쌍을 만든다. **판정 문턱·평가 조건·screening 판은 하나도 바꾸지 않았다** — 자를 재는 회차가 자를 바꾸면 읽을 수 없다. **두 팔 다 승급 대상이 아니다**(`promotion: forbidden_not_a_reward_change`): 학습 seed 는 보상 가중치가 아니다. R-6 해석은 열린 결정 **U2-SEED-REPLICATE-20260918** 이고 사용자 결정 대기다 — 사용자가 「실행도 하지 말라」로 닫으면 이 패키지는 폐기한다.
- 계획 `workspace/training/quadruped/upload/plan/GO2_A045_SEED_PAIR_PLAN_20260924.md`, 기준 변경 `workspace/training/quadruped/reports/GO2_A045_CRITERIA_CHANGES_20260924.md`, 사양 `config/experiments/G_A045_seed43_a033_rewards.json`·`G_A046_seed43_lin_vel_z_m15.json`, 발행 도구 `tools/build_go2_seed_pair_package.py`.
- 발행: `upload/G-A045_A046/current/GO2_G_A045_A046_seed43_pair_full69_v8.zip` SHA256 `02c1b36c59e9a5c499b43c46776d69bce7e4d74f63c740ca8719e75d9c3df151` (release `20260924_seed43_pair_full69_v8`). v1 은 같은 날 만든 **로컬 초안**이고 발행된 적이 없다 — 러너 머리말에 열린 결정 번호를 적기 전 바이트다. history 의 바이트는 고치지 않으므로 덮어쓰지 않고 다음 판으로 냈다. 팔 ZIP 둘은 `GO2_G_A045_seed43_a033_rewards_full69_v7.zip` `a6a20361…` · `GO2_G_A046_seed43_lin_vel_z_m15_full69_v7.zip` `4be46723…` 다 — 사양의 「학습 18회」를 원장에서 다시 센 수로 고치면서 팔 바이트도 바뀌어 v2 로 냈다. 쌍 ZIP 안 `arms/` 에 들어 있고 따로 올리지 않는다.
- 러너 `workspace/training/quadruped/server_run_go2_full69_campaign.sh`(신규): 기존 campaign 러너에서 **게이트만 뺀** 판이고 공유 헬퍼 11개는 바이트가 같다. 팔마다 전수 69 로 직행하고, 팔이 팔을 막지 않으며, 재진입은 이름이 아니라 `$SELF` 경로로 한다(결함 C-14 의 교훈). 기존 campaign 발행 경로는 한 글자도 건드리지 않았다.
- v4 사유: **독립 검토가 사전등록한 「읽는 법」 의 오류 넷을 잡았다**(결함 C-26). ① 계단 재현을 B 의 절대값만으로 판정한 것(A 가 70 인데 B 가 50 이면 오히려 나빠진 것이다) — 이제 행동 수준(절대값)과 보상 효과(**같은 seed 의 B−A**)를 따로 읽는다. ② 작은 seed 차이를 「A044 의 비단조는 다이얼 탓」의 근거로 쓴 것 — 이 쌍은 `−1.75` 를 반복하지 않으므로 그 원인은 **미확정**이고, 보상 효과와 학습 경로는 배타적이지도 않다. ③ 큰 차이에서 승급 규칙 폐기·장기 학습 전환을 적은 것 — 한 표본은 그 결론을 지지하지 않고 기존 `INTERNAL_GATE_FAIL` 관측을 무효로 만들지도 않는다. ④ R-6 을 닫힌 것처럼 적은 것 — CLI 인자 전달은 규정 허용의 증거가 아니고, 반대로 공식 제출 불가도 단정하지 않는다(우리 금지는 내부 보수 규칙이며 열린 결정 U2 는 운영진 답변·공식 근거로 닫는 것이 안전하다). **판정 문턱·평가 조건·러너·수집 계약은 하나도 바뀌지 않았다** — 바뀐 것은 읽는 법이다. 같은 판에서 총점이 어디로 갔는지를 산문 대신 같은 채점기의 반사실로 쟀다(`tools/go2_score_decomposition.py` → `SCORE_SPLIT.csv`: A044 는 생존 `−4.62775` · 추종 `+0.99438` · 교차항 `−0.00144`). 관문 `ReviewCorrectionsTest` 7 검사가 네 정정을 고정한다.
- v5 사유: **검토 3차** — 점수 분해를 「기여 분해」로 고쳐 적었다. 세 항의 합이 총점 차이와 같은 것은 교차항을 잔차로 두기 때문이라 **검증이 아니라 정의**이고, 읽을 것은 교차항의 크기다(A044 `0.04%` 대 A043 `79.89%` — 후자는 두 인수로 나누는 것 자체가 약하다는 뜻이다). 어느 쪽이든 **「보상 변경이 낙상을 일으켰다」는 인과는 나오지 않는다.** 값·문턱·러너·수집 계약은 그대로이고 사양 산문과 안내문만 바뀐다. 관문 `ReviewCorrectionsTest::test_32` 가 고정한다.
- v6 사유: **검토 4차** — 잔차 비율의 **분모**를 갈라 적었다. `|교차항|/|순변화|` 는 큰 반대 몫들이 상쇄되면 튀므로 **인과적 기여율도 설명 실패율도 아니다**. 크기합을 분모로 한 값을 함께 싣는다(A044 `0.04%`/`0.03%`, A043 `79.89%`/`30.75%`, A043 순변화는 크기합의 `38.49%`). 두 수가 벌어지는 것 자체가 「상쇄가 심하다」는 신호다. 값·문턱·러너·수집 계약 불변.
- v7 사유: **검토 5차** — ① 「최악이라도 GPU 시간만 잃는다」로 **손실 상한을 긋지 않는다**. G-A033 산출물이 보존된다는 사실과 팀 제출 자격에 영향이 없다는 판단은 별개이고, 서버 실행 자체가 허용되지 않는 행위로 판정될 경우 **제재 범위는 미확정**이다(위반 확정도 아니다 — 허용도 손실 상한도 확정할 수 없다는 뜻). **사용자의 실행 결정만으로 U2 가 닫히지도 않는다.** ② A043 기각을 G2 하나로 좁히지 않는다 — 총점 `+2.09593`이 `+2.53`에 미달(기준 2)했고 비열등 4건(G2 proxy `−0.44161`, `combined_yaw_right` 3 seed 생존)과 screening 3건(`rough_forward`·`push_pos_x`·`push_neg_x`)이 함께 있었다. **유망한 신호와 채택 자격은 분리해 읽는다.** 관문 `test_33`·`test_34` 가 고정한다.
- 로컬 검증: 관문 `tools/test_go2_g_a045_package_contract.py` **31검사 통과**(러너 이름 붙인 차이·공유 헬퍼 바이트 동일·재진입 실행·문턱 불변·승급 금지·영상 짝·ZIP manifest·재빌드 결정성·안내문의 실패 경로 진술). 네 관문은 **반대 방향으로도 확인했다** — 이름 없는 러너 편집, 문턱 한 개 이동, 승급 금지 삭제, 자 팔에 보상 변경을 심으면 각각 떨어진다.
- **느린 관문은 옵트인이다(2026-09-24).** `tools/test_go2_g_a044_package_contract.py` 는 회수물이 생긴 뒤 69 case 의 `steps.csv` 를 통째로 읽게 되어 한 번에 **38분**이 걸렸다 — 그렇게 느린 관문은 일상 스윕에서 돌지 않고, 돌지 않는 관문은 없는 것과 같다. 이제 전수 판독 8 검사는 `GO2_SLOW_TESTS=1` 에서만 돌고(기본은 이유를 말하며 건너뜀), 돌 때는 스스로 시간을 재 예산(`GO2_SLOW_BUDGET_S`, 기본 3000초)을 넘기면 **실패**한다. 같은 수확물을 두 번 읽던 자리는 캐시로 묶었다. **범위를 갈라 적는다**: 같은 범위(34 검사 전부 실행)는 `2288초 → 857초`(중복 읽기 캐시와 배선 검사의 I/O 제거), 기본 경로는 `92초`이며 그때는 **34 중 8 건너뜀**이다 — `38분 → 92초` 는 범위가 다른 두 수를 나란히 놓은 것이라 쓰지 않는다. **회차를 발행하기 전에는 `GO2_SLOW_TESTS=1` 로 한 번 돌린다**(실측 857초) — 건너뛴 관문이 조용히 사라지지 않는지는 `SlowGateIsWiredTest` 가 지킨다.
- **실행 규칙 두 가지를 실측으로 확인했다(2026-09-24).** ① `timeout N cmd | tail` 은 timeout 의 종료 코드를 **가린다**(실측: 파이프 있으면 exit 0, 없으면 124) — 그래서 파이프를 쓸 때는 `set -o pipefail` 을 먼저 켜거나 파일로 받고 `$?` 를 본다. ② `timeout` 은 이 환경에서 손자 프로세스까지 정리했다(1회 실측: 자식을 띄운 python 을 5초에 끊고 2초 뒤 잔존 python 0개). 다만 **테스트 안의 경과시간 검사는 멈춘 작업을 끊지 못한다** — 그것은 끝난 뒤에야 실패를 알리는 사후 신호이고, 실제로 끊는 것은 바깥 `timeout` 과 `subprocess.run(timeout=...)` 이다.
- **로컬 검증 완료는 성능 판정이 아니다.** 서버 실행·GPU 소비 **0**, 잔여 예산 변동 없음.

## G-A044-LOCAL-REVIEW-20260924 — 결과 보존·검증·다음 튜닝 분석
- 상태: PLANNED → RUNNING → RECEIVED → VERIFIED. SHA `10824d2d3025769d101faf150248feccce169eed4a738b3b6439d0b68d5c20c0`; CRC·내부548 SHA·해제본549파일 일치. canonical 병합은 하지 않아 MERGED로 표시하지 않는다.
- 원본은 덮어쓰지 않고 보존하며 `workspace/server_returns/G-A044/`에 검증 기록을 격리한다. 서버 실행 사실은 회수 로그로 확인하며 신규 서버 실행은 하지 않는다.
- 회수 완결: report 원본·학습로그/env·평가900 checkpoint·69case·sentinel5·신규 영상14(전편499프레임 디코딩/지문 일치)·재사용6 SHA/지문 확인. 서버 종료 가능, 추가 필수 회수 없음. VIDEO_UNKNOWN(행동 전체 관찰 미완료), OFFICIAL_RESULT_UNMEASURED.
- 내부 정량 INTERNAL_GATE_FAIL: 42.528610→38.893793/70(-3.634817), A033 유지. 판독문 `workspace/training/quadruped/reports/GO2_G_A044_READOUT.md`, 다음 정책 분석 `workspace/training/quadruped/upload/plan/GO2_POST_A044_POLICY_ANALYSIS_20260924.md`. 분석/보고 기록은 별도 보존하며 원본 lifecycle의 병합을 가장하지 않는다.

## G-A044-PACKAGE-20260922 — A033 위 `lin_vel_z_l2 −2.0→−1.75` 전수 수집 패키지 제작
- 상태: PLANNED → RUNNING(로컬 제작·검증) → **발행 v9 · 사용자 실행 승인(2026-09-23)**. 회수·병합은 아직 **없다** — 서버 실행은 사용자가 하고, 이 줄은 승인 기록이다.
- **2026-09-23 사용자 결정 (G-D-A044-RUN-20260923): v9 로 진행한다.** 사용자가 ZIP SHA·CRC·내부 manifest 32/32 일치, v8→v9 변경이 사양의 발행 식별자와 manifest 뿐(러너·보상·판정 코드 불변), C-23 관문 4개와 C-24 관문 1개 5/5 성공을 직접 확인했다. **C-17 과 C-2 는 이번 실행 전에 고치지 않고 별도 유지보수로 둔다.** 서버 실행은 사용자가 한다 — 이 줄은 승인 기록이지 실행 기록이 아니다. 실행 뒤의 회수 완결 판정은 안내문 §5 의 다섯 줄과 §4 의 세 상태로 내린다.
- 계획 근거: `workspace/training/quadruped/upload/plan/GO2_POST_A043_PLAN_20260922.md` §1~§6·§9. 사양 `workspace/training/quadruped/config/experiments/G_A044_a033_lin_vel_z_m175.json`.
- 발행: `upload/G-A044/current/GO2_G_A044_a033_lin_vel_z_m175_full69_v9.zip` SHA256 `2e12a5667f9ef93015dfcc7247bd10f5b83fcc07473c1ec29f4bca6d18f77ce6`(release `20260922_a033_lin_vel_z_m175_full69_v9`). 대체된 v2 `b3321fb3…acedc`·v1 `f588d9cd…06c09`은 history 보존, 둘 다 서버에 올린 적 없음. v2 사유: v1 안내문이 소요 시간 근거를 영어 원문 그대로 실어 읽히지 않았다. v3 사유: 관문 `test_go2_detectability_gate::test_14`가 사양 산문의 맨 이름 `FORECAST_CHECK.csv`(저장소에 같은 이름 2개)를 잡아 네 자리를 전체 경로로 고쳤다. v4 사유: **v3 는 서버에서 아무것도 돌지 않았을 것이다** — 팔 러너가 tmux 안에서 자기 자신을 다시 부를 때 패키지에 없는 조상 파일 이름(`server_run_go2_candidate_staged.sh`)을 글자로 박고 있었다(결함 C-14). 같은 판에서 회수 명령의 `--keep`(실존하지 않는 선택지, C-15)과 SHA 한 줄로 읽히던 종료 절(C-16)도 고쳤다. **v4 는 산문만 바뀐 판이 아니다 — 러너 바이트가 바뀌었다.** 값·문턱·수집 계약은 여전히 불변이고, 이미 발행된 회차의 바이트도 불변이다(G-A042·G-A043 을 실행된 러너 `6fd78eeb8eac5342` 로 고정했다). v2·v3 은 산문만 바뀐 판이다. campaign 껍데기를 쓰지 않는다 — **1단계 분기도 서버 게이트도 없는 회차**라 회차 ZIP 자체가 실행 단위다. v5 사유: **올릴 ZIP 이름에 판 번호를 넣었다**(결함 C-18, 사용자 지적). 판은 `release_id` 에만 있었고 이름에는 없어 history 에 같은 이름의 ZIP 이 넷 쌓였는데 그중 v3 는 올리면 아무것도 돌지 않는 판이다 — 어느 것인지 가리는 근거가 사람의 SHA 손대조뿐이었다. 이제 사양 검증이 `upload_zip` 끝과 `release_id` 의 `_v<N>` 이 같은지 보고 다르면 빌드를 거부한다(관문 `test_16`). **v5 페이로드는 v4 와 두 줄만 다르다** — `experiment.json` 의 이름·판. 러너·보상·설정 바이트는 v4 와 동일하다. v6 사유: **계획서 `GO2_POST_A043_PLAN_20260922.md` 대조에서 나온 기록 공백 셋**을 메웠다 — ① 안내문이 서버 실행 시간 110분만 적고 계획 §7 의 세션 계획치 120~150분(회수 포함)을 옮기지 않았다 ② 사양이 G-A043 을 63번 인용하면서 그 정책의 model/env SHA 를 고정하지 않았다(`comparison_arm`, 값은 회수 산출물 `G-A043_LOCAL_VERIFY.json` 에서 읽었다) ③ 계획 §9-1 의 c3 상한 `0.567/70` 이 서술로만 있었다. **판정 문턱 19개는 여전히 A043 과 숫자 단위로 동일하고(차이 0), 러너·보상·run_config 바이트는 v5 와 같다** — v6 페이로드 차이는 `experiment.json` 과 그 해시 줄뿐이다. v7 사유: **안내문 §5 의 exit code 설명이 틀렸다**(결함 C-20, 사용자 검토). `두 명령의 exit 1 은 성능 기준 미충족` 은 두 번 틀렸다 — 첫 판독기는 성능 FAIL 에 exit **0** 을 내고(FAIL 이 `PASS_VERDICTS` 안에 있다), 그 명령의 exit 1 은 INCONCLUSIVE·BASELINE_REMEASURE_REQUIRED 곧 **판정 불가**다. 둘째 판독기는 FAIL 과 INCONCLUSIVE 를 같은 exit 1 에 담는다. 이 줄이 **서버 종료 게이트**에 있었으므로 대가는 회수 결손을 성능 실패로 읽고 서버를 끄는 것 — 그때 잃는 것이 영상과 report 다. 관문 `test_20` 은 두 판독기를 빈 수확물로 **실행**해 exit 1 이 성능이 아님을 보이고, 판독기 소스에서 비통과 판정 이름을 읽어 안내문이 그것을 담는지 본다. **값·문턱·러너 바이트는 v6 과 같다** — 페이로드 차이는 안내문과 `experiment.json`·해시 줄뿐이다. v8 사유: **사용자 검토 2회차가 둘을 더 잡았다.** ① ZIP 안의 사양이 아직 `--keep` 을 적고 있었다(결함 C-21 — C-15 를 안내문에서만 고쳤고, 사양은 패키지에 실려 서버로 간다). ② 수집이 중단된 실행이 전수 완료와 똑같이 보였다(결함 C-22 — `finish` 가 조기 종료 경로에서도 `RESULT_STATE=FULL` 과 같은 `[DONE]` 표식을 냈다). 러너가 이제 개수를 세어 `COLLECTION_STATUS` 를 따로 적고 결손이면 `[INCOMPLETE COLLECTION]` 을 찍으며, 종료 게이트가 `COLLECTION_STATUS=FULL_69_COMPLETE` 를 요구한다. **v8 은 러너 바이트가 바뀐 판이다** — 값·문턱·수집 계약은 그대로다. 관문 test_14(안내문+사양 양쪽 명령 실행)·test_21(finish 실행). v9 사유: **안내문이 실패 경로를 잘못 적고 있었다**(결함 C-24, 사용자 검토 3회차). ① `[DONE]` 은 늘 나오지 않는다 — 러너의 `on_exit` crash 경로는 부분 ZIP 과 `COLLECTION_STATUS=INCOMPLETE_CRASH` 만 남기고 표식 없이 끝나므로, 표식을 기다리는 사용자는 오지 않을 줄을 기다리며 휘발 서버의 예산을 태운다. ② 「불완전하면 메운 뒤 종료」는 복구 가능한 누락에만 맞다 — 파국 게이트가 멈춘 판은 정책이 실행되지 않은 판이고 69 를 채우는 것이 오히려 러너의 계약(STOP_UNSAFE)과 충돌한다. 안내문 §4 를 세 상태(정상 완료 / 복구 가능한 누락 / crash·안전상 평가 불가)로 나누고 §5-a 와 종료 문장이 그 구분을 따르게 했으며, `FULL_69_COMPLETE` 가 개수 확인일 뿐 SHA·지문·identity·report 검사를 대신하지 않는다고 적었다. 관문 test_22 가 발행된 러너의 crash 경로를 실행해 표식 부재를 보인다. **러너 바이트는 v8 과 같다** — v9 페이로드 차이는 `experiment.json` 의 판 이름 두 줄과 그 해시 줄뿐이고, 안내문이 바뀌었다. 같은 판에서 결함 C-23(옛 `pinned = staged + 핀 블록` 동치 관문이 C-14 이후 빨간 채로 남아 다음 회귀를 가리고 있었다)을 **관문만 고쳐** 닫았다 — 러너를 건드리지 않았고 v8 ZIP 은 같은 SHA 로 재빌드된다. 발행 도구 `tools/build_go2_full_collection_release.py`.
- 수집 계약: `run_config.env`가 `GO2_STAGE=full`을 고정한다(러너가 그 파일을 source 한 **뒤** STAGE를 정하므로 명령줄 선택이 아니라 패키지 계약이다). 학습 → 파국 게이트 → **69 case 전수**(평가 seed 101/202/303 × 32env) → sentinel 5 → 영상 → 결과 ZIP 하나. 근거는 결함 C-11(A043의 결정적 손실이 1단계 23 case 밖이었다).
- 영상 사전 판정: **필수.** 후보 10개(`combined_yaw_left`·`combined_yaw_right`·`rough_forward`·`rough_lateral`·`stairs_10_down`·`stairs_15_down`·`push_pos_x`·`push_neg_x`·`push_pos_y`·`push_neg_y`, 모두 seed 101, 4env×500step) + 기준선 신규 4개(G2 양방향·G6 ±y — 이 네 case의 G-A033 영상이 없다). 기준선 나머지 6개는 SHA·지문 대응 확인된 기존 영상 재사용(`go2_g_a041_*` 2 · `go2_g_a042_*` 1 · `go2_g_a033_*` 1 · `go2_g_a043_*` 2). 밀침 영상 재사용은 결함 C-13(빌더 지문이 `PUSH_X`/`PUSH_Y`를 상수로 박아 둠)을 고친 뒤에 가능했다.
- 회수 필수 목록(실행 시): 학습 bundle·iter900 checkpoint·`_keep/go2_g_a044_a033_lin_vel_z_m175/exported/report.html` 원본·**69 case 전부**의 telemetry·sentinel 5·영상 14개(후보10+기준선4)·SHA 목록. 누락은 `REPORT_REQUIRED_NOT_ACQUIRED` / `VIDEO_REQUIRED_NOT_ACQUIRED`로 기록하며 회수 완결로 보고하지 않는다.
- 기준 변경 근거는 별도 문서: `workspace/training/quadruped/reports/GO2_G_A044_CRITERIA_CHANGES_20260922.md`. **판정 문턱은 하나도 바꾸지 않았다** — 넓힌 것은 수집(전수)과 보호(밀침 네 방향, screening 판 `post_a043_push4_v1`)뿐이다. 결함 C-12·C-13은 원천 수정(대장 `reports/GO2_DEFECT_LEDGER.md`).
- **서버 실행은 사용자 결정 사항이다.** 로컬 검증 완료는 산출물 무결성이며 성능·통과 판정이 아니다.

## G-A043-LOCAL-REVIEW-20260922 — 다운로드 검토
- 상태: PLANNED → RUNNING → RECEIVED → VERIFIED. 원자료는 workspace/_keep에 보존하며 기존 정본 병합·덮어쓰기 없음.
- 결과 ZIP SHA256: `9a5e7d2858702c1a766421cf221c8b3233e3b98043c914bb65b345366c68c8c6`. 외부 SHA·CRC·안전경로·내부 SHA 530항목·압축 해제본 531파일 대조 불일치 0. campaign ZIP도 외부 SHA·CRC·내부 SHA 5항목 일치. generic tar 검증기는 ZIP 비지원이므로 ZIP 전용 대조로 확인.
- 필수 회수: 원 학습 report·env·로그·iter900 checkpoint, 후보69 telemetry, sentinel5, 신규 영상 후보6+기준선2, 재사용 기준선4 SHA 일치. 서버 종료 가능; 추가 필수 회수 없음. 성능 판독은 진행 중이며 무결성 검증을 성능 판정으로 쓰지 않는다.

- Review complete: INTERNAL_GATE_FAIL; A033 retained. See reports/GO2_G_A043_READOUT.md and workspace/server_returns/G-A043_LOCAL_VERIFY.json. No MERGED transition: raw files retained in inbox without canonical merge. Analysis and user reporting completed.

## G-A043-PACKAGE-20260922 — A033 위 `lin_vel_z_l2 −2.0→−1.5` 실행 패키지 제작
- 상태: PLANNED → RUNNING(로컬 제작·검증). 서버 실행·회수·병합은 **없다.** 새 학습도 없다.
- 발행: `upload/G-A043/current/GO2_G_A043_a033_lin_vel_z_m15_one_command.zip` SHA256 `68480a13f96bf7032462ce852238fcbbaaeb726e66638a9d7502cbc154dcda45`(release `20260922_a033_lin_vel_z_m15_one_command_v3`). 대체된 v2 `69f20613…1891c`·v1 `90661e80…f0b11c`는 history 보존, 둘 다 서버에 올린 적 없음. v3 사유: 2차 검토가 사양 산문 두 곳(±y "짝 비교 불가" 오기, 상한 집계 범위)을 잡았다.
- 영상 사전 판정: **필수.** 후보 6개(`stairs_10_down`·`stairs_15_down`·`rough_forward`·`rough_lateral`·`push_pos_x`·`push_neg_x`, 모두 seed 101, 4env×500step) + 기준선 신규 2개(`push_pos_x`·`push_neg_x` — 이 두 case의 G-A033 영상이 없다). 기준선 나머지 4개는 SHA·지문 대응 확인된 기존 영상 재사용(`go2_g_a041_*` 2개, `go2_g_a042_*` 1개, `go2_g_a033_*` 1개). 근거: reward 변경 run이고 후보 채택/폐기 판단에 쓰므로 §2에 따라 필수.
- 회수 필수 목록(실행 시): 학습 bundle·iter900 checkpoint·`_keep/go2_g_a043_a033_lin_vel_z_m15/exported/report.html` 원본·1단계 22 case telemetry(계단 15cm 3seed·밀침 −x 3seed·±y 2 포함)·sentinel 5·영상 8개(후보6+기준선2)·SHA 목록. 누락은 `REPORT_REQUIRED_NOT_ACQUIRED` / `VIDEO_REQUIRED_NOT_ACQUIRED`로 기록하며 회수 완결로 보고하지 않는다.
- 기준 변경 8건의 근거는 별도 문서: `workspace/training/quadruped/reports/GO2_G_A043_CRITERIA_CHANGES_20260922.md`. v1의 ±y 제외 근거는 `tools/go2_reward_mechanism.py` `PUSH_CASES`(네 방향)와 충돌해 철회했고, 표지를 복원해 1단계 22 case로 확대했다. 결함 C-8·C-10은 원천 수정(대장 `reports/GO2_DEFECT_LEDGER.md`).
- 로컬 검증 완료: 사양 `validate_spec` 통과, 재빌드 일치, 계약 테스트 `tools/test_go2_g_a043_campaign_contract.py` **32/32 통과**(v3 발행 바이트 기준 — `PackageTest` 21 · `GateAndVerifierTest` 6 · `PlanReadersTest` 5). 원장·관문 재확인 53/53(`test_go2_canonical_consistency`·`detectability_gate`·`tuning_base_data`·`defect_ledger`). 남은 기존 실패는 결함 C-2(G-A035·A037·A039 발행 ZIP 재빌드 불일치)뿐이고 G-A043과 무관하다. **로컬 검증 완료는 성능·통과 판정이 아니다.**

## G-A042-LOCAL-REVIEW-20260921 — 다운로드 분석
- 상태: PLANNED → RUNNING → RECEIVED. 사용자 회수 `workspace/_keep/GO2_G_A042_RESULT.zip` 및 campaign ZIP·SHA와 풀린 run을 읽기 전용 검사한다. 기존 정본 병합·덮어쓰기는 하지 않는다.
- 필수: 해당 학습 report·로그·env·iter900 checkpoint, 사전등록 표적 telemetry(10/15cm 포함), 후보4·기준선1 신규 영상 및 재사용 영상 대응. SHA·필수 목록 확인 전 서버 종료 판정 보류.
- 분석: A033 대비 계단 진행·정체·낙상·험지 추종, fact_rules와 계획 screening을 분리 확인. 파일 존재는 VIDEO_OBSERVED가 아니다.
- RECEIVED → VERIFIED. 결과 ZIP SHA `7c6b3439f3f5cbe6d19b95f62208f6d1fac36d5c4780f775a72f66b09e856c89`, 외부 SHA/CRC/안전경로/内部232 SHA 항목/풀린 파일 대응 불일치0. 로컬 판독 artifact/stage/identity faults0. generic tar 검사기는 ZIP 비지원이며 ZIP 검사로 대체했다.
- 후보21 telemetry·sentinel5·후보4/A0331 신규 영상(각499frame,9.98s) 및 원 학습 report 회수 확인. 영상 후보4종 표본 직접 관찰; 전수 연속행동 미확인. 사전등록 재사용 기준선과 sentinel5/5 일치. **서버 종료 가능**, 필수 추가 회수 없음. 전체69case는 TARGET_FAIL로 미실행(회수 누락 아님).
- 분석·보고 완료, 기존 정본 병합은 비해당이므로 MERGED로 기록하지 않는다. INTERNAL_GATE_FAIL, A033 유지. 보고 `workspace/training/quadruped/reports/GO2_G_A042_READOUT.md`; 원 자료는 변경하지 않음.

## G-A042-REPAIR-20260921 — 계획·감사에 따른 실행 패키지 수정
- 상태: PLANNED → RUNNING. 사용자 지정 제작 계획·감사·재개 지점에 따른 로컬 수정/검증/재발행. 서버 실행·새 학습·회수·병합 없음.
- 기존 A042 current 전체를 SHA 대조하여 history에 보존한 뒤 새 release ID로 발행한다. 기존 회수 자료와 다른 회차 release는 변경하지 않는다.
- 회귀검사: required case 삭제, wrong/missing identity, 통합 fact_rules+계획 screening, stationary/TARGET_FAIL 필수 수집, env별 진단·coverage, 테스트 출력 격리.
- 새 실행의 영상 필수: rough_forward/rough_lateral/stairs_10_down/stairs_15_down seed101 양팔. 기준선 3개는 기존 사양 SHA·identity로 재사용, 15cm만 신규. 두 높이 포함 12 표적+초기 보호 기록은 성능 실패와 무관하게 수집한다.
- 원 학습 report는 평가 전에 `_keep/go2_g_a042_a033_track_lin_vel_xy_160/exported/report.html`에 보존하고 결과 ZIP/SHA에 포함. 로컬 도구 변경 자체는 VIDEO_NOT_REQUIRED. 서버 결과/행동/공식 점수는 미측정.
- REPORT_READ_STATUS=READ_MATCHED(학습 run 대응, 평가 성능 판정 아님): A033/A041의 `_keep/<run>/exported/report.html` 본문을 직접 읽고 TRAIN_STATUS/CHECKPOINT_PIN과 대조. A033 09-15 21:29~22:27, 1000iter, report-best700·최고19.28@651·track1.5; 평가900 model `ccd60e19…6044`. A041 09-21 10:02~10:59, 1000iter, report-best700·최고19.79@681·ang_vel_xy−0.04; 평가900 `f4c0b929…c8e8`. HTML의 학습 평균/일반 설명을 행동·기전 증거로 승격하지 않는다. A042 report는 아직 생성되지 않음.
- C-6 테스트 출력 격리: feet_air_time builder 시험은 TemporaryDirectory에서만 생성하며 기존 발행 파일 SHA 불변을 검사(6 tests 성공). 수정 릴리스 외 과거 ZIP을 재생성하지 않음.
- 로컬 수정 완료·보고: A042 v4 `current/` SHA `a95d3b6d2164354381e850ed7749d4c97d3a6df6ae02ef5bb4f29ef8dda06133`, ARTIFACT_VERIFIED. 집중53개 성공; A04226개 중25개 성공+기존 문구 기대1개 수정 후 단독 재검사 성공. `upload/G-A042/REPAIR_VALIDATION.json`에 실패·재검사·비관련 A040 경로검사 실패를 구분 보존. 서버 실행/회수/병합 상태를 완료로 올린 것이 아니다.

## G-A042-PACKAGE-REVIEW-20260921 — 실행 전 패키지 감사
- 상태: PLANNED → RUNNING. 발행 ZIP·사양·러너·계획 §4 판독기를 읽기 전용 대조한다. 서버 실행·결과 회수·병합 없음.
- 발행 ZIP을 재작성하는 전체 테스트는 실행하지 않는다. 한정 테스트와 합성 반례만 임시 경로에서 수행한다.
- 영상: VIDEO_NOT_REQUIRED — 이번은 새 정책 행동 평가가 아닌 실행 패키지 계약 감사다.
- 로컬 감사 완료: ZIP CRC/외부·내부 SHA 일치, 전용26검사26/26 OK. 계획 판정 미연결·지문 검사 누락·정지 early-stop 수집 누락 등으로 서버 실행 미해제 유지. 보고서 `workspace/training/quadruped/reports/GO2_G_A042_PACKAGE_AUDIT_20260921.md`. 다운로드 lifecycle의 RECEIVED/MERGED는 이번 작업 비해당; 과거 발행물 변경 없음.

## G-A041-LOCAL-REVIEW-20260921 — 다운로드 검토
- 상태: PLANNED → RUNNING → RECEIVED. 사용자 제공 `workspace/_keep/GO2_G_A041_RESULT.zip` 및 campaign ZIP, SHA, 풀린 폴더를 검사한다. 외부 실행은 회수 로그로 확인하며 기존 정본에 덮어쓰기/병합하지 않는다.
- 목적: A041 단일변수·iter900 대응, 원 학습 report, 표적 telemetry·영상 회수 및 예측/실측 대조. 서버 종료 여부는 필수 목록 검증 후 결정한다.
- 영상: 필수; 사양의 후보 4개·기준선 2개 신규 영상과 기존 재사용 영상 대응을 확인한다. 영상 파일 존재와 행동 관찰은 구분한다.

## G-DATA-STANDARD-20260920 — 데이터 의미 명세 및 표준 뷰
- 상태: PLANNED → RUNNING. 기존 집계표 다섯 종의 생성 정의 감사와 표준화. 신규 서버 작업/학습/회수/병합 없음.
- 입력: TILT.csv, SITUATIONS.csv, PROBE_SITUATIONS.csv, FALL_CHANNEL_ROLLUP.csv, CLIMB_REWARD.csv 및 해당 생성 코드, 보관 Isaac 원문, 강좌 14·15 HTML.
- 출력: config/go2_evidence_data_dictionary.json, GO2_DATA_STANDARD.md, 로컬 표준 뷰 reports/evidence/go2_standardized_v1/standardized.json. 기존 CSV는 불변.
- 영상: VIDEO_NOT_REQUIRED — 행동 성능이 아닌 데이터 정의와 변환 무손실성 검사. 실제 정책 개선 판정 없음.
- 로컬 결과: 5개 표 129행 표준 뷰 생성, 원본 셀/명세/고유키/유한수/누락·대리식 분류 회귀 검증. 신규 회수·병합 단계는 비해당. 전체 raw 재계산/정책 성능 개선 검증이 아님. 자세한 완료 범위는 GO2_DATA_STANDARD.md §5.

## G-AUDIT-EVIDENCE-LIVE-20260920 — 역할 인계 동작 감사
- 상태: PLANNED. 사용자 요청: 증거 관리자 추가 산출물을 실제로 동작시키고 결과 감사.
- 범위: 기존 A033 보존 자료의 모집단·수식 출처를 읽기 전용 재확인하고 증거 관리자 → 분석가 → 기획자 → 독립 감사자 → PM 인계를 시험한다. 새 학습·다운로드·병합·정책 변경 없음.
- 검증: 역할 계약/정본 일치 및 추론·역할 회귀 테스트. 테스트 성공과 사실적 추론의 타당성을 별도로 보고한다.
- 영상: VIDEO_NOT_REQUIRED — 새 정책/행동 평가가 아닌 기존 수치의 출처·모집단 인계 감사. 기존 영상의 행동을 새로 판정하지 않는다.
- 기록: 이 작업 행과 에이전트 응답; 새 성능 원장이나 실행 패키지 생성 없음.
- 진행: PLANNED → RUNNING. 기존 로컬 자료 재독해 작업 완료; 신규 회수·병합이 없어 RECEIVED/VERIFIED/MERGED를 새로 주장하지 않는다.
- 로컬 검증: `python -B -m unittest tools.test_go2_evidence_role_contract tools.test_go2_canonical_consistency -q` 19/19, `python -B -m unittest tools.test_go2_inference_integrity_contract tools.test_go2_role_situation_exam_contract tools.test_go2_role_regression_contract -q` 17/17 성공(총 36, 서로 다른 테스트). 독립 감사의 evidence+detectability 19검사는 이 수에 합산하지 않음.
- 실제 인계: evidence_live(증거 관리자) → data_reaudit(분석가) → plan_reaudit(기획자) → audit_reaudit(독립 감사) → PM. READ_ONLY로 A033 rough_lateral의 FALL_CHANNEL_ROLLUP tilt-only 9/8/13과 TILT seed101 base-contact19 대 non-base-contact13의 .31123/.05106/AUC .838을 분리했다. 원자료: `workspace/training/quadruped/reports/evidence/go2_a038_reread_20260919/FALL_CHANNEL_ROLLUP.csv`, `workspace/training/quadruped/reports/evidence/go2_reward_mechanism_20260917/TILT.csv`. 독립 감사가 per-env로 세 seed의 tilt-only가 base-contact 집합에 포함됨을 확인했으나 정의상 일반 관계는 아님.
- 수식 한계: Isaac 보관 원문 gx²+gy²와 계측 1-gz²의 동치는 unit-norm 가정 필요. 이번 감사에서는 norm 미확인. 종료 전 창과 전체 episode 평균의 비대칭도 유지. report best700과 평가 iter900 구분. 연관 근거이지 reward 효과나 -0.5 최적값 근거가 아님.
- 감사 결함 재현: `_check_rows`는 `run,score,other / A,1.5,9.8`에서 A의 score를9.8로 잘못 설명해도 수용. INFORMATION_RUN은 RECOMMENDED 전용 R6/번호/readout/원장 등 검사를 우회. 역할 계약 테스트는 링크·필드 존재만 검사. 이 턴은 실행·감사이며 결함 수정을 수행하지 않음.
- PM 결과: 제한된 실제 인계의 사실 분리 확인. 자동 검증의 충분성은 기각. 가장 쉬운 점수 상승/특정 가중치 우월성은 미확정. 서버 실행·학습·패키지 발행 없음. 보고 완료, 다음 수정 대상은 열 단위 근거 연결과 실행 후보 공통 검증이다.

> **역할:** 서버 작업의 계획, 파일 목록, 다운로드, 검증, 선택 병합, 작업 이력을 한곳에서 추적한다.  
> **대상:** 메인 팀장, 스케줄러, 기획자, 분석가, 보고서 작성자, 서버 실행 사용자.  
> **갱신 방식:** 작업 시작 전에 행을 만들고, 증거가 생길 때 같은 행의 상태만 전진시킨다. 과거 행은 삭제하지 않는다.  
> **갱신일:** 2026-08-31

## 0. 예선 기준 현재 위치

- [예선 목표] 시뮬레이션 70점 후보의 H1~H7 실제 행동과 설계 의도 20점·리포트 10점의 영상 증거를 확보한다.
- [현재 단계] **단계 1/6 — H4 정량 기본 행동 게이트.** H4 yaw 추종량이 가장 이른 미완료 증거다.
- [확보] Run06 10,000 iter·model_9900·학습/영상 artifact 정합, 사전등록 수치 게이트 5/5 PASS, H1~H3·H5 시각 PASS.
- [미확보] H4 양방향 yaw 추종량, H6 tracking·termination, H7 밀침 회복시간, 독립 seed.
- [이번 테스트] 추가 학습 없이 Run06 고정 정책의 H4·H6·H7 원시 telemetry를 회수한다.
- [흐름] Run06 분석 완료 → **A260831-08 고정 평가** → 정량 판정 → 최종 문서·제출물 정합 → 제출.
- [지금 할 일] 검증된 평가 ZIP을 서버에 올리고 런북의 한 줄 명령만 실행한다.
- [보장하지 않음] 영상 1세트나 단일 seed만으로 공식 survival_rate, 최적 reward, 예선 점수 또는 통과 가능성을 보장하지 않는다.

## 1. 이 문서가 해결하는 문제

서버는 접속마다 초기화되고, 사용자는 서버 명령 실행과 다운로드를 담당한다. 반면 로컬
`C:\dev\Nconnect\workspace\training`은 과거 run·원장·보고서를 보존하는 정본이다. 서버의
`training` 전체를 로컬에 덮어쓰면 새 run뿐 아니라 업로드 당시의 오래된 문서도 함께 돌아와
로컬 정본을 과거 상태로 되돌릴 수 있다.

따라서 모든 서버 작업은 다음 두 결과를 별도로 관리한다.

1. **필수 run bundle:** 해당 run의 checkpoint·tfevents·로그·설정·상태·해시
2. **보험 snapshot:** 서버 `/workspace/training` 전체 사본. 직접 병합하지 않고 복구·누락 확인에만 사용

## 2. 정본 우선순위

충돌할 때 아래에서 위로 덮지 않는다. 위 항목이 우선한다.

1. 실제 회수 artifact와 검증된 내용(`STATUS.txt`, params YAML, tfevents, checkpoint tensor)
2. 이 문서의 artifact 작업 원장과 파일 변경 원장
3. `PROJECT_STATE.md`의 고정 사실·결정·LATEST NEXT
4. `H1_REWARD_EVIDENCE_MASTER.md`의 reward·run 과학 판정
5. `CAMPAIGN_SCHEDULE.md`의 현재 단계·일정
6. `workspace/training/humanoid/upload/plan/CAMPAIGN_PLAN.md`의 장기 방향
7. 개별 보고서와 과거 계획

파일 SHA256은 전송 무결성 증거다. `policy.pt` 동일성은 비결정적 직렬화 때문에 checkpoint
iter + `model_best.pt` SHA256과 `torch.jit.load(...).state_dict()` tensor 비교로 판정한다.

## 3. 역할과 기록 책임

| 역할 | 실행 책임 | 반드시 갱신할 곳 |
|---|---|---|
| 사용자 | 서버 시작, 제공 명령 실행, 결과 tar 다운로드 | 외부 실행 결과를 메인 팀장에게 전달. 원장 갱신 책임은 없음 |
| 메인 팀장 | 명령·회수 경로 확정, 검증, 선택 병합, 최종 상태 보고 | 이 문서, `PROJECT_STATE.md`, 관련 계획·보고서 |
| 스케줄러 | 가장 이른 미완료 단계와 필수/개선/조사 등급 관리 | `CAMPAIGN_SCHEDULE.md`, 이 문서 작업 상태 |
| 기획자 | 단일 변수, 통제 변수, 성공/실패/INCONCLUSIVE, 회수물 사전등록 | `experiment_history.csv`, `H1_REWARD_EVIDENCE_MASTER.md` |
| 분석가 | SHA·설정·seed·지표·checkpoint·H1~H7 측정 범위 판정 | 이 문서 검증 결과, reward 마스터, 해당 보고서 |
| 보고서 작성자 | 검증된 run 식별자와 근거만 인용 | `REPORT_*.md`, `TECH_REPORT_H1.md`, evidence index |

## 4. 관리 파일 목록

### 4-a. 운영·판정 정본

| 경로 | 역할 | 갱신 시점 |
|---|---|---|
| `AGENTS.md` | 모든 담당자가 따라야 할 최상위 운영 계약 | 불변 규칙 변경 시 |
| `ARTIFACT_MANAGEMENT.md` | 파일 목록·artifact lifecycle·작업 내역의 단일 진입점 | 모든 서버 작업 전/후 |
| `PROJECT_STATE.md` | 사실(F)·결정(D)·LATEST NEXT 원장 | 새 사실·결정 즉시 |
| `CAMPAIGN_SCHEDULE.md` | 현재 단계·등급·게이트·다음 일정 | 상태 전이 시 |
| `workspace/training/humanoid/upload/plan/CAMPAIGN_PLAN.md` | 목표·점수축·장기 단계 계획 | 전제·범위 변경 시 |
| `H1_REWARD_EVIDENCE_MASTER.md` | reward 9개와 Run별 과학적 지위 | 새 분석 결과 수용 시 |
| `SERVER_SESSION_RUNBOOK.md` | 서버에서 복사해 실행할 검증된 명령 | 서버 패키지·경로 변경 시 |
| `REPORT_260831.md` | 현재 사용자용 종합 보고 | 캠페인 판정 변경 시 |

### 4-b. 학습·제출 artifact

| 경로/패턴 | 내용 | 병합 규칙 |
|---|---|---|
| `workspace/server_returns/<RUN_ID>/` | 서버 다운로드 최초 격리 위치 | 원본 보존, 여기서 직접 수정 금지 |
| `workspace/training/humanoid/logs/rsl_rl/humanoid/<run>/` | checkpoint, tfevents, params | 검증된 새 run 디렉터리만 추가 |
| `workspace/training/humanoid/reports/experiment_history.csv` | 실험 사전등록·결과 이력 | 기존 행 삭제 금지, Run06은 bundle 판정 후 갱신 |
| `workspace/training/humanoid/reports/*_add.md` | run별 분석 보고 | 대응 run 식별자와 근거 필수 |
| `workspace/training/humanoid/reports/EVIDENCE_INDEX_S0.md` | H1~H7 영상·근거 색인 | 최종 후보 평가 후 갱신 |
| `workspace/training/humanoid/exported/model_best.pt` | 현재 export 기준 checkpoint | 명시적 승급 결정 전 교체 금지 |
| `workspace/training/humanoid/exported/env.yaml` | 제출 환경 설정 | 채택 checkpoint와 일치 검증 후 교체 |
| `workspace/training/humanoid/exported/policy.pt` | 제출 정책 | checkpoint tensor 동일성 확인 후 교체 |
| `workspace/training/humanoid/humanoid_rewards.py` | 현재 보상 소스 | 사전등록된 단일 변경만 허용 |
| `workspace/training/humanoid/run06_server_package.zip` | 현재 서버 패키지 | SHA256 `1478e6a20d068dcbecd64ef648f1e3d1a7d5adf6e24dd6907d95b0430e8eaf86` |
| `workspace/training/humanoid/server_run06_videos.sh` | Run06 H1~H7 고정 영상 러너 | SHA256 `793ca0546d5cea3d0c63e96f61b850404e8d072e59eee6d4ac541c072e59df9f`, CRLF 0, Git Bash `bash -n` PASS; terrain seed 오류 제거·resume·3종 지형 preflight 지원 |
| `workspace/training/humanoid/run06_fixed_eval_package.zip` | Run06 H4·H6·H7 정량 평가 업로드 package | SHA256 `bf90f1943d36f5538da6aa861eab655a6fd28c2c244c4a544bc26282e05aac93`, 14 members, ZIP CRC PASS, Run06 model_9900 내장 |
| `workspace/training/humanoid/server_run06_fixed_eval.sh` | 학습 없는 32환경 고정 evaluator 러너 | CRLF 0, Git Bash `bash -n` PASS, H4 좌우·H6 ±10°·H7 push 원시 CSV 회수 |
| `workspace/training/quadruped/server_run_Go2_videos.sh` | **LEGACY_INVALID_MAPPING — 실행·G1~G7 판정 금지** | H1형 G1 stand/G2 forward/G3 lateral/G4 complex/G5 rough/G6 ±10°/G7 push로, 제공 Go2 registry와 불일치. 역사 보존만 하며 신규 evaluator가 대체해야 함 |
| `workspace/training/quadruped/quadruped_rewards.py` | Go2 실질 4변수 동시 변경 pilot 1,000 iter | `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05`; action -0.01은 불변. `MULTIVARIABLE_EXPLORATORY_BASELINE`, 개별 인과효과 미측정 |
| `workspace/training/quadruped/config/go2_self_eval_registry.json` | Go2 G1~G7 canonical 내부평가 registry | G1 forward·G2 omni·G3 rough·G4 ±20°·G5 10~15cm stairs·G6 push·G7 DR, weight sum 1.0 |
| `tools/verify_download_artifact.py` | 서버 다운로드 정형 검증기 | 외부/내부 SHA, 안전한 tar 경로, 시나리오 수, model SHA를 JSON으로 판정 |
| `.codex/agents/artifact-verifier.md` | 저비용 artifact 검증 역할 | `explore`/`gpt-5.6-luna` 전용, 의미 판정·병합·서버 종료 권한 없음 |
| `workspace/server_returns/train_260831-06_run05cfg_10000/` | Run06 검증 격리본 | bundle SHA·내부 18/18·snapshot tar 검증 완료, 아직 training 미병합 |

## 5. 서버 artifact lifecycle

```text
PLANNED → RUNNING → RECEIVED → VERIFIED → MERGED → ANALYZED → REPORTED → SUBMISSION_READY
               ↘ FAILED / INCONCLUSIVE / BLOCKED
```

| 상태 | 완료 기준 |
|---|---|
| `PLANNED` | 목적·변수·seed·iter·시간·중단점·회수물·다음 분기 기록 |
| `RUNNING` | 사용자 제공 서버 출력으로 실행 시작 확인. 실제 iter는 로그 전까지 미측정 |
| `RECEIVED` | 원본 tar가 `workspace/server_returns/<RUN_ID>/`에 있고 파일 SHA 기록 |
| `VERIFIED` | tar SHA, `TRAIN_RC`, source hash, params, seed, checkpoint, tfevents 확인 |
| `MERGED` | 병합 전/후 목록과 대상 경로 기록, 기존 정본 비파괴 확인 |
| `ANALYZED` | 사전 기준으로 `INTERNAL_GATE_PASS/FAIL/INCONCLUSIVE`와 H1~H7 측정 범위 판정 |
| `REPORTED` | reward 마스터·상태·일정·보고서가 같은 판정으로 동기화 |
| `SUBMISSION_READY` | 최종 `policy.pt`·`env.yaml`·리포트 일치와 H1~H7 증거 확인 |

## 6. 회수·병합 불변식

1. 서버 `training` 전체 다운로드는 허용하지만 **보험 snapshot**으로만 취급한다.
2. 로컬 `workspace/training`에 전체 압축을 직접 해제하거나 폴더를 통째로 덮어쓰지 않는다.
3. `/workspace/_keep/<RUN_ID>_DOWNLOAD.tar.gz`를 별도 다운로드하거나 snapshot 전 `training/_server_returns/<RUN_ID>/`로 복사한다.
4. 원본 tar는 `workspace/server_returns/<RUN_ID>/original/`에 보존하고, 분석용 해제본은 `extracted/`에 둔다.
5. 검증 전 `exported/model_best.pt`, `env.yaml`, `policy.pt`, 보고서, 원장을 교체하지 않는다.
6. 병합 전 `MERGE_PLAN.tsv`, 병합 후 `MERGE_RESULT.tsv`와 `LOCAL_SHA256SUMS.txt`를 남긴다.
7. 같은 이름의 파일은 자동 overwrite하지 않는다. 내용 비교 후 `add / replace / keep-local / conflict`를 명시한다.
8. 서버 snapshot에만 있고 필수 bundle에 없는 파일은 누락 원인을 확인한 뒤 별도 판정한다.

## 7. Run별 필수 회수 파일

| 분류 | 필수 파일/검사 |
|---|---|
| 실행 상태 | `STATUS.txt`, `TRAIN_RC`, `RUN_ID`, `MAX_ITERS`, 시작·종료 시각 |
| 무결성 | 다운로드 tar SHA256, 내부 `SHA256SUMS.txt`, source hash |
| 학습 설정 | `params/agent.yaml`, `params/env.yaml`, seed, num_envs, max_iterations |
| 곡선 | TensorBoard tfevents, `train.log` |
| 모델 | 3k/5k/10k milestone과 마지막 checkpoint |
| 소스 | `train.py`, `humanoid_rewards.py`, `h1_task/*.py`, restore 결과 |
| 제출 후보 | `model_best.pt`, `env.yaml`; `policy.pt`는 별도 export·tensor 검증 전 제출 후보 아님 |
| 분석 | Run05 대비 xy/yaw, episode length, base_contact, mean_std, H1~H7 직접/미측정 표 |

### 7-a. 학습 후 영상 필요성 판정·종료 게이트

학습 작업에는 학습 artifact와 행동 영상 artifact를 별도 상태로 둔다. 학습 bundle이
`VERIFIED`여도 영상이 필요한 run의 행동 평가는 `PENDING`이며 `ANALYZED`로 승급하지 않는다.

| 판정 | 적용 조건 | 종료 전 필수 조치 |
|---|---|---|
| `VIDEO_REQUIRED` | 새 reward/env/policy/checkpoint, 장기 학습, 후보 채택·폐기, H1~H7·survival·tracking 주장 | 고정 evaluator 영상 생성 → 로그·policy/checkpoint 식별자 포함 tar 생성 → tar와 `.sha256` 로컬 다운로드 확인 |
| `VIDEO_CONDITIONAL` | 학습 결과나 이상 징후에 따라 추가 시나리오가 달라짐 | 기본 CORE 영상을 확보하고 종료 직후 재판정; 추가 영상 필요 시 같은 세션에서 FULL로 확장 |
| `VIDEO_NOT_REQUIRED` | checkpoint 없는 smoke test 또는 동일 tensor·동일 evaluator 영상이 이미 검증됨 | 예외 근거와 대체 영상 경로·정책 식별자 기록 |
| `VIDEO_REQUIRED_NOT_ACQUIRED` | 필수 영상 생성/패키징/다운로드 실패 | 실패 로그와 재현 checkpoint·source·config 회수; 평가 완료 금지; 다음 세션 첫 작업으로 이관 |

**서버 종료 가능 조건:** 영상 판정이 기록되고, `VIDEO_REQUIRED`이면 영상 tar와 SHA가 로컬에
도착했으며 파일 존재·외부 SHA 일치까지 확인돼야 한다. 내부 파일 수·정책 대응 검증은
`RECEIVED → VERIFIED` 단계에서 수행한다. 영상이 없는 학습은 성능상 실패가 아니라
**행동 평가 미완료**다.

영상 사전등록에는 `RUN_ID / checkpoint iter+SHA / suite(CORE·FULL) / H1~H7 매핑 / seed /
num_envs / video_length / 명령 고정값 / 예상 파일 수 / 서버 경로 / 로컬 회수 경로 / 실패 시
부분 bundle 경로`를 모두 적는다.

## 8. Artifact 작업 원장 — append-only

| 작업 ID | 일시 | 등급 | RUN_ID/범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|---|
| `A260831-01` | 260831 | 조사 | 서버 회수 정책 | `REPORTED` | 없음 | 전체 snapshot 격리·선택 병합 규칙 확정 | 이 문서, `AGENTS.md`, `SERVER_SESSION_RUNBOOK.md`, 담당 지침 3종 | 완료 — 후속 작업은 이 규칙 유지 |
| `A260831-02` | 260831 | 개선 | `train_260831-06_run05cfg_10000` | `ANALYZED` | Run06 10k 자연 완료·두 tar 다운로드 | 종료·bundle·설정·곡선 검증 | `TRAIN_RC=0`, model_9900, `INTERNAL_GATE_PASS` 5/5 | Run06 동결 기준선 유지 |
| `A260831-03` | 260831 | 필수(제출요건) | Run06 필수 bundle 회수 | `VERIFIED` | 필수 bundle·전체 snapshot 다운로드 | `server_returns/<RUN_ID>/` 격리, tar·SHA·내부 18/18 검증 | `INGEST_STATUS.md`, `FILE_MANIFEST.tsv`, `LOCAL_SHA256SUMS.txt`, `MERGE_PLAN.tsv` | 원본 보존, 분석 전 병합 금지 |
| `A260831-04` | 260831 | 조사 | Run06 분석·선택 병합 | `ANALYZED` | 없음 | Run05 대비 Run06 마지막500 곡선·영상 분석 | xy·yaw·episode·base_contact·std 개선; 영상 증거 계층 정정 | 제출 후보 문서에 한계 반영 |
| `A260831-05` | 260831 | 필수(제출요건) | Run06 H1~H7 고정 영상 10종 | `VERIFIED` | resume 완료·FULL tar와 SHA 다운로드 | FULL 원본 격리·외부/내부 SHA·시나리오·model 대응 검증 | verifier PASS, 내부 47/47, video 10, policy 10, model SHA `8eb06e2…b636` | 서버 종료; A260831-04 영상·곡선 분석 시작 |
| `A260831-07` | 260831 | 개선 | 저비용 다운로드 검증 역할 | `VERIFIED` | 없음 | Luna용 read-only agent와 결정론적 검증 CLI 작성 | `artifact-verifier.md`, `verify_download_artifact.py`, Run06 FULL PASS JSON | 메인 팀장이 입력 계약·최종 의미 판정 유지 |
| `A260831-08` | 260831 | 필수(제출요건) | Run06 H4·H6·H7 고정 정량 평가 | `ANALYZED` | ZIP 업로드·한 줄 실행·FULL tar 다운로드 | 원본 telemetry 회수·로컬 보고서 재생성 | H4 yaw, H6 양방향, H7 회복 내부 측정 양호; threshold·공식 결과 없음 | 제출 후보의 보조 근거로만 사용 |
| `A260831-10` | 260831 | 개선 | 판정 지침·후속 학습 방향 | `REPORTED` | 없음 | 증거 4계층, TTL 우선 보고, 단일변수 screening·승급 규칙 확정 | `AGENTS.md`, 마스터 §9, 일정·상태·제출 리포트 동기화; candidate manifest 검증 | 공식 결과 대기 계획 철회; A260831-11로 자체 점수 확보 |
| `A260831-11` | 260831 | 필수(제출요건) | Run06 H1~H7 전체 자체 점수 | `PLANNED` | 다음 서버 접속에서 평가 전용 ZIP 업로드·한 줄 실행·FULL tar와 SHA 다운로드 | H1~H7 10 case 20초 telemetry, 내부 proxy v1 scorecard, package SHA `e897fa10…05551` | `run06_fixed_eval_package.zip`, `FIXED_EVAL_REPORT.json/md`; 학습 없음 | 회수 후 70점 게이트 판정, 최대 감점 시나리오만 screening |
| `A260831-09` | 260831 | 조사 | Go2 pilot·구형 영상 스위트 | `INCONCLUSIVE` | 실행 금지 | 제공 Go2 registry와 구형 runner 매핑 대조 | pilot artifact는 존재하나 구형 runner는 `LEGACY_INVALID_MAPPING`; G1~G7 미측정 | `G-A002` 신규 evaluator로 대체 |
| `G-A001` | 260901 | 조사 | Go2 운영체계·자체평가 재설계 | `REPORTED` | 없음 | 별도 원장·전용 역할 4종·canonical registry·protocol·handoff·validator 작성 | `GO2_*`, `.codex/agents/go2-*`, `validate_go2_campaign.py` | 새 세션에서 G-A002 evaluator 구현 |
| `G-A002` | 260901 | 필수(제출요건) | Pilot-01 정확한 G1~G7 평가 package | `PLANNED` | 통합 ZIP 업로드·한 줄 실행·단일 결과 ZIP 다운로드 | telemetry/report/lineage/worst-case video runner와 package builder/test 구현 완료 | package 로컬 검증 완료; 서버 결과는 `[미측정]` | `G-A005` package로 실행 |
| `G-A003` | 260901 | 조사 | Pilot-01 기반 초기 캠페인 계획 | `REPORTED` | 없음 | frozen artifact·control 유효성 감사, 평가→조건부 control→단일변수 ablation→승급 계획 작성 | `workspace/training/quadruped/upload/plan/go2-post-pilot-initial-work-plan.md`, G-F10·G-D08, 일정·reward 원장 동기화 | `G-A002` evaluator/package 구현 |
| `G-A004` | 260901 | 조사 | Default-01 1,000 iter + Pilot-01 쌍대 G1~G7 평가 | `PLANNED` | 통합 ZIP 업로드·한 줄 실행·단일 결과 ZIP 다운로드 | Default test PRD·상세계획·통합 runner 구현 완료 | Default 결과는 `[미측정]`; `VIDEO_REQUIRED`: 정책별 worst-case G1~G7 7개, seed 101/202/303 중 정량 최악 seed, 500 steps, 결과 ZIP `evaluation/<policy>/videos/` | `G-A005` 실행 → 정책별 69 telemetry·7 영상 회수 |
| `G-A005` | 260901 | 필수(제출요건) | Go2 Default-vs-Pilot 단일 실행·회수 package | `VERIFIED` | `/workspace/go2_default_vs_pilot_v1.zip` 업로드 후 검증된 한 줄 실행 | deterministic ZIP build, reward-only default staging, embedded Pilot SHA, manifest, runner syntax·contract test | `workspace/training/quadruped/go2_default_vs_pilot_v1.zip`, SHA `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356`; 28 members; ZIP CRC·manifest·CRLF·Git Bash `bash -n` 검증 | 서버 실행 후 `/workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip`과 SHA 회수 |

## 9. 파일 변경 원장 — append-only

| 일시 | 작업 ID | 파일 | 변경 내용 | 검증 |
|---|---|---|---|---|
| 260831 | `A260831-01` | `ARTIFACT_MANAGEMENT.md` | 중앙 파일 목록·artifact lifecycle·작업 원장 신설 | 필수 절·표·링크 검사 |
| 260831 | `A260831-01` | `AGENTS.md` | 서버 snapshot 비덮어쓰기와 중앙 문서 선조회 규칙 | 규칙 중복·마커 확인 |
| 260831 | `A260831-01` | `SERVER_SESSION_RUNBOOK.md` | Run06 완료 후 필수 bundle·보험 snapshot 회수 명령 | package SHA 일치·shell 명령 정적 검토 |
| 260831 | `A260831-01` | `PROJECT_STATE.md` | F48~F51, D39~D42, LATEST NEXT 기록 | append-only 확인 |
| 260831 | `A260831-01` | `workspace/training/humanoid/upload/plan/CAMPAIGN_PLAN.md`, `CAMPAIGN_SCHEDULE.md`, `REPORT_260831.md` | 현재 단계 2/6 및 Run06 자연 완료·격리 회수 동기화 | 첫 화면 8항목 검사 |
| 260831 | `A260831-01` | `.codex/agents/*.md` | 기획·일정·분석·보고 시 중앙 운영 문서와 작업 원장 참조 | 3개 담당 지침 검색 |
| 260831 | `A260831-03` | `workspace/server_returns/train_260831-06_run05cfg_10000/` | 원본 bundle·snapshot 격리, tar 해제본, manifest·merge plan·수신 기록 작성 | bundle SHA 일치, tar 2종 PASS, 내부 checksum 18/18 PASS |
| 260831 | `A260831-05` | `workspace/training/humanoid/server_run06_videos.sh` | H1~H7 10종 고정 명령 영상·로그·policy를 CORE/FULL tar로 회수하는 러너 신설 | 8,155 B, CRLF 0, Git Bash `bash -n` PASS |
| 260831 | `A260831-06` | `AGENTS.md`, `ARTIFACT_MANAGEMENT.md`, `SERVER_SESSION_RUNBOOK.md`, `.codex/agents/*.md` | 학습 전·후 영상 필요성 재판정과 영상 다운로드 전 서버 종료 금지 게이트 신설 | 중앙 규칙·역할별 체크리스트·종료 보고 필드 대조 |
| 260831 | `A260831-05` | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/`, `server_run06_videos.sh` | CORE/PARTIAL 원본 격리·검증 및 H5 terrain seed 타입 오류 제거·resume 기능 추가 | 외부 SHA 2종 PASS, tar 2종 PASS, 내부 36/36 PASS, model SHA 일치, Git Bash `bash -n` PASS |
| 260831 | `A260831-05` | `workspace/server_returns/train_260831-06_run05cfg_10000/videos/` | FULL tar·SHA 격리, 해제본·검증 JSON 보존 | tar SHA `c80f972c…9be`, 내부 47/47 PASS, video/policy 10/10, model SHA 일치 |
| 260831 | `A260831-07` | `.codex/agents/artifact-verifier.md`, `tools/verify_download_artifact.py` | 저비용 정형 다운로드 검증 역할·JSON 검증기 신설 | Run06 FULL 입력에서 rc=0, status PASS |
| 260831 | `A260831-08` | `eval_telemetry.py`, `fixed_eval_report.py`, `server_run06_fixed_eval.sh`, `run06_fixed_eval_package.zip`, `tools/test_fixed_eval_contract.py` | 기존 play 경로에 opt-in step telemetry를 추가하고 Run06 model_9900 고정 평가 package 생성 | unittest 5/5, Python compile, Git Bash `bash -n`, ZIP CRC·14 members·내장 model SHA PASS |
| 260831 | `A260831-09` | `SERVER_SESSION_RUNBOOK.md` | Go2 G1~G7 영상 스위트 절차 추가 — H1 `server_run06_videos.sh` 벤치마킹 문단 신설 | H1 10종 구조·CORE/FULL·fingerprint·검증 동일 명시, Go2 10종 매핑·명령 인자 대조 |
| 260831 | `A260831-09` | `workspace/training/quadruped/server_run_Go2_videos.sh` | H1 `server_run06_videos.sh`(8,155B) 벤치마킹해 Quadruped-v0 10종 포팅 — G1·G2·G3×2·G4×2·G5·G6×2·G7, seed 42·4 env·1000 step | CRLF 0, model SHA `C4D78ADF…`, Quadruped-v0 task 전환·G시나리오 매핑 확인 |
| 260831 | `A260831-09` | `workspace/training/quadruped/quadruped_rewards.py` | 이미지 5변수 반영 — `track 1.2`·`feet 0.2`·`lin -2`·`ang -0.05` (실질 4개 변경) | `grep` 4/4 일치, `report.html` 4/4 주황 점, Python AST PASS |
| 260831 | `A260831-10` | `AGENTS.md`, `.codex/agents/prelim-campaign-manager.md`, `.codex/agents/humanoid-test-planner.md`, `.codex/agents/humanoid-report-writer.md` | artifact·영상·내부 gate·공식 결과 분리, 서버 TTL 우선 답변, 학습 승인 규칙 추가 | 필수 제목·용어 검색, `git diff --check` |
| 260831 | `A260831-10` | `H1_REWARD_EVIDENCE_MASTER.md`, `CAMPAIGN_SCHEDULE.md`, `PROJECT_STATE.md`, `experiment_history.csv` | Run06 단계 5/6 동기화, 공식 산식과 내부 proxy 경계 정정, 후속 screening 순서 확정 | H1~H7 증거 행렬·F69~F70/D56~D58·현재 단계 대조 |
| 260831 | `A260831-10` | `workspace/submission_candidates/h1_run06_model9900/`, `workspace/training/humanoid/exported/TECHNICAL_REPORT.md`, `workspace/training/humanoid/reports/TECH_REPORT_H1_RUN06_FINAL.md` | 제출 리포트 판정 용어·공식 산식 출처 정정 및 3개 사본 동기화 | report SHA 동일, candidate `SHA256SUMS.txt` 5/5 일치; policy/env/model hash 불변 |
| 260831 | `A260831-11` | `fixed_eval_report.py`, `server_run06_fixed_eval.sh`, `RUN06_FIXED_EVAL_README.txt`, `tools/test_fixed_eval_contract.py` | H4·H6·H7 부분 평가를 H1~H7 10 case 전체 20초 평가로 확장하고 내부 시뮬 proxy /70 게이트 추가 | unittest 8/8, compile, Git Bash `bash -n`, ZIP 14 members·SHA `e897fa10…05551` |
| 260831 | `A260831-11` | `AGENTS.md`, 담당 agent 3종, 마스터·일정·상태 원장 | 부분 PASS 점수 제외, 공식 결과 대기 철회, 총 자체예상 70/100 최소·75/100 목표 규칙 | `SELF_ASSESSMENT_INCOMPLETE`, threshold, NEXT 문구 대조 |
| 260831 | `A260831-11` | `SELF_ASSESSMENT_RUBRIC.md`, 제출 후보 리포트 3개 사본·manifest | 문서 자체감사 27/30 고정, 부분 평가를 성능 승급에서 제외 | report 3개 SHA 동기화, candidate manifest 6/6 PASS |
| 260901 | `G-A003` | `workspace/training/quadruped/upload/plan/go2-post-pilot-initial-work-plan.md`, `GO2_PROJECT_STATE.md`, `GO2_CAMPAIGN_SCHEDULE.md`, `GO2_REWARD_EVIDENCE_MASTER.md`, `ARTIFACT_MANAGEMENT.md` | 1차 튜닝 이후 평가 우선 초기계획, 유효 control 부재, 최소 경로·예산·재평가점 기록 | `validate_go2_campaign.py` PASS, `git diff --check` PASS |
| 260901 | `G-A004` | `GO2_DEFAULT_BASELINE_TEST_PRD.md`, `workspace/training/quadruped/upload/plan/go2-default-baseline-experiment-plan.md`, Go2 상태·일정·reward·handoff, `ARTIFACT_MANAGEMENT.md` | 조건부 control 계획을 Default-01 필수 생성·Pilot 쌍대평가·기본값 one-at-a-time 계보로 정정 | `validate_go2_campaign.py`, 문서 계약 검사, `git diff --check` |
| 260901 | `G-A004` | Default test PRD·상세계획, Go2 역할 지침 5종, 상태·일정 | PRD를 매 기획 턴 참조·동일 턴 갱신하는 living contract로 승격하고 `PRD_CHANGE`·`LEDGER_SYNC` 게이트 추가 | `validate_go2_campaign.py`, PRD lifecycle 계약 검사, `git diff --check` |
| 260901 | `G-A005` | Go2 evaluator·lineage·통합 runner·builder·tests·README, `play.py`, `train.py`, `go2_task/env_cfg.py` | Default 1k와 Default/Pilot 69-case·worst-video 평가를 단일 업로드/명령/결과 ZIP 구조로 구현 | Python compile·5 unit tests, Git Bash `bash -n`, CRLF 0, ZIP CRC·safe paths·27-file internal manifest, Pilot SHA, reward-only 4-line diff |
| 260901 | `G-A005` | Go2 PRD·상태·일정·상세계획·AGENTS·handoff·planner brief | G-D13 사용자 실행 package 자동 제공 계약과 실제 경로·SHA·완료표식·회수 게이트 동기화 | `validate_go2_campaign.py`, `git diff --check` |

## 10. 새 작업 기록 템플릿

```markdown
| `A<YYMMDD>-<NN>` | <일시> | 필수(제출요건)/개선/조사 | <RUN_ID/범위> | `PLANNED` | <사용자 실행> | <로컬 작업> | <사전 증거> | <첫 NEXT> |
```

작업 완료 시 새 행을 만들지 않고 같은 작업 ID의 상태와 증거를 전진시킨다. 범위가 달라지거나
새 서버 비용이 생기는 경우에만 새 작업 ID를 만든다. 외부 시스템의 사용자 행동은 로그·파일로
확인되기 전 `[미측정]`으로 두며, 우리가 지시한 사실과 사용자가 실제 수행한 사실을 구분한다.

### A260831-11 상태 전이 — 260901

- 상태: `PLANNED → RECEIVED → VERIFIED → ANALYZED`
- 원본: `workspace/_keep/train_260831-06_run05cfg_10000_FIXED_EVAL_FULL.tar.gz`
- 외부 SHA-256: `4e552b2caea4f9a33475bf7a93bc35a383c9aa9b79a42e308b002c01674b860f`
- 검증: 안전 경로 0, 내부 69/69, case 10/10, `RUNNER_RC=0`, model SHA 일치
- 분석: 66.0414/70, `CALIBRATION_PASS / GENERALIZATION_UNVERIFIED`

### A260901-01 — 독립 multi-seed 검증

| 항목 | 값 |
|---|---|
| 등급 | 필수(제출요건) |
| 상태 | `SUBMISSION_READY` |
| 정책 | Run06 model_9900, SHA `8eb06e2…b636` 동결 |
| seeds | 101, 202, 303 사전등록 |
| 범위 | seed별 H1~H7 10 case, 32 env, 1,000 step |
| 판정 | 시나리오별 최악 seed, 세 seed 모두 통과 |
| 영상 | `VIDEO_NOT_REQUIRED` — 동일 checkpoint 영상 10종 VERIFIED, 이번 작업은 seed telemetry |
| 패키지 | `workspace/training/humanoid/run06_independent_eval_package.zip` |
| package SHA-256 | `ed235d67f2f2f4decb2fec71cc1d2664a45f2304b928dff5d20d9be343f584d2` |
| 예상 서버 시간 | 15~25분, 학습 없음 |
| 필수 회수 | `..._INDEPENDENT_EVAL_FULL.tar.gz`와 `.sha256` |
| 결과 | 외부 SHA 일치, 내부 189/189, 30/30 case, 실패 seed·시나리오 0, 65.73/70 |
| 후보 | `workspace/submission_candidates/h1_run06_model9900/UPLOAD_READY/` 3종, manifest 3/3 |
| NEXT | 팀 대시보드 업로드·접수 증거 회수 |

## 11. Go2 partial 수신 및 복구 — `G-A006` (260901)

| 작업 ID | 등급 | 범위 | 상태 | 확보 | 미확보 / NEXT |
|---|---|---|---|---|---|
| `G-A006` | 필수(제출요건) | Default-vs-Pilot 결과 회수·복구 | `RECEIVED` | Default 학습 artifact, Default telemetry 69/69, 부분 결과 461파일 | Pilot telemetry 0/69, 영상 0/14, 비교 보고서, FULL ZIP 및 유효 SHA. 서버 종료 불가; hotfix resume 후 재회수 |

- 서버 원본: `/workspace/_keep/go2_default_vs_pilot_v1/`
- 최초 로컬 inbox: `workspace/_keep/go2_default_vs_pilot_v1/`
- 격리 원본: `workspace/server_returns/go2_default_vs_pilot_v1_partial_260901/original/go2_default_vs_pilot_v1/`
- 부분 결과: `RESULT_STATE=PARTIAL`, `RUNNER_RC=1`, 519,957,865 bytes
- 로컬 directory manifest SHA-256: `2b7867626065552ee1fe1a73a07a79a8ac577cb3ef0a03e481b6b0607e00b8a4`
- 수신한 `GO2_DEFAULT_VS_PILOT_RESULT.zip.sha256`는 0 byte라 무결성 증거로 사용할 수 없다.
- 원인: Default 평가 후 Pilot의 `exported/`를 삭제한 뒤 같은 경로에서 checkpoint를 복사했고, 실패 packaging이 서버에 없는 bare `python3`를 호출했다.
- 현재 서버용 hotfix: `workspace/training/quadruped/go2_default_vs_pilot_v1_hotfix.zip`, SHA-256 `b2fa2d57aee9ab55ea9765171d8230c8aeac8c38bbe46285548c864b4eee2d39`.
- 새 서버용 수정 통합 package: `workspace/training/quadruped/go2_default_vs_pilot_v1.zip`, SHA-256 `db239f77fe3336209ecb8d4f38478c1fc1dd605fbf5c0351e95a9ba1b7e74cfd`.
- 폐기된 최초 package는 격리 원본에 `go2_default_vs_pilot_v1_buggy.zip`으로 보존했다. SHA-256 `a95e09c474e5d2d5d7ed0563ebace26d761360f8fd84e0f6e4ebf493c2422356`이며 다시 실행하지 않는다.
- 다운로드 매핑 정본: `workspace/server_returns/DOWNLOAD_MAP.tsv`.
- 병합: `NOT_PERFORMED`; FULL 결과 검증 전 `workspace/training/quadruped`에 run 결과를 병합하지 않는다.

### G-A006 FULL 회수 검증 — 260901

- 상태: `RECEIVED → VERIFIED`
- 회수물: `workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip` 및 `.sha256`
- 격리 원본: `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/original/`
- 외부 SHA-256: `af41ccc5ab99b8d586d2a2567c753863bc16ac05fe90b4d08ad6d63a05f2b25b` 일치
- package: 925 entries, unsafe path 0, `RESULT_STATE=FULL`, `RUNNER_RC=0`
- 필수 telemetry: Default 69/69, Pilot 69/69
- 필수 영상: Default 7/7, Pilot 7/7, 14개 모두 non-empty; 관찰 판정은 `VIDEO_UNKNOWN`
- 내부 manifest: launcher.log 1건만 packaging 종료행 후첨으로 불일치, 나머지 923건 일치·누락 0
- 판정: `ARTIFACT_VERIFIED`; 서버 종료 가능. 병합은 `NOT_PERFORMED`, 다음 상태는 `ANALYZED`.
- 상세: `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/VERIFICATION_STATUS.md`

### G-A006 선택 병합·분석·보고 — 260901

- 상태: `VERIFIED → MERGED → ANALYZED → REPORTED`
- 선택 병합: paired/self-eval JSON·MD 4개와 14개 영상 contact sheet만 `workspace/training/quadruped/reports/evidence/go2_default_vs_pilot_260901/`에 추가했다.
- 원본 MP4·FULL ZIP은 `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/`에서 보존하며 로컬 training 정본에 통째로 덮어쓰지 않았다.
- 병합 증거: `MERGE_PLAN.tsv`, `MERGE_RESULT.tsv`, `LOCAL_SHA256SUMS.txt`; 18개 대상 모두 `OK`.
- 영상 판정: 각 MP4의 3%~97% 구간 12프레임 직접 관찰, `VIDEO_OBSERVED`; 연속 gait timing·foot contact는 미측정.
- 분석: Default `17.90699/70`, Pilot `41.97990/70`, delta `+24.07291/70`; 둘 다 `INTERNAL_GATE_FAIL`; 분기 `SHARED_WEAKNESS_FOUND`.
- 보고서: `workspace/training/quadruped/reports/GO2_DEFAULT_VS_PILOT_ANALYSIS_260901.md`.
- NEXT: Default 계보 `feet_air_time .01→.2` 단일변수 1,000-iter screening을 별도 작업 ID로 사전등록한다.

## 12. Go2 단일변수 screening package — `G-A007` (260901)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A007` | 개선 | Default 계보 `feet_air_time 0.01→0.20` only, 1,000 iter | package `VERIFIED` / result `RECEIVED(PARTIAL)` | 학습 완료, evaluator 8건 뒤 Isaac Sim crash; 재개 실행 표식은 아직 `[미측정]` | PARTIAL ZIP·SHA 격리, CRC·safe path·training artifact·8 telemetry 확인 | result SHA `3853b4fcf38f78938a348a0f8d915512aaa8750277fdc1d9cea8366e16a2b8ef`, candidate model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5` | 동일 서버에서 `GO2_RESUME=1`; FULL ZIP·SHA 재회수 전 서버 종료 불가 |

### 사전등록된 artifact·영상 계약

- RUN_ID: `train_260901-Go2_feet_air_time_020_1000`
- 기준: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `feet_air_time 0.01→0.20`; 나머지 네 reward·seed 42·4096 env·1,000 iter 고정.
- `VIDEO_REQUIRED`: candidate G1~G7 정량 worst-case 각 1개, 총 7개, 평가 seed 101/202/303 중 worst seed, 4 env, 500 steps, 약 10초.
- Default 영상은 `VIDEO_NOT_REQUIRED`: 동일 Default-01 tensor·동일 registry/evaluator의 7영상이 G-A006에서 `ARTIFACT_VERIFIED`·`VIDEO_OBSERVED`; `workspace/server_returns/go2_default_vs_pilot_v1_full_260901/extracted/videos/default/`을 재사용한다.
- telemetry: candidate 69건, G1~G7 survival·tracking·G5 completion·G6 recovery·G7 실현값.
- 필수 정책 증거: `model_best.pt`, `env.yaml`, `policy.pt`, `POLICY_LINEAGE.json`, source·diff·log·checkpoint·tfevents·params.
- 실패 회수: `/workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip`이 `PARTIAL`로 만들어져 가능한 checkpoint·source·config·launcher log를 보존한다.
- 정상 회수: 같은 결과 ZIP이 `FULL`, `RUNNER_RC=0`, telemetry 69, video 7을 포함해야 한다.
- 로컬 다운로드 위치: `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` 및 `.sha256`.
- 서버 종료 게이트: 위 두 파일 로컬 도착·외부 SHA 일치·ZIP CRC·내부 manifest·69 telemetry·7영상·lineage 확인 전 종료 불가.

### 로컬 검증 증거

- 사전등록 PRD: `workspace/training/quadruped/upload/plan/GO2_FEET_AIR_TIME_020_SCREENING_PRD.md`.
- package: `workspace/training/quadruped/go2_feet_air_time_020_v1.zip`.
- package SHA companion: `workspace/training/quadruped/go2_feet_air_time_020_v1.zip.sha256`.
- 상세 검증: `workspace/training/quadruped/go2_feet_air_time_020_v1.VERIFICATION.md`.
- 검증: deterministic rebuild SHA 일치, ZIP CRC·safe path, 내부 manifest 94/94, 단일 reward diff, frozen baseline 69/69·identity, Python compile, contract 5/5, CRLF 0, Git Bash `bash -n`.
- 예상 실행 창: 이전 artifact 실측을 기준으로 1시간 35분~2시간. 전체 서버 과금 시간은 보장하지 않는다.

### PARTIAL 결과 회수 — 260901

- 로컬 원본 보존: `workspace/server_returns/go2_feet_air_time_020_v1_partial_260901/original/`.
- 외부 SHA: `3853b4fcf38f78938a348a0f8d915512aaa8750277fdc1d9cea8366e16a2b8ef`, companion과 일치.
- ZIP: 96 members, CRC 정상, unsafe path 0, `RESULT_STATE=PARTIAL`, `RUNNER_RC=5`.
- 학습: `TRAIN_RC=0`, seed 42, 4096 env, 1,000 iter; candidate model SHA `0dc8815f54498642c8548093d31fde869a293de91401931876427101d2f393e5`.
- 평가: telemetry 8/69, candidate video 0/7, `POLICY_LINEAGE.json` 미생성. 따라서 `ARTIFACT_VERIFIED` 미달, `VIDEO_UNKNOWN`, `INTERNAL_GATE_INCONCLUSIVE`, `OFFICIAL_RESULT_UNMEASURED`.
- 실패점: `G2/combined_yaw_left`, eval seed 101 시작 시 Isaac Sim startup segmentation fault; 이미 완료된 8건은 fingerprint로 재사용 가능하다.
- 내부 manifest: 95건 중 94건 일치, `launcher.log` 1건은 manifest 생성 뒤 tee가 계속 기록하는 기존 packaging 순서 문제로 불일치. 외부 ZIP SHA와 CRC는 일치하지만 FULL 결과에서 다시 감사한다.
- 고정 검사 도구 `tools/verify_download_artifact.py`는 tar/gzip 전용이라 ZIP 입력을 `ESCALATE`했다. 메인 루프가 ZIP CRC·safe path·manifest·count를 직접 검증했다.
- 재개 명령: `cd /workspace/go2_feet_air_time_020_v1 && GO2_RESUME=1 bash server_run_go2_feet_air_time_020_v1.sh`.
- 서버 종료 게이트: FULL 결과 ZIP·SHA를 다시 내려받아 telemetry 69·video 7·lineage·policy와 무결성을 로컬 검증하기 전까지 **종료 불가**.

### 파일 변경 원장 추가

| 일시 | 작업 ID | 파일 | 변경 내용 | 검증 |
|---|---|---|---|---|
| 260901 | `G-A007` | screening PRD·runner·reporter·builder·tests·README·ZIP | Default report 재사용 + candidate 1회 학습/69-case/7영상/단일 결과 ZIP 구현 | deterministic SHA, ZIP CRC·manifest, compile, tests 5/5, `bash -n`, CRLF 0 |
| 260901 | `G-A007` | Go2 PRD·상태·일정·reward master·planner brief·AGENTS | 단계 3 현재 위치, 사전 gate, package 경로·실행·회수·종료 조건 동기화 | `validate_go2_campaign.py`, `git diff --check` |

## 13. Go2 evaluator graceful-shutdown hotfix ? `G-A008` (260901)
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 확인한 정상 기록: `workspace/training/quadruped/go2_feet_air_time_020_v2.VERIFICATION.md`(v2 원인·수정·패키지 SHA·검증, 정상 영문), `GO2_OPUS_REAUDIT_INDEPENDENT_260907.md:296`(G-A008 요약 1행). 이 절의 표·파일 변경 원장 문구는 대체 기록 미확보.

| ?? ID | ?? | ?? | ?? | ??? ?? | ?? ?? | ?????? | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A008` | ??(????) | G-A007 candidate ??? ?? evaluator ?????? ?? ?? | `VERIFIED` | v1 ?? ?? `[???]`; v2 ?? ?? ?? ?? | PARTIAL ?? ??, graceful stop, bounded retry, stable manifest, deterministic package | `go2_feet_air_time_020_v2.zip`, SHA `73c6ba1f9cc29b22889d146e4c949ff54b7a9e2b4638199f61c9961dc9f88dbc`, tests 6/6 | ?? v1 ??? ?? ?? ??; v2? completed case?checkpoint ??? ?? |

### ????? ??

- `BUGGY_DO_NOT_REUSE`: v1 telemetry? hard process exit ??? retry ?? runner.
- ?? ??: v1? 8 case ?? ? ?? Isaac startup? `XOpenDisplay` ?? segmentation fault? ?? ??? ????.
- ?? ?? ??? ??: ?? horizon?? `env.step()` ???? ????? ?? ??? upstream `env.close()`?`simulation_app.close()`? ????.
- v2: hard-exit AST call 0, `simulation_app.is_running()` false? ?? loop exit, case/video ?? 3? bounded retry, ?? case fingerprint ???.
- manifest ??: active `launcher.log`? ???? immutable `launcher.snapshot.log`? package??.
- ??: deterministic SHA, ZIP CRC, safe path, manifest 94/94, Python compile, contract 6/6, Git Bash `bash -n`.
- ??: NVIDIA Kit ?? segmentation fault ??? ???? ???? ???. v2? ?? cleanup? ???? transient startup failure? ?? ??? ?? ???? ??? ??.

### ?? ?? ??

| ?? | ?? ID | ?? | ?? ?? | ?? |
|---|---|---|---|---|
| 260901 | `G-A008` | `go2_eval_telemetry.py`, runner, result packager | hard exit ??, graceful close, bounded retry, live-log manifest race ?? | compile, contract 6/6, AST hard-exit 0, `bash -n` |
| 260901 | `G-A008` | builder, v2 README, v2 ZIP, verification | ??? ?? ?? ?? resume hotfix package | SHA `73c6ba1f?8dbc`, deterministic rebuild, CRC, manifest 94/94 |

## 14. Go2 feet_air_time 0.20 FULL 재수신 — `G-A007` (260901)

- 등급: `개선`
- lifecycle: `RECEIVED`
- 로컬 inbox: `workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip` 및 `.sha256`
- 수신 시각: 2026-09-01 20:53 KST
- 파일 크기: 207,738,612 bytes
- 외부 ZIP SHA-256: `ec45628bae08092f7d671ea5c4cc409d9a247bde80e5bd4214d13b191239effc` (companion 일치)
- 1차 비파괴 검사: ZIP CRC 정상, unsafe path 0, `RESULT_STATE=FULL`, 69개 case `EVAL_RC=0`, 영상 7개, `policy.pt`·`POLICY_LINEAGE.json`·`model_best.pt`·`env.yaml` 존재.
- 격리 예정 경로: `workspace/server_returns/go2_feet_air_time_020_v1_full_260901/`
- NEXT: 격리 추출 → 내부 manifest/정책 lineage/69 telemetry/7 영상 검증 → 선택 병합·분석·원장 갱신.

## 15. Go2 track-linear 단일변수 screening — `G-A009` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A009` | 개선 | Default 계보 `track_lin_vel_xy_exp 1.0→1.2` only, 1,000 iter + 저비용 단계평가 | `REPORTED` | ZIP 업로드·한 줄 실행·결과 ZIP 2종 다운로드 완료 | 격리·무결성·정량 비교·G1 영상 판독·원장 갱신 완료 | result SHA `d9d84f68…61c3`, manifest 125/125, candidate/baseline 7/7, G1 `VIDEO_OBSERVED`, 분석 보고서 | G-A010 engine+JSON 로컬 준비 |

### 사전등록 artifact·영상 계약

- RUN_ID: `train_260902-Go2_track_lin_vel_120_1000`.
- 기준: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `track_lin_vel_xy_exp 1.0→1.2`; 나머지 reward·seed 42·4096 env·1,000 iter 고정.
- `VIDEO_REQUIRED`: candidate G1 forward-fast seed 101, 4 env, 500 step, 1개.
- telemetry: 조기중단 candidate 7 + baseline 7; 조기통과 때 candidate 21 + baseline 7.
- 결과 ZIP: `/workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 실패도 `PARTIAL` ZIP으로 checkpoint·source·config·log·완료 case를 자동 보존한다.
- 로컬 다운로드 위치: `workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 서버 종료 게이트: 두 파일 로컬 도착·외부 SHA·ZIP CRC·manifest·예상 case 수·영상 1·policy lineage를 검증하기 전 종료 판정 금지.

### package 검증

- 경로: `workspace/training/quadruped/go2_track_lin_vel_120_v1.zip`.
- SHA-256: `8d341d5dbae5aac6c6a4376442f2cdf20264fa2439d3b22c68e64811a81aefa7`.
- 6,467,257 bytes, 46 members, CRC OK, unsafe path 0, manifest 45/45.
- deterministic rebuild SHA 동일, Python compile, contract 9/9, Git Bash `bash -n`, CRLF 0.
- evaluator: G5 per-env body-velocity integral v2, G7 `NCRC_EVAL_DR=1`, 공식 등가성 주장 없음.

### result 회수·종료 게이트 검증

- 수신 파일: `workspace/_keep/GO2_TRACK_LIN_VEL_120_RESULT.zip` 및 `.sha256`.
- 격리 원본: `workspace/server_returns/train_260902-Go2_track_lin_vel_120_1000_g_a009/original/`.
- 외부 ZIP SHA-256: `d9d84f68c19eac9c84ec932154c7edf9d40743b8a05e92468ff0348bbc7661c3`; companion 일치.
- package: 126 members, CRC 정상, unsafe path 0, 내부 manifest 125/125 일치, `RESULT_STATE=FULL`, `RUNNER_RC=0`, `TRAIN_RC=0`.
- 학습물: model SHA `143871e3f69514a47ea4929c312895cf2da2e95b311aef83209866b3c3e542d4`, `model_900.pt`, `env.yaml`, tfevents, params, source, reward diff 확인.
- 평가물: candidate/baseline telemetry 7/7, candidate G1 영상 1/1(1,932,776 bytes), `POLICY_LINEAGE=ACTOR_TENSORS_MATCH` 8/8.
- 증거 계층: `ARTIFACT_VERIFIED`, G1 `VIDEO_OBSERVED`, runner decision `INTERNAL_EARLY_KILL_FAIL`, `OFFICIAL_RESULT_UNMEASURED`.
- 종료 판정: 필수 회수물 누락 0; 서버 종료 가능. 상세 검증은 격리 경로의 `VERIFICATION.json`, `INGEST_STATUS.md`, `LOCAL_SHA256SUMS.txt`에 보존.

### result 분석·영상 증거 보존

- 분석 보고서: `workspace/training/quadruped/reports/GO2_TRACK_LIN_VEL_120_RESULT_ANALYSIS_260902.md`.
- 찾기 쉬운 영상: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/videos/G1_forward_fast_seed_101.mp4`.
- contact sheet: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/contact_sheets/G1_forward_fast_seed_101_contact_sheet.jpg`.
- 영상 원본↔복사본 SHA-256: `9d81170136efebbcfb1e708a36b438900365a1da47a32d1cc25a83ba303c6cdb`, 일치.
- 정량 CSV: `workspace/training/quadruped/reports/evidence/go2_track_lin_vel_120_260902/G_A009_COMPARISON.csv`.
- 기계판독 요약·해시: 같은 폴더의 `ANALYSIS_SUMMARY.json`, `SHA256SUMS.txt`.
- 최종 계층: `ARTIFACT_VERIFIED`; G1 `VIDEO_OBSERVED`; G-A009 `INTERNAL_EARLY_KILL_FAIL`; `OFFICIAL_RESULT_UNMEASURED`.

## 16. Go2 `lin_vel_z_l2` 단일변수 screening — `G-A010` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A010` | 개선 | Default 계보 `lin_vel_z_l2 -3.0→-2.0` only, 1,000 iter + tier-1 조기평가 | `PLANNED` | `upload/G-A010/current`의 engine ZIP·JSON 업로드 후 한 줄 실행 | 고정 engine v1.1·JSON·PRD·run guide·contract 검증 완료 | engine SHA `e8f8b3cd…b7cd`, spec SHA `e59dcb93…f8c9`, 34 members, manifest 33/33, tests 8/8, `bash -n` | 서버 실행 → 결과 ZIP 2종 회수 |

- 기준 policy: Default-01 iter 800, model SHA `99ceeaa1a3a1ebee972841a771072b711744a1c8dec6e94b318b55f146dc4676`.
- 단일 변경: `lin_vel_z_l2 -3.0→-2.0`.
- 고정 reward: `track_lin_vel_xy_exp=1.0`, `feet_air_time=0.01`, `ang_vel_xy_l2=-0.08`, `action_rate_l2=-0.01`.
- 고정 학습: from-scratch, seed 42, 4096 env, 1,000 iter.
- `VIDEO_REQUIRED`: candidate G1 `forward_fast`, seed 101, 4 env, 500 step, 1개. 학습 종료 뒤 이상 징후가 있으면 추가 시나리오를 재판정한다.
- 조기평가: candidate G1~G7 대표 7-case, repaired-v2 baseline과 paired 비교. G1 proxy `+0.05` 미만 또는 어느 G survival `-0.10` 초과 하락이면 즉시 종료·회수한다.
- 대표평가·69-case·장기학습은 tier-1 조기통과 전 금지한다.
- 현재 upload engine ZIP: `workspace/training/quadruped/upload/G-A010/current/go2_tuning_engine_v1_1.zip`, SHA-256 `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- 현재 upload JSON: `workspace/training/quadruped/upload/G-A010/current/G_A010_lin_vel_z_m2.json`, SHA-256 `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- 검증: deterministic rebuild, ZIP CRC, unsafe path 0, manifest 33/33, extracted-engine materialization, contract 8/8, Python compile, CRLF 0, Git Bash `bash -n`.
- 서버 한 줄 명령: `cd /workspace && unzip -oq go2_tuning_engine_v1_1.zip && cd /workspace/go2_tuning_engine_v1_1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.
- 완료 표식: `[DONE] GO2_LIN_VEL_Z_M2_RESULT_READY`.
- 결과 ZIP: `/workspace/_keep/GO2_LIN_VEL_Z_M2_RESULT.zip` 및 `.sha256`; 성공·실패 모두 가능한 artifact를 단일 ZIP으로 자동 묶는다.
- 실행 지침: `workspace/training/quadruped/upload/G-A010/current/GO2_G_A010_RUN_GUIDE.txt`; package 상세: 같은 폴더의 `go2_tuning_engine_v1_1.VERIFICATION.md`.
- 현재 계층: upload package만 `ARTIFACT_VERIFIED`; 외부 실행·checkpoint·telemetry·영상은 `[미측정]`, `OFFICIAL_RESULT_UNMEASURED`.

## 17. G-A010 server-preflight Python launcher hotfix — `G-A012` (260902)

- 최초 engine v1.0은 bare `python3`를 호출해 서버에서 `command not found`로 종료됐다. tmux·학습은 시작되지 않아 iteration 소비는 0이다.
- v1.0 SHA `4489bef4…8a5a`는 `BUGGY_DO_NOT_REUSE`다.
- hotfix engine: `workspace/training/quadruped/upload/G-A010/current/go2_tuning_engine_v1_1.zip`, SHA `e8f8b3cde9d5a4f8b2de3663dd7036f19b1c28c97bf6aa01a5a779660f72b7cd`.
- 같은 폴더의 spec: `workspace/training/quadruped/upload/G-A010/current/G_A010_lin_vel_z_m2.json`, SHA `e59dcb93498740a50b7ea5cf21fa89592c187acadcebd000a92955df7c22f8c9`.
- 수정: validate·shell-env·materialize를 모두 `/workspace/IsaacLab/isaaclab.sh -p`로 실행하고 bare `python3` 의존을 제거했다.
- 검증: ZIP 34 members, CRC, unsafe 0, manifest 33/33, contract 8/8, extracted materialization, compile, CRLF 0, `bash -n`.
- 새 명령: `cd /workspace && unzip -oq go2_tuning_engine_v1_1.zip && cd /workspace/go2_tuning_engine_v1_1 && bash server_run_go2_tuning_engine_v1.sh /workspace/G_A010_lin_vel_z_m2.json`.

## 18. Go2 업로드 staging·이력 체계 — `G-A013` (260902)

| 작업 ID | 등급 | 범위 | 상태 | 사용자 실행 | 로컬 작업 | 증거·산출물 | NEXT |
|---|---|---|---|---|---|---|---|
| `G-A013` | 필수(운영) | Go2 서버 입력의 단일 업로드 진입점과 버전 이력 | `REPORTED` | `upload/<ID>/current`에서 지시된 두 파일만 선택 | current/history 분리·SHA copy 검증·append-only ledger 자동화 | `upload/README.md`, `G-A010/UPLOAD_HISTORY.tsv`, `tools/publish_go2_upload_bundle.py` | 이후 모든 Go2 실행 package를 동일 체계로 publish |

- 사용자 업로드 진입점은 `workspace/training/quadruped/upload/<EXPERIMENT_ID>/current/`로 고정한다.
- `history/<RELEASE_ID>/`는 release snapshot이며 과거 파일을 현재 사용본으로 승격하지 않는다.
- `UPLOAD_HISTORY.tsv`는 v1.0 `WITHDRAWN_BUGGY_DO_NOT_REUSE`와 v1.1 `ACTIVE_ARTIFACT_VERIFIED`를 분리 기록한다.
- publisher는 원본과 current/history 복사본 SHA를 비교하고, 같은 release identity는 ledger에 중복 추가하지 않는다.


## G-A027-RESULT-AUDIT-20260909 — 독립 결과 감사 착수
- 대상 실행: G-A027 (기존 A017/Pilot 재평가). 등급: 조사.
- 상태: PLANNED. 회수 여부부터 확인하며 외부 실행/수신을 추정하지 않는다.
- 범위: 승인 입력 고정, 로컬 회수물 탐색, 실제 입력이 있을 때만 검증·비교. 기존 파일 병합·삭제 없음.
- 예정 증거: workspace/server_returns/G-A027/audit_20260909/INPUT_INVENTORY.json 및 root 결과 감사 보고서.

### G-A027-RESULT-AUDIT-20260909 — 2026-09-10 재개 / H1-CAL-20260910
- 새 관찰: `_keep/GO2_A017_FULL_SUITE_RESULT.zip`, 동명 SHA, 결과 디렉터리 존재. 과거 미회수 관찰을 현재 상태로 사용하지 않는다.
- 상태: RECEIVED → VERIFIED. 외부 실행은 회수 RUNNER_STATUS의 rc=0·TRAINING=none과 대조했다. 새 학습이 아니다.
- 범위 확장: 사용자 전사 H1 공식 57.45/70과 자체 점수 비교, 보정 참고점수 추가, Go2 별도 적용 검토. 기존 채점·원자료 보존은 사용자 명시 결정이다.
- 격리: `workspace/server_returns/G-A027/received/`. training 병합 없음(MERGED 해당 없음); 상태를 임의로 건너뛰어 REPORTED로 표기하지 않는다. 로컬 감사 보고서는 별도 완료 기록.
- 검증: 반환 ZIP SHA `5108b047175c6fc0cb0982b1434c686e413bac5d75469ae9c71cb2d17d144ace`, ZIP CRC·안전 경로, 내부 manifest 882/882, 승인 package 대비 model/env 4/4 일치. tar 전용 공용 도구는 ZIP 적용 대상 밖이므로 ZIP 검사와 전용 harvest 도구를 사용했다.
- 정량: 전용 검증기 exit 0, 두 arm 69/69 `INTERNAL_MEASUREMENT_OK`. 파일 무결성 및 측정 유효성 판정이지 정책 성능 통과가 아니다.
- 산출물: `workspace/server_returns/G-A027/audit_20260910/`, `GO2_RESULT_AUDIT_G-A027_20260910.md`, `H1_OFFICIAL_CALIBRATION_20260910.md`. 초기 예정 디렉터리 audit_20260909 대신 실제 재개일 audit_20260910 사용.

### G-A027-RESULT-AUDIT-20260909 / H1-CAL-20260910 — 2026-09-11 로컬 감사 마감
- 파일 lifecycle VERIFIED 유지, training 선택병합 미실시(MERGED 해당없음). 별도 로컬 감사·보고 산출물 완료.
- H1 공식 전사·raw/보정 비교를 workspace/calibration/h1_official_20260910/에 보존. 기존 결과 덮어쓰기 없음.
- Go2 기존/보정 결과와 원자료를 workspace/server_returns/G-A027/에 격리보존. 영상7개 관찰판정 별도, 하강영상 미확보.
- 보고서 날짜260910은 감사입력일이며 마감일은260911. GO2_RESULT_AUDIT_G-A027_20260910.md와 H1_OFFICIAL_CALIBRATION_20260910.md 참조.

## 2026-09-11 사용자 결정 — 계획 경로·H1 report 회수
- 작업 ID: DOC-20260911-PLAN-REPORT. 상태: PLANNED. 로컬 문서 이동·회수 스크립트 보완이며 서버 실행은 하지 않는다.
- 계획: 기체별 upload/plan으로 계획서·실험 PRD·기획 브리프를 이동하고 참조/빌더 입력을 갱신한다. 회수 snapshot·승인 ZIP·실험 JSON·상태/일정 원장은 이동하지 않는다.
- H1: training/humanoid/exported/report.html을 _keep/<RUN_ID>/exported/report.html에 보존한다. 누락/이전 실행 report는 성공 회수로 표시하지 않는다. 기존 final 경로는 호환 보존한다.
- 검증: 이동 전후 SHA256, 링크·빌더 경로, report 복사 정상/누락/stale 테스트, bash -n. 학습·채점 로직은 변경하지 않는다.

### DOC-20260911-PLAN-REPORT 완료 기록
- 상태: REPORTED (로컬 작업). 서버 실행·배포는 미수행.
- 이동 11건: H1 2건, Go2 9건. 이동 직후 원본 SHA 일치 확인. 경로 참조 수정 후 해시는 PLAN_MIGRATION_20260911.json의 post_reference_sha256에 별도 보존. 참조 갱신 파일은 PLAN_REFERENCE_UPDATES_20260911.json.
- 검증: `python -m unittest tools.test_h1_report_recovery -v` 5 tests, exit 0; `python -m unittest tools.test_go2_feet_air_time_020_contract tools.test_go2_track_lin_vel_120_contract -q` 12 tests, exit 0; `python tools/validate_go2_campaign.py` exit 0; `git diff --check` exit 0. H1 test에 LF·bash -n·정상/누락/빈/stale report 검사가 포함된다.
- 한계: .codex/agents는 호스트 읽기 전용이므로 옛 참조를 직접 수정하지 않았다. 상위 AGENTS의 migration 매핑 우선 규칙으로 경로를 해석한다. 회수 snapshot·승인 upload release는 변경하지 않았다. 기존 패키지 빌더 테스트는 개발용 ZIP을 재생성하므로 새 서버 승인본으로 취급하지 않는다.
- 학습 배포 원본(train.py/play.py/task/reward), 채점식 및 A027 튜닝 제안값은 변경하지 않았다. H1 회수 변경은 server_run06_long.sh에 적용, 평가 전용 runner에는 현재 exported의 오래된 report를 자동 연결하지 않는다.

### H1-CAL-20260910 — 2026-09-11 제출 안내본 역추적
- 사용자 요청: 실제 제출하도록 안내했던 파일·기록으로 H1 정책과 report 대응을 확인한다. 기존 작업 ID 재사용, 로컬 읽기·해시 대조만 수행한다.
- 승인 기대값: PROJECT_STATE.md:1203-1208, UPLOAD_READY/SHA256SUMS.txt 및 RUN06_PROMOTION_SHA256SUMS.txt. 회수 report의 자체 주장만으로 제출본을 정하지 않는다.
- 역추적 완료: 제출 지시 경로 Run06 UPLOAD_READY 확인, manifest 3/3·회수 model/env 기대 SHA 2/2 일치(exit 0). SUBMISSION_INSTRUCTION_TRACE_20260911.json 보존. 외부 업로드 identity와는 분리. 서버 실행 없음.

## GO2 next tuning preparation - 2026-09-13
- User requested preparation for the next quadruped tuning. Work ID: GO2-P1-PREP-20260913. Lifecycle: PLANNED. No server execution or new training performed.
- Plan: workspace/training/quadruped/upload/plan/GO2_A027_NEXT_TUNING_PREP_20260913.md; adjacent JSON fixes 18 diagnostic cases. Existing policies, rewards and approved releases preserved.
- Evidence: existing CSV stores actual_wz, not wx/wy; run_video does not request simultaneous telemetry. Prior assumption that existing angular channels suffice is withdrawn.
- Four review findings addressed in the plan. Numeric diagnostic thresholds, separate instrumentation and independent review remain open. HOLD: package unverified, training evidence insufficient. Historical schedule remains CLOSED.
- Local verification: 5 preparation-contract assertions passed (18 unique cases); git diff --check passed. No runtime/package test claimed.
`n### GO2-P1-PREP-20260913 report follow-up`n- 2026-09-13: user requested returned A027 report review. Local discovery/content and identity checks only; no merge or server execution.

<!-- GO2:REPORT-FIRST:START -->
## 2026-09-13 연구 방향 변경 — G-D-REPORT-FIRST-20260913
- 사용자 결정: 지침과 서브에이전트에 학습 report 필독을 강제하고 연구 방향을 변경한다.
- 새 순서: report·env·학습로그/정책 대응 → 시나리오 약점 → 실패 유형/경쟁 가설 → 후보 선정.
- 이전 T1 `ang_vel_xy_l2 -0.05→-0.06`은 **DEFERRED_HYPOTHESIS**로 내린다. 다음 튜닝값/1순위가 아니며 효과 INCONCLUSIVE.
- G5 하강 생존은 현재 평가상 우선 진단 대상이나 원인은 미확정. 회전 과다, 발걸림/정지, 낮은 자세,
  학습 성숙도 및 평가/영상 대응 문제를 구분한다. 모두 가설이며 보고서만으로 인과를 판정하지 않는다.
- Pilot HTML은 직접 읽었으나 이번 작업에서 정책 대응을 완결 검증하지 않았으므로 READ_UNMATCHED.
  A017 원 학습 HTML은 현재 탐색 범위에서 MISSING / REPORT_REQUIRED_NOT_ACQUIRED.
  A027 SELF_EVAL_REPORT는 원 학습 HTML을 대체하지 않는다.
- NEXT: 로컬 원 학습 bundle·snapshot·로그에서 A017/Pilot report 대응을 먼저 회수·검증한다.
  그 후 필요한 진단을 다시 동결한다. 기존 18case 목록은 제안 범위이며 실행 승인/고정 패키지가 아니다.
- 서버 실행·reward/배포코드 변경 없음. 새 학습 HOLD — report 대응 및 진단 근거 미완료.
- 작업 ID GO2-P1-PREP-20260913 유지. 과거 승인 release와 결과는 변경하지 않는다.
<!-- GO2:REPORT-FIRST:END -->

### GO2-P1-PREP-20260913 — review bundle packaging
- Local documentation packaging only; preparation remains PLANNED. No server execution, training approval, artifact merge or policy change.
- Output (corrected by G-D-UPLOAD-PATH-20260913): workspace/training/quadruped/upload/GO2_TUNING_REVIEW_MATERIALS_20260913.zip. Includes source snapshots and manifest; not a server execution package.

### GO2-P1-PREP-20260913 — package path correction
- User decision G-D-UPLOAD-PATH-20260913: plan/ is for planning documents only; packages belong in upload/ or existing release directories.
- Local relocation of review ZIP and SHA only. Verify SHA before/after; preserve contents and historical releases. No server execution approval.

### G-D-UPLOAD-PATH-20260913 — 사용자 경로 정정
- plan/은 계획 문서 전용. ZIP·SHA·배포 manifest·실행 파일은 upload/ 또는 기존 작업별 release 경로에 저장한다.
- 검토 ZIP·SHA를 workspace/training/quadruped/upload/로 이동했고 이동 전후 SHA가 일치한다. 검토용이며 실행 승인본은 아니다.

### G-D-NUMBERING-20260913 — G-A028 예약
- G-D98/G-D175/G-D178 재확인. 원장·upload 검색에서 G-A028 기존 등록 없음; 다음 준비 회차로 예약한다.
- GO2-P1-PREP-20260913은 G-A028 준비 작업 별칭이다. 상태 PLANNED, 미실행, 학습 승인 없음.
- 검토 자료 경로: workspace/training/quadruped/upload/G-A028/review/GO2_G_A028_TUNING_REVIEW_MATERIALS_20260913.zip. 실행 정본 current/는 아직 발행하지 않는다.
- 이전 무번호 upload 루트 경로는 이 경로로 대체한다. 기존 승인 release는 보존한다.

### G-A028 — 2026-09-13 실행 준비 선행조건 실측
- 기존 G-A027 current의 RUN_GUIDE·builder·runner·발행 도구를 직접 확인했다. 다음 실행 정본도 같은 current/history/manifest/guide 체계를 사용한다.
- workspace 내 upload/history 제외 ZIP·tar.gz 52개 내부 목록까지 검색했다. A017 원 학습 report.html은 발견하지 못했다. A017 결과 ZIP(GO2_PILOT_TRACK_LIN_VEL_XY_140_RESULT.zip)에도 없다. 검색 오류 0건.
- 증거: workspace/training/quadruped/upload/G-A028/review/REPORT_RECOVERY_SEARCH.json. 기존 Pilot 계열 exported/report.html로 A017 보고서를 대신하지 않는다.
- 실제 차단: REPORT_REQUIRED_NOT_ACQUIRED 및 다음 단일 변경값 미확정. 실행 패키지 완성·서버 실행을 주장하지 않는다. report 원본은 외부 보관 사본 회수가 필요하며 과거 checkpoint로 당시 학습 HTML을 꾸며 생성하지 않는다.
- 배포 train.py/play.py/go2_task/quadruped_rewards.py 변경 없음. 학습 미실행. G-A028은 PLANNED 유지.

### GO2-REPORT-RECOVERY-20260913 — PLANNED
- User requires server-generated report.html in every future tuning _keep and result bundle. Scope: active Go2 tuning engine recovery, regression tests, guidance; no training-path edits or historical release replacement.
- Plan: preserve model/env/logs before report gate, copy report to _keep/<run>/exported/report.html, pin SHA and freshness, reject missing/empty/stale reports and incomplete resume; exercise local fixtures and ZIP/SHA inclusion.

### GO2-REPORT-RECOVERY-20260913 — 로컬 구현·검증
- 사용자 결정: 앞으로 튜닝 결과 _keep/<튜닝명칭>/exported/report.html에 서버 생성 원본을 필수 회수한다. ZIP·SHA에도 포함하며 누락/빈 파일/이전 실행 report는 REPORT_REQUIRED_NOT_ACQUIRED다.
- 공용 server_run_go2_tuning_engine_v1.sh에 학습 시작 marker, 평가 전 report 보존, SHA, resume 재검증, 누락 시 PARTIAL 회수 및 비정상 종료를 구현했다. report 검사 전에 model/env/policy/log를 보존한다. train.py/play.py/go2_task와 기존 승인 ZIP은 수정하지 않았다.
- 검증: report 전용 5개(정상 ZIP/SHA 포함·누락·빈 파일·stale·bash -n/LF), 기존 report 지침 8개: 총13개 성공. py_compile 성공.
- 전체 engine 계약19개 중16개 성공,3개는 baseline model/env identity mismatch로 실행 차단. 새 실행 ZIP 발행 완료로 주장하지 않는다. 테스트 build 출력은 임시 디렉터리로 격리했다.

### G-A028 P1 — 실행 패키지 사전등록
- PLANNED. 기존 계획 P1(학습 없는 낙상 진단)을 실행 파일로 구현한다. 보존 A017/Pilot × G5 하강10/15cm·G4 +20도 × seed101/202/303,18영상,4env,1000step. 같은 재생 telemetry 필수.
- 기존 A027 32env 정량은 재사용. 4env 새 영상 telemetry를 기존 rollout에 결합하지 않는다. wx/wy·발접촉 채널은 없으며 회전 인과와 /70 점수를 판정하지 않는다.
- report: 새 학습 없음으로 신규HTML NOT_APPLICABLE, 원 A017 MISSING/Pilot READ_UNMATCHED 유지. 실패에도 model/env·로그·부분 결과 ZIP 회수. 실제 서버 실행은 미측정.
- 종료:18영상·18유효summary·telemetry·로그·SHA 확보. 판독은 별도 VIDEO_UNKNOWN부터 시작. 새 학습은 자동 착수하지 않는다.

### G-A028 P1 — 실행 패키지 발행(2026-09-13)
- current: workspace/training/quadruped/upload/G-A028/current/GO2_G_A028_P1.zip. SHA256 0d9843681e7d1b852273a09c0964c94cef47d3ac4a8c153d5d84ee6bc25eaacf. history/20260913_p1 및 UPLOAD_HISTORY.tsv 보존.
- 기존 계획 P1의 서버 재생 실행 패키지다. P2 새 튜닝 학습 패키지와 구별한다. 가중치 변경/학습 없음. 18영상·동일 실행 telemetry/summary·로그·model/env를 단일 결과 ZIP으로 회수.
- 검증:15 tests 성공(모의18case완료·실패부분회수·기존결과보존·report 회수 포함), CRC/내부SHA30개·bash -n·py_compile·diff check 정상. 실제 IsaacLab 실행은 미측정. ARTIFACT_VERIFIED_LOCAL_TESTED, 성능 판정 아님.
- 공용 학습 engine의 Default baseline hash 문제는 P1에 해당하지 않는다. P1은 승인 A027 ZIP SHA를 직접 검증하고 두 보존 정책과 계측 소스를 그대로 사용한다. 일반 학습 engine의 남은 문제를 해결했다고 주장하지 않는다.
- 원 학습 report 공백은 유지, 새 학습 HTML은 평가 전용으로 NOT_APPLICABLE. 신규 튜닝의 report 필수회수는 공용 학습 runner에 별도 구현한 상태.
- 외부 실행 상태 PLANNED. 다음: 사용자 서버 실행·단일결과ZIP/SHA 회수, 로컬 18영상/정량/로그/identity 확인 후 판독. P2 자동 학습 없음.

### G-A028-RESULT-AUDIT-20260913 ? PLANNED ? RUNNING ? RECEIVED
- User reports download complete. Found workspace/_keep/GO2_G_A028_RESULT.zip and SHA, plus extracted GO2_G_A028_P1. Read-only source analysis; preserve original downloads. ZIP-only verification escalated from tar-only artifact verifier. Audit scope: manifest/policy identity, 18 simultaneous video/telemetry cases, report relationship and preregistered expectations. No training or source modification.

### G-A028-RESULT-AUDIT-20260913 ? result/report relationship correction
- Download verified: ZIP SHA 6e4a807b276e566e01aa58e5f12a61f01e74df999809e975220f69722794ed1e; internal SHA192/192, model/env4/4,18 valid telemetry cases.18 videos decoded, each999frames/19.98s; exact step/frame alignment unverified. ARTIFACT_VERIFIED only.
- Report body read: existing Pilot HTML READ_UNMATCHED; A017 HTML MISSING; A028 new HTML NOT_APPLICABLE(TRAINING=none). No new training occurred.
- Frozen proxy survivors (3seeds x4env): A017 stairs10=0/12, stairs15=0/12, slope+20=11/12; Pilot2/12,0/12,12/12. No /70 score. SELF_ASSESSMENT_INCOMPLETE.
- IMPORTANT correction: stairs_down label does not establish actual descent. Sampled video shows approach/stalling inside inverted stairs. Withdraw unconditional descent-fall explanation; descent coverage VIDEO_UNKNOWN.
- IMPORTANT measurement limit: approved telemetry uses mean scanner ray height, not ground directly under body. Stair boundary bias can contribute to low-height verdict; physical fall interpretation INTERNAL_GATE_INCONCLUSIVE. Applies to same A027 measurement method too; preserve historic numeric outputs, do not promote them to verified physical falls.
- Report does not replace videos,steps.csv,execution logs or policy/config identity. Current strongest observed problem is stair stalling, not proven excessive roll/pitch. -0.06 remains DEFERRED_HYPOTHESIS; no new training or reward change authorized by these results.
- Evidence/report: workspace/server_returns/G-A028/audit_20260913/REPORT_RELATIONSHIP_AUDIT.md; case_metrics.json, artifact_verification.json, video_validation.json, contact sheets. Original downloads preserved; ZIP/SHA copied to workspace/server_returns/G-A028/received/. No training merge.
- File lifecycle RECEIVED ? VERIFIED. MERGED not performed (no training merge); separate analysis/report work completed. Future action: resolve scenario/height semantic gaps before selecting a reward; no server action requested.

### GO2-ALL-SCENARIO-PRIORITY-20260913 ? PLANNED ? RUNNING
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 대체 기록 미확보(저장소에서 `GO2-ALL-SCENARIO-PRIORITY-20260913`의 정상 기록을 찾지 못했다).
- ??? ??: ?? ??? ????? ?? G1~G7? ?? ??? ????? ?? ????? ????? ??. ?? A027/A028 ?? ??? ??? ????? ????? ??? ???? ???. ?? ??? ?? ??? ????.

### G-A029 — 2026-09-14 난이도 기반 튜닝 파일·회수 계약 점검
- 작업 상태 PLANNED. 원장 및 upload에서 G-A029/G_A029 중복 없음 확인 후 예약.
- 사용자 요청: 난이도 기반 튜닝 정책에 맞는 파일 준비, 서버 원본 report.html 회수와 파일 양식 검증.
- 범위: 로컬 검토 spec·계획·회수 테스트. 새 reward 후보 확정/서버 실행/학습/기존 release 변경 없음.
- REPORT_REQUIRED_NOT_ACQUIRED(A017) 및 다음 단일변수 근거 미확정으로 current 실행본 발행 금지. review 자료만 생성.
- 영상: 이번 로컬 테스트는 정책 미생성으로 VIDEO_NOT_REQUIRED. 향후 실제 튜닝 영상은 필수이며 대상 case/seed/수량은 실행 전 동결.

### G-A029 — 2026-09-14 로컬 검토 파일 및 회수 검증 결과
- 사용자 요청을 난이도 기반 검토 정책으로 기록: 낙상 완치 대신 기대 이득·비용·원인 확실성을 함께 비교. G3 또는 특정 reward의 실행 우선순위 확정은 아님.
- 계획: workspace/training/quadruped/upload/plan/GO2_G_A029_DIFFICULTY_SCREENING.md.
- 검토 파일: workspace/training/quadruped/upload/G-A029/review/GO2_G_A029_TUNING_REVIEW.zip (+SHA). 실행 JSON과 구별되는 NON_EXECUTABLE_TUNING_REVIEW, execution/training=false, single_change=null. current 미발행.
- 회수·지침·엔진 계약 총32 tests 성공. 정상 report의 ZIP/SHA 포함, missing/empty/stale 거부, bash -n/LF 확인. 회수 후 본문과 정책 의미 대응은 별도 필요.
- 발견/수정: 러너 CRLF를 LF로 정규화하고 .gitattributes로 고정. Windows shell fixture PATH 고정. 엔진 계약 테스트가 기존 ZIP을 덮어쓰던 부작용을 임시폴더 빌드로 차단.
- 이번 테스트가 변경한 기존 엔진 ZIP/SHA 두 파일만 초기 clean 상태 및 HEAD=index 확인 후 원 바이트 복원. 후속 테스트에서 두 파일 불변 확인. 승인 upload/current/history 변경 없음.
- 증거: review/GO2_G_A029_VALIDATION.json 및 GO2_G_A029_TEST_OUTPUT.txt. ZIP CRC/내부SHA 확인. 실제 서버/성능 미측정.
- A017 원 학습 report MISSING 및 변경값 미확정 유지. 로컬 파일 준비 완료이나 학습 작업 상태 PLANNED, 실행본 생성은 HOLD. 이전 engine baseline 실패 기록은 이번 로컬19개 계약 테스트 성공으로 현 상태 정정하며 A017 실행 spec 검증 완료를 뜻하지 않음.

### G-A029 ? ?? ?? ?? ? ?? ??? ?? ?? (2026-09-14)
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 관련 정상 기록: 같은 파일 위 「G-A029 — 2026-09-14 난이도 기반 튜닝 파일·회수 계약 점검」 절. 두 절의 내용이 같은지는 확인할 수 없다.
- ?? ?? ID ??. ?? ???? ??? reward ?? ??/?? ??. ?? lifecycle PLANNED ??. ? ?? report ???? ? ?? ??/?? ??/?? current ?? ??. ?? artifact ? ?? release ??.

### G-A029 ? 2026-09-14 ?? ?? ?? ? ?? ??? ??
> **CORRUPTED — 인코딩 손상, 근거 사용 금지(2026-09-14 표시, G-P-A029-REVISION-20260914).** 원문을 복원·삭제하지 않는다. 같은 주제의 확인한 정상 기록: `workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md`, `workspace/training/quadruped/upload/G-A029/review/GO2_G_A029_ACTION_RATE_M0008_DRAFT.json`. 손상 줄의 "35 unittest" 검증 결과는 대체 기록 미확보(`review/GO2_G_A029_TEST_OUTPUT.txt`는 32 tests로 다른 회차다).
- ??? ??: ?? ?? ??? ???? ???? ????? ?? ?? ?? ??. ?????? ?? ??? ?? ???.
- ?? ???: workspace/training/quadruped/reports/GO2_G_A029_WEAKNESS_ANALYSIS_20260914.md. G3/G7 ?? ??? ?? ???? G1/G2 ???G4/G6 ?? ??, G5 ??? ?? ????. ?? ??? ?? ??? ?????? ?? ???.
- A017 ??? ??: action_rate_l2 -0.01?-0.008(20% ?? ???, ??/??? ???). ?? Python reward ?? ??? baseline ??, ??? JSON? upload/G-A029/review? ??. ?? ??? ?? ??? ??.
- REPORT_READ_STATUS: A017 MISSING, Pilot READ_UNMATCHED ??. ?? ??: ?? engine? A017 frozen baseline ???, ?? manifest ? ?? ?? ?? ???. ?? ?? ??/current/history ?? ??.
- ?? ??: 35 unittest ??(?????Python ??/LF??????report fresh/missing/empty/stale?ZIP/SHA?shell ???engine ??). ?? ??/?? ?? ???. ?? lifecycle PLANNED, ?? ?? ??.

### G-A029 — 2026-09-14 continuation resume audit
- NEW-CONTINUATION; existing work ID retained, lifecycle PLANNED. Scope: plan section 3 only; inspect newly available report copies, no repeat of 52-archive scan, no server/training/release mutation. Local read-only checks require no new video (VIDEO_NOT_REQUIRED: no policy generated).

### 2026-09-14 G-A029 §3 종료 — HOLD / 원 보고서 회수
- NEW-CONTINUATION으로 지정 계획 §3을 종료했다. -0.008은 조건부 실험 가치만 인정하며 후보 확정/학습 승인이 아니다. A017 REPORT_READ_STATUS=MISSING / REPORT_REQUIRED_NOT_ACQUIRED로 실행본 발행 차단.
- 기존 52archive 재검색 없이 목록 밖 ZIP 6개를 확인했으나 report.html 0개. 상세 경로·직접 코드/로그 근거·한계는 GO2_REWARD_EVIDENCE_MASTER.md의 같은 날짜 §3 판단 종료 행과 기존 인계 계획에 기록했다. 깨진 과거 append는 판정 근거에서 제외한다.
- NEXT 하나: A017 원 학습 report.html 외부 보관 사본 회수 → run/env/log/model_900 대응 확인 → 기존 계획 §4 패키지 구현·검증. 추가 서버 진단이나 새 검토 ZIP을 만들지 않는다.
- G-A029 PLANNED, 단계0/6, 서버/학습/실행 ZIP 발행 없음. 역사 일정 CLOSED 유지. 원 자료·승인 release 보존.
### GO2-REPLAN-A029-20260914 — PLANNED
- 사용자 요청: G-A029 감사에 따른 문제 진단과 튜닝 계획. 로컬 원자료 읽기 및 계획/원장 동기화만 수행; 서버 실행·패키지 발행 요청으로 확대하지 않는다. G-A029 REJECTED_BY_AUDIT와 review 보존.
- VIDEO_NOT_REQUIRED: 이번 작업은 정책을 생성하지 않는 로컬 기획. 미래 후보 평가 영상은 필수. 외부 실행 [미측정].

### GO2-REPLAN-A029-20260914 — 감사 후 사용자 요청 재계획
- 사용자 결정: G-A029 감사에 따라 메인 문제를 진단하고 튜닝 계획을 수립한다. 이번 요청은 계획이며 서버 실행/패키지 발행으로 확대하지 않는다. 역사 일정 CLOSED는 유지한다.
- G-A029 REJECTED_BY_AUDIT 및 -0.008 NEXT 철회 유지, review 불변. 과거 A017 HTML 누락을 발행 차단으로 복원하지 않는다.
- 계획 정본: workspace/training/quadruped/upload/plan/GO2_POST_A029_TUNING_PLAN_20260914.md.
- 직접 근거: A018 양 arm 각7case 모두 schema2/v2; A013/A025 baseline은 schema1/2 혼재, candidate는 schema2라 합산 비대칭. A027 G3 rough_lateral seed101/202/303의 base-contact 종료는 17/14/17개(/32), 첫 종료 전0.5초 q=1-gz² 평균 .688/.628/.660. 기울기는 연관성이지 최초 원인 확정 아님.
- 계획값: A017 조건 flat_orientation_l2 0→-1.0 단일변수, G3 접촉 종료/생존 표적; G5 정체·경사 회귀 동시 감시. -1은 관측 기반 단위 크기 exploratory 값이지 upstream 최적값/만족 판정 아님.
- REPORT_READ_STATUS: A017 MISSING(기존 복구 불가 확정 유지), Pilot READ_UNMATCHED(이번 HTML 본문 직접 열람, 정책 대응 미완결).
- NEXT: 다음 미사용 번호로 위 계획의 current 실행 패키지 구현·검증. 이번에 번호 예약/실행 ZIP/서버 명령은 발행하지 않았다. 학습·성능·공식 결과 새 측정 없음.
- 작업 완료: 로컬 분석·계획 REPORTED. 외부 artifact lifecycle은 실행/수신/병합이 없어 진행시키지 않는다. 원 artifact 변경 없음.

### G-A030 — 2026-09-14 실행 패키지 발행 (ARTIFACT_VERIFIED, 서버 미실행)
- 근거: 사용자 결정 `G-D-A030-GO-20260914`(`GO2_PROJECT_STATE.md`). A017 + `flat_orientation_l2 0.0→-1.0`, 측정 경로 (나′).
  - C 보류는 로컬 패키지 범위에서만 풀렸다. 서버 실행은 사용자 결정 대기다.
- 업로드 1개: `workspace/training/quadruped/upload/G-A030/current/GO2_G_A030_flat_orientation_m1.zip`.
  - SHA256 `e4fbdc0033866612ca9804f9479416d7d4e188bf403b23078cdb6591f35eab05`.
  - 서버 위치: `/workspace/GO2_G_A030_flat_orientation_m1.zip`.
  - 한 줄 실행·완료 표식·재측정 명령·종료 게이트는 같은 폴더의 `GO2_G_A030_RUN_GUIDE.txt`에 있다.
- 결과: `/workspace/_keep/GO2_G_A030_RESULT.zip`과 `.sha256` → 로컬 `workspace/_keep/`. 압축을 풀면 `workspace/_keep/go2_g_a030_a017_flat_orientation_m1/`이다.
- 필수 회수물:
  - `exported/report.html`(REPORT_ACQUIRED, 평가 전 보존)
  - 학습 model/env/로그/tfevents, `ENV_REWARD_CHECK.txt`
  - 후보 69 case telemetry
  - A017 표지 5건(재측정 시 69건)
  - 영상 14개(후보 12, A017 2)
  - RUNNER_STATUS, SHA256SUMS
- 서버 종료 게이트: 결과 ZIP·SHA를 받고 로컬 검증이 끝나기 전에는 종료 가능이라고 하지 않는다.
- 회수 검증(GPU 0, 수치 판독 전): `python -B tools/verify_go2_g_a030_harvest.py --harvest workspace/_keep/go2_g_a030_a017_flat_orientation_m1 --out workspace/_keep/go2_g_a030_a017_flat_orientation_m1/harvest_verification.json`
  - INCONCLUSIVE면 점수를 읽지 않는다.
  - BASELINE_REMEASURE_REQUIRED면 `GO2_RESUME=1 GO2_REMEASURE_BASELINE=1`로 A017 69건을 같은 evaluator에서 다시 잰다.
- 영상: VIDEO_REQUIRED. 사람 판독 전에는 VIDEO_UNKNOWN이다.
- 로컬 검증 증거:
  - `tools/test_go2_g_a030_package_contract.py` 24/24, 기존 Go2 테스트 46개와 A017 full-suite 계약, `GO2_CAMPAIGN_CONTRACT_OK`.
  - ZIP 재빌드 동일 SHA, current=history 바이트 동일, SHA sidecar 일치.
  - 회수 검증기 합성 smoke 5종 기대 판정 일치.
  - 러너 preflight 모의 실행이 tmux 기동까지 통과했다. 변조 evaluator와 잘못된 플래그는 거부했다.

### G-A031 + G-A032 쌍 — 2026-09-15 서버 실행·회수 (RECEIVED, 로컬 검증 FAIL·FAIL)
- 업로드: `upload/G-A031_A032/current/GO2_G_A031_A032_basic_motion_pair.zip` `e714d948…7e6c` (계획 §9-1).
- 서버 실행: 13:46~15:59, 두 회차 1단계만.
- 회수: `workspace/_keep/GO2_BASIC_MOTION_PAIR_RESULT.zip` `5ad3f8fd7dd6430bfe68697cb39ec29c410f2aa60b1afb49ae14e4b295050c60`.
  - 안의 `arm_results/`: G-A031 `bd154bc6…0ad9`, G-A032 `a9e9db07…7dd0`.
  - 로컬 `_keep`에 풀린 폴더: `go2_basic_motion_pair_a031_a032/`, `go2_g_a031_a017_feet_air_time_001/`, `go2_g_a032_a017_feet_air_time_010/`.
- 검증: SHA·CRC·내부 SHA256SUMS 일치. `tools/verify_go2_basic_motion_harvest.py` 두 회차 FAIL(1_target_basic_motion), 결함 0.
- 서버 종료: 로컬 검증 뒤 종료 가능 보고(2026-09-15).
- 알려진 결함: 쌍 러너가 게이트 FAIL을 UNDECIDED로 기록했다(`isaaclab.sh -p` 종료 코드 변환). 결과 동일. 후속 러너에서 수정(아래 G-A033).

### G-A033 — 2026-09-15 한 파일 패키지 발행 (ARTIFACT_VERIFIED, 서버 미실행)
- 근거: 계획 §6-3 규칙(`feet_air_time` 쌍 실패 → 0.2 유지, `track` 1.4→1.5), 계획 §12.
- 업로드 1개: `workspace/training/quadruped/upload/G-A033/current/GO2_G_A033_track_lin_vel_xy_150_one_command.zip`.
  - SHA256 `4ddb46da3f1f2526c34f0b843f8583d063104598cb29792758de9ec47d311595`.
  - 서버 위치: `/workspace/GO2_G_A033_track_lin_vel_xy_150_one_command.zip`.
  - 한 줄 실행·완료 표식·재시작 규칙은 같은 폴더의 `GO2_G_A033_ONE_COMMAND_RUN_GUIDE.txt`에 있다.
- 안의 회차 ZIP: `GO2_G_A033_track_lin_vel_xy_150_staged.zip` `0e873d6532f1c6bd98cb726a6de9e92ab5eb413e75cc5feb3e93e6a97ddac7a2`(history에만 있음, 따로 올리지 않는다).
- 결과: `/workspace/_keep/GO2_G_A033_CAMPAIGN_RESULT.zip`과 `.sha256` → 로컬 `workspace/_keep/`.
- 회수 검증: `python -B tools/verify_go2_basic_motion_harvest.py G-A033 --harvest workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150`.
- 서버 종료 게이트: 결과 ZIP·SHA를 받고 로컬 검증이 끝나기 전에는 종료 가능이라고 하지 않는다.

### 2026-09-15 G-A034 A017 오르막 정지 로봇 영상 확인 패키지 (학습 없음)
- 업로드: `workspace/training/quadruped/upload/G-A034/current/GO2_G_A034_slope_inspect.zip` SHA256 `fa4772d66ac1ccbac14f298bbb566e6016c08c0a4abc18fa31660e303908dbc8` (6.4 MB)
- 내용: G-A027 패키지의 A017 정책·play.py·evaluator를 바이트 그대로 재사용(model SHA `0563deff…95a4`) + `server_run_go2_slope_inspect.sh` + `go2_slope_stuck_check.py`
- 목적: slope_plus_20 seed 101에서 저장 기록상 넘어진 로봇 4·18·20·22·24·27·31 중 22·24·4와 대조군 0을 카메라로 따라가 원인(제자리걸음·미끄러짐·웅크림·막힘·뒤로 밀림)을 눈으로 확인
- 결과: `/workspace/_keep/GO2_SLOPE_INSPECT_RESULT.zip` (영상 4개, 재측정 기록, STUCK_CHECK.txt의 재현 판정 REPRODUCED/NOT_REPRODUCED)
- 검증: runner bash 문법 통과, 재현 판정 스크립트는 저장 데이터에서 MATCH, 잘못된 기준 목록에서는 NOT_REPRODUCED. 이 Isaac Lab 버전의 viewer에 env_index가 있음은 저장된 env.yaml에서 확인. GPU 실행 0회, 실행 시간은 미측정

### 2026-09-15 G-A033 v2 발행 — `track` 1.4→1.5, iter 900 고정 평가 (서버 미실행)
- 업로드: `workspace/training/quadruped/upload/G-A033/current/GO2_G_A033_track_lin_vel_xy_150_iter900_one_command.zip` SHA256 `88be31980a05bac6e1cd2ba72be4cd4e5594119641f7b557a732665a6a85ae41` (6.2 MB)
- 한 줄: `cd /workspace && echo '88be31980a05bac6e1cd2ba72be4cd4e5594119641f7b557a732665a6a85ae41  GO2_G_A033_track_lin_vel_xy_150_iter900_one_command.zip' | sha256sum -c - && unzip -oq GO2_G_A033_track_lin_vel_xy_150_iter900_one_command.zip && bash /workspace/go2_campaign_g_a033/server_run_go2_campaign.sh`
- 완료 표식 `[DONE] GO2_G_A033_CAMPAIGN_RESULT_READY`, 결과 `/workspace/_keep/GO2_G_A033_CAMPAIGN_RESULT.zip` + `.sha256`
- v1(`GO2_G_A033_track_lin_vel_xy_150_one_command.zip` `4ddb46da…1595`)은 미실행으로 history에 보존. 서버 종료 판단은 결과 수신 후 로컬 검증을 통과한 뒤.
- 회수 확인 항목 추가: `training/CHECKPOINT_PIN.txt`(EVAL_CHECKPOINT_ITER=900), `training/model_best.pt`(평가한 iter 900), `training/model_best_by_reward.pt`(finalize 선택)

### 2026-09-15 G-A033 v2 서버 결과 회수 (서버 종료 가능)
- 결과: `workspace/_keep/GO2_G_A033_CAMPAIGN_RESULT.zip` SHA256 `b136e708eaccd8b985c3334d52f352061c349eebf2f50bcfabe021651f944154`, 회차 `workspace/_keep/GO2_G_A033_RESULT.zip` SHA256 `57019d2513caa118213cca9941e7ac2d69b8690357b86cf8575b83ab3ea9a10c`
- 풀린 폴더: `workspace/_keep/go2_campaign_g_a033/`, `workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/` (ZIP과 파일 단위 동일)
- 로컬 검증: `python -B tools/verify_go2_basic_motion_harvest.py G-A033 --harvest workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150 --out .../reports/LOCAL_VERIFY_G_A033.json` → FAIL, artifact 결함 0, ruler 불일치 0, 핀 900 확인
- 서버에 남길 것 없음: 모델(900·700)·영상 5·로그가 ZIP 안에 있다

## PM-REPAIR-STRATEGY-20260919

User requested local judgment-validator fixes and evidence-based tuning strategy review. No server execution, new package, reward change or artifact merge. Baseline remains G-A033; last training is G-A038 (2026-09-17). G-A040 is INFORMATION_RUN, not a release or performance promotion. Results and limitations: `workspace/training/quadruped/upload/plan/GO2_PM_REPAIR_STRATEGY_20260919.md`. Existing archives unchanged. VIDEO_NOT_REQUIRED for this tool-only change; no fresh video observation claimed.

### G-DATA-STANDARD-20260920 로컬 후속 검증
- 위 명세 누락 시험과 생성기 수정 완료: 관련 51 tests 성공, 5개 표 129행 재생성. 원자료/legacy CSV/배포 학습 코드 변경 없음. 원 집계 생성기 이관과 raw 재계산은 미완료. 회수/병합 작업 아님.

## G-HANDOFF-MONITOR-20260920 — 전달 감시자 대조 시험
- 로컬 시험 완료. 신규 회수·병합·학습 없음. 원자료와 배포 코드는 변경하지 않음.
- 실제 analyst에 증거 관리자 역할을 부여: 오류 5개(T1/T3/T5/T6/T7)를 모두 기각하고 제한적 정상 주장 3개(T2/T4/T8)를 수용. verifier가 원 CSV와 생성 코드를 별도 확인하여 8개 판정에 동의.
- 독립 감사는 추가 오류 M1(both_channels가 동시 발생을 증명), M2(자동 검사 성공이 의미 정확성과 전 인계 자동 감시를 증명)도 기각. M1/M2는 실제 관리자 발언이 아니라 PM이 주입한 시험 주장임.
- 자동 검사: 초기 5개 모듈 51 tests 성공. 메모리 내 formula/kind/population 허위 변조 3개는 normalize가 모두 수용. 구조 검사의 의미 검증 한계를 재현.
- 감사 중 PM의 PowerShell→Python 기록 경로에서 이 항목의 한글이 물음표로 손상된 것을 encoding 검사로 발견. apply_patch로 해당 신규 항목만 복원하고 재검증. 감사자가 사용한 50-test 조합은 초기 51-test 조합과 다름.
- 판정: 이번 사례의 의미 검토 INTERNAL_GATE_PASS. 자동 전 인계 차단, 일반 오류 검출률, 원자료 전체 재계산은 미검증. 이번 시험은 PM이 명시적으로 전달한 1회 대조 시험이며 기획자·분석가 전체 연쇄 실행은 아님.
- VIDEO_NOT_REQUIRED / REPORT_READ_STATUS=NOT_APPLICABLE — 정책 행동·튜닝값 선정이 아닌 데이터 인계 의미 검사.
- 최종 재검증: data_standard + inference_integrity + detectability + canonical_consistency + evidence_role + role_regression 6개 모듈 58 tests, 9.523초, 종료 코드 0. 인코딩 손상 복원 후 결과이며 초기 감사 실패를 은폐하거나 동일 실행으로 합산하지 않음.
# G-HANDOFF-MONITOR-20260920 운영 반영

- 사용자 요청으로 공통 인계 계약과 기체 지침에 INPUT_REVIEW/OUTPUT_REVIEW/PM_REVIEW 및 버전별 검토 기록, 재사용·재검사·UNKNOWN 처리와 감사 독립성 반영.
- 신규 계약 테스트 실패를 먼저 확인한 뒤 명세 수정. 기존 역할 파일은 공통 계약 참조를 유지하며 보호된 역할 디렉터리를 수정하지 않음. 자동 런타임 훅은 추가하지 않음.
- 원자료·배포 학습 코드·역사 ZIP 변경 없음. 영상/학습 report 비해당인 운영 절차 변경.

## G-A047-RECEIPT-20260926 — 다운로드 검토
- 상태: PLANNED → RUNNING → RECEIVED. 사용자 다운로드 통보 및 workspace/_keep/GO2_G_A047_RESULT.zip 도착 확인.
- 원본 ZIP·해제본은 보존. 무결성, report identity, 69 case·sentinel 5·후보 영상 8·재사용 영상 8 및 로컬 판독 확인 중. 성능·서버 종료 미판정.

- G-A047-RECEIPT-20260926 갱신: RECEIVED → VERIFIED. ZIP SHA·CRC 정상, 내부 SHA 530건·해제본 531건 대조, 69 case/sentinel 5 수집, 후보 영상 8 + 재사용 영상 8 지문 일치, report READ_MATCHED. 로컬 판정 fact_rules FAIL / screening INTERNAL_GATE_FAIL. 성능 실패, NO_CANONICAL_MERGE라 MERGED로 전진하지 않는다(ANALYZED·REPORTED). 판독 `workspace/training/quadruped/reports/GO2_G_A047_READOUT.md`(2026-09-26 한글 깨짐을 원 JSON에서 복구).
## G-A048-LOCAL-REVIEW-20260926 — 다운로드 검토
- 상태: PLANNED → RUNNING → RECEIVED. 사용자 다운로드 ZIP·SHA·해제본을 검사한다. 원자료 및 기존 정책은 덮어쓰지 않는다.
- 필수: 원 학습 report·env·로그·평가 iter900 checkpoint, 후보69 telemetry·sentinel5, 후보영상10 및 저장 기준선영상10의 SHA·identity 대응.
- 검증 출력: `workspace/server_returns/G-A048_REVIEW_20260926/`. 채택 판정과 사전등록 가설 판정은 분리한다. 서버 종료 판단은 회수 검증 이후 한다.
- RECEIVED → VERIFIED. 결과 ZIP SHA `89698d3f806e0dd321610148bb36cc6f425e2a3c5752d59ca2e6692bab307389`, CRC·537파일 대응·결과 SHA536件 일치. provenance32件는 원 발행 ZIP과 대조 일치. full69·sentinel5·원 report·후보영상10/재사용10 회수. 필수 추가 회수 없음, 서버 종료 가능.
- 분석·보고 완료, NO_CANONICAL_MERGE로 MERGED 상태를 부여하지 않음. 내부proxy50.15656/70이나 screening15cm3항 실패: INTERNAL_GATE_FAIL/A033 유지. `reports/GO2_G_A048_READOUT.md` 참조. 영상은3종 표본 프레임 관찰, 전체 VIDEO_UNKNOWN.

## G-A058 — 보상 무변경 재학습 v1: A048 seed 42, A043 seed 43·44 (2026-09-30, 상태 PLANNED)
- 발행: `workspace/training/quadruped/upload/G-A058/current/GO2_G_A058_replicate_a048s42_a043s43s44_v1.zip` SHA256 `ece5a1900cf7b1da5d348c68c9d4423a42c1892322a9c75b47bc0ddc79362da2`, 안내 `GO2_G_A058_RUN_GUIDE.txt`. 빌더 `tools/build_go2_g_a058_replicate_package.py`, 러너 `tools/go2_g_a058_run_sweep.sh`(G-A057 러너에서 이름만 교체), 행별 러너·shared 는 G-A055 v2 바이트 그대로.
- 근거·순서·판독: `workspace/training/quadruped/upload/plan/GO2_OTHER_PC_SEQUENCE_PROPOSAL_20260930.md`(Codex 합의 2026-09-30). 다른 PC에서 G-A057 첫 행(track 1.2) 뒤, 나머지 11행보다 먼저 돈다. 인계 §7 'A048 반복 실행 안 함'은 이 한 번의 대조 실행에 한해 변경(Codex).
- 판독: A048 seed 42 는 비교 기준이며 효과 판정 문턱이 아니다. A043 행은 개별 정책(15cm ≥50 · 우회전 ≤5 → 후보 검증)과 설정 재현성(두 seed 합)을 나눠 판정. 경계는 탐색용. 다른 PC 정책은 제출 후보가 아니다.
- 영상 판정: 필수 — 러너가 실행마다 후보 영상 10편을 결과 ZIP에 넣는다. report.html 포함.
- 검증: tools/test_go2_g_a058_replicate_contract.py 9 통과(보상=기준 env.yaml, seed 42/43/44, shared=G-A055 v2, 실행별 체크섬, 러너 이름 교체만, 가짜 러너 완료·실패 계속·재개·학습 전 실패 23). 발행 ZIP SHA·SWEEP 체크섬·세 트리 체크섬·bash -n·CRLF 없음 확인.

## G-A057 — A048 보상 단일변수 일괄 탐색 v1 (2026-09-29, 상태 PLANNED)
- 발행: `workspace/training/quadruped/upload/G-A057/current/GO2_G_A057_a048_single_var_sweep_v1.zip` SHA256 `c225879e4e2730fa768b32aef4b3e374b14baae83a002ffacdaa92010e9e3484`, 안내 `GO2_G_A057_RUN_GUIDE.txt`. 새 학습 12개(순서 SWEEP_PLAN.json 그대로), 재사용 6, 기준 공유 5. seed 43·A043+0.01 행 없음.
- 사전등록: `workspace/training/quadruped/reports/evidence/go2_g_a057_sweep_plan/PREREGISTRATION.json`(ZIP 안 `go2_g_a057/PREREGISTRATION.json`), 판독 `tools/go2_g_a057_prereg_readout.py`. 채택·승급 대상 아님.
- 영상 판정: 필수 — 실행마다 러너가 후보 영상 10편을 찍어 결과 ZIP에 넣는다. report.html 은 러너가 결과 ZIP·SHA 에 포함한다.
- 상태 단어: 완료 DONE/SKIP_DONE · 실행 안전 중단 SAFETY_STOP_NONFINITE/SKIP_SAFETY_STOPPED/ABORT_* · 실행 실패 RUN_ERROR/COLLECTION_FAILED. 평가 결과로 멈추지 않는다.
- 검증: tools/test_go2_g_a057_sweep_contract.py 16 · test_go2_g_a057_prereg_contract.py 9 · test_go2_g_a057_sweep_compare_contract.py 8 통과. 서버 실행 승인은 별개(미승인).
