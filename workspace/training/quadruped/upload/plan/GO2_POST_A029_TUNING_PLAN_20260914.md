# G-A029 감사 후 Go2 튜닝 재계획

작성 2026-09-14 · STAY · 직접 분석/기획. 작업 ID `GO2-REPLAN-A029-20260914`.
사용자 요청은 문제 진단과 계획이다. 이번 문서는 실행 패키지의 대체물이 아니며 서버 명령을 발행하지 않는다.
G-A029는 `REJECTED_BY_AUDIT` 유지. 기존 review·승인 ZIP·원자료를 변경하지 않는다.

> **상태(2026-09-14 추가, 본문 미수정):** 이 계획의 `flat_orientation_l2 -1.0`은 **미확정 탐색 후보**다. 최우선으로 확정하지 않았고, C 단계 보류 중이다. 후보 비교(원장 §5, G-D-PRIORITY-20260914)와 측정 경로 결정이 먼저이며, §6 NEXT의 "실행 패키지 구현"은 그때까지 효력이 없다. 근거: `reports/GO2_POST_A029_PLAN_POLICY_AUDIT_20260914.md` §6·§7. 현재 상태는 `GO2_NOW.md`가 우선한다.

## 0. 예선 기준 현재 위치
- [예선 목표] 설계 의도 20·리포트 10의 근거 정합성 복구, 시뮬레이션 70의 G3 생존 개선 실험 설계. 문서 점수는 미감사.
- [현재 단계] 2/6 — 짧은 학습 pilot 후보 재선정. 역사 계측의 물리적 해석 한계는 별도 유지.
- [확보] A027 A017/Pilot 각 69case 평가, A017 학습 로그, A018 양 arm v2 결과, A028 관찰 기록.
- [미확보] A017 원 학습 HTML(복구 불가), 새 후보 성능·독립 학습 seed 재현·공식 결과. G5 실제 하강/전도는 미확정.
- [이번 테스트] 로컬 원 CSV의 종료 원인·종료 전 기울기 확인. 학습/서버 테스트 아님.
- [흐름] A027·A028 확보 → **감사 후 후보 재계획** → 내부 실험 기준 충족 시 독립 seed → 실패 시 후보 철회 → 최종 평가·제출.
- [지금 할 일] 서버 실행 없음. G-A029 review 파일을 실행에 사용하지 않는다.
- [보장하지 않음] 단일 seed·학습 reward·내부 proxy로 공식 점수나 통과를 보장하지 않는다.

## 1. 내 문제 진단 — 증거와 추론

| 순위 | 진단 | 확신 | 재발 방지 |
|---|---|---|---|
| 1 | 기존 실패 실험 A018을 누락하고 같은 -0.008을 다시 추천했다 | 높음: 감사 §2, 원 TIER1_DECISION | 후보마다 동일 항의 전 실험과 evaluator 대칭성 표를 먼저 작성 |
| 2 | 최대 손실과 약한 인수 대신 속도 부족이라는 눈에 띄는 증상을 골랐다 | 높음: A027 scenarios | 손실을 survival×tracking으로 분해하고 변경 표적과 연결 |
| 3 | 20% 완화를 값의 근거로 사용했다 | 높음: A029 value_basis | 관측된 상태에서 항의 크기와 부작용을 계산하고 탐색값임을 명시 |
| 4 | 과거 HTML의 복구 불가 공백을 영구 HOLD로 만들고 실행 요청에 review를 제공했다 | 높음: 최신 사용자 결정·원장 | 과거 누락은 한계로 보존, 새 run 원본 회수는 필수. 계획과 실행 산출물 구별 |
| 5 | 많은 로컬 계약 테스트를 튜닝 가설의 타당성과 혼동했다 | 추론, 중간 | 패키지 검증·행동 관찰·내부 성능을 각각 보고 |

감사 자체도 무비판적으로 복사하지 않는다. A013/A025 baseline은 전부 v1이 아니라 **schema1/2 혼재**다.
각 baseline 7case와 candidate 7case를 직접 읽었다. candidate는 모두 schema2/v2이며 rough_forward baseline은 schema1이다.
따라서 합산 비교는 비대칭이라 무효지만, 모든 개별 기록이 무효라는 뜻은 아니다.
A018은 baseline/candidate 각각 7case 모두 schema2/posture_gate_v2다. 원 결정의 46.49124→2.09260 /70,
차이 -44.39864와 7/7 생존 후퇴를 확인했다. 이는 해당 실험의 유효한 내부 실패이며 모든 seed·조합에서 해롭다는 증명은 아니다.

근거: `reports/GO2_G_A029_TUNING_AUDIT_20260914.md:24-49`,
`workspace/_keep/go2_g_a018_pilot_action_rate_m008/reports/TIER1_DECISION.json`,
`workspace/_keep/go2_g_a0{13,25}_flat_orientation_m1/evaluation/{baseline_tier1,candidate}/cases/seed_101/*/summary.json`.

## 2. report·정책 identity

- A017 `REPORT_READ_STATUS=MISSING`; `REPORT_REQUIRED_NOT_ACQUIRED — 복구 불가`라는 기존 확정을 유지한다. archive 재검색·복구 요청 반복 없음.
- A017 원 로그 `workspace/_keep/go2_g_a017_pilot_track_lin_vel_xy_140/logs/candidate_training.log:33222` 및 말미를 직접 읽음:
  학습 run 2026-09-04_22-24-51, 최고 reward 19.781@856 → **model_900.pt** 선택, 학습 최종999.
  terrain4.25·학습낙상 진단10.6%·std0.548은 원 로그의 학습 요약이며 시나리오 지표가 아니다.
- A027 A017 `SELF_EVAL_REPORT.json` identity: model SHA `0563deffae52552cdf0343d16b95baaa2bdcc924eca4c53e24f58a0c53d295a4`,
  env SHA `41050c084cd05e7646ce2cb4ac34e06a6870fb7a65b4f767c5714611b9a801ff`, evaluator SHA `353614487a903e0347e7142396ce2e13c5133169950b1839b6dc26287a930d84`.
  이번에는 기록을 대조했으며 모델 파일을 새로 해시/텐서 검증했다고 주장하지 않는다.
- Pilot `workspace/training/quadruped/exported/report.html` 본문 전체를 직접 읽음: 2026-08-31 15:42~16:40,
  최종999/1000, 최고18.02@972, terrain3.94, 마지막10회 학습낙상13.8%, std0.499,
  track1.2/feet.2/lin_z-2/ang_xy-.05/action-.01. `REPORT_READ_STATUS=READ_UNMATCHED`:
  이번에 정책 tensor/checkpoint 대응까지 검증하지 않았으며 A017 보고서로 대체하지 않는다.

## 3. 무엇이 실제 문제인가

아래 수치는 A027 고정 내부식의 **역사 proxy**다. scanner ray 평균 지면 높이 한계가 있으므로 실제 낙상률·공식 점수로 승격하지 않는다.
근거: `workspace/_keep/go2_a017_full_suite/evaluation/a017/SELF_EVAL_REPORT.json`의 scenarios.

| 시나리오 | 영상 | 내부 정량 S/T (최저 곱 case) | 역사 감점 /70 | 공식 결과 |
|---|---|---|---:|---|
| G1 | 이번 재판독 안 함 | 1.000/.8944 | 1.11 | 미측정 |
| G2 | 이번 재판독 안 함 | 1.000/.8921 | 1.13 | 미측정 |
| G3 | 이번 재판독 안 함 | .46875/.75736 | 9.03 | 미측정 |
| G4 | 이번 재판독 안 함 | .750/.6810 | 5.14 | 미측정 |
| G5 | A028 기존 관찰 기록상 정체; 실제 하강 VIDEO_UNKNOWN | 0/.1614 | 10.50 | 미측정 |
| G6 | 이번 재판독 안 함 | .90625/.9616 | .90 | 미측정 |
| G7 | 이번 재판독 안 함 | .90625/.7209 | 2.43 | 미측정 |

### 이번에 직접 계산한 G3 실패 전 상태

입력: A027 A017 `cases/seed_{101,202,303}/rough_lateral/steps.csv`.
env별 최초 terminated 이전 25행(0.5초)의 `q=max(0,1-proj_grav_z²)`를 모았다.
단위 중력이라는 upstream 가정하에 q는 orientation 항의 비가중 크기다. 종료 행은 reset 이후 상태일 수 있으므로 제외했다.

| seed | terminated 개체 /32 | base_contact 개체 /32 | 종료 전 q 평균 | 종료 전 q 중앙값 |
|---|---:|---:|---:|---:|
| 101 | 17 | 17 | .68847 | .77125 |
| 202 | 14 | 14 | .62795 | .65738 |
| 303 | 17 | 17 | .66033 | .71715 |

같은 횡이동의 t≥0.5 전체행 q 중앙값은 .01104/.01197/.00936이다. 이것은 정상 개체만의 통계가 아니라 전체 분포이며,
failure-window와 정상 상태의 인과 대조로 쓰지 않는다. 종료 전 상태가 큰 기울기에 집중된다는 **연관성**만 확보했다.
G3 낮은 survival은 종료 이벤트 17/14/17과도 연결되므로 단순 높이 오차만으로 설명되지 않는다.
반대로 **기울기가 최초 원인인지, 접촉/미끄러짐 이후 결과인지 미확정**이다.

G5 stairs_15_down은 seed별 32/32개가 높이<.18m을 25행 지속했지만 기울기 기준(gz>-.5) 25행 지속은 0/32였다.
이는 낮은 높이 판정을 모두 전도로 해석하면 안 된다는 추가 근거다. 실제 하강·접촉·지형 경계 문제는 기존 A028 한계 유지.
G5를 버리는 것이 아니라 **진단 명확도가 더 높은 G3 생존을 첫 학습 표적**, G5를 동시 측정 대상으로 선택한다.

## 4. 다음 단일변수 선택

**계획값: A017 reward 조합에서 `flat_orientation_l2: 0.0 → -1.0`만 변경.**
나머지 track1.4, feet.2, lin_z-2, ang_xy-.05, action-.01 및 배포의 모든 나머지 설정 유지.
로컬 Pilot reward 파일을 baseline으로 오인하지 않는다. 정책 resume가 아니라 동일 조건 from-scratch다.

값 근거는 권장범위 중간이나 기본값 복사가 아니다. 관측된 실패 전 q=.628~.688에서 가중 항은 약 -.63~-.69,
전체행 중앙 q에서는 약 -.01이다. **관측된 큰 기울기에 유의한 선택 압력을 주는 단위 크기 탐색**으로 -1을 고정한다.
20° 기울기에는 약 -.117, 60°에는 -.75가 된다. 이 크기는 사람이 정한 실험 설계이며 통계적으로 추정된 최적 계수가 아니다.
시간 적분·reward 집계가 다른 학습 로그 평균과 직접 비교하지 않는다.

공식 함수: `sum(square(projected_gravity_b[:,:2]))`.
[IsaacLab v2.3.0 rewards.py](https://raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.0/source/isaaclab/isaaclab/envs/mdp/rewards.py).
Go2 rough upstream 부모값은 0.0이며 -1.0을 추천한다는 근거가 아니다.
[velocity_env_cfg.py](https://raw.githubusercontent.com/isaac-sim/IsaacLab/v2.3.0/source/isaaclab_tasks/isaaclab_tasks/manager_based/locomotion/velocity/velocity_env_cfg.py).
서버 배포 버전 동일성은 미확인. 함수 자체에는 정규화/지형 법선 목표가 없다. 180° 뒤집힘에도 q=0이므로 생존 보상의 대체물이 아니다.

| 가설 | 기대 관측 | 반증/경쟁 설명 |
|---|---|---|
| H-A: 과도한 기울기 억제가 G3 접촉 종료를 줄인다 | rough_lateral 종료 개체 감소, 생존·진행 비열등 | q만 줄고 종료·추종 그대로면 목적 불충족 |
| H-B: 기울기는 접촉/미끄러짐의 결과다 | 종료 감소 없음 또는 정체 증가 | action/접촉 정보가 부족하므로 원인 확정 금지 |
| H-C: 지형에 필요한 기울기까지 억제한다 | G4/G5 진행·추종 또는 생존 후퇴 | 후보 폐기, 자동으로 -0.5 등 비율 탐색하지 않음 |
| H-D: 단일 seed/학습성숙도 효과다 | seed43에서 개선 미재현 | exploratory 유지, 장기 승급 금지 |

대안: action 완화는 A018 유효 실패로 제외. track 추가 인상은 G4/G6 회귀 위험으로 후순위.
ang_xy -.06은 정적 기울기와 각속도를 혼동하지 않도록 보류. feet/lin_z는 이번에 동시에 변경하지 않는다.
flat의 A013/A025 비교는 비대칭이라 개선/악화 확정 근거가 없지만 관측 이력 자체는 보존한다.

reward 상태: track **부분 만족**(조합 성능), action 완화 **미만족**(A018 조건에 한정),
현재 action -.01의 최적성 **미측정**, feet/lin_z/ang_xy의 개별 효과 **INCONCLUSIVE**, flat -1의 A017 효과 **미측정**.

## 5. 실험·판정·회수 계획

| 순서 | 등급 | 작업 | 완료 기준 |
|---|---|---|---|
| 1 | 조사 | 이번 로컬 원자료 재분석·후보 결정 | 위 근거/경쟁 가설/계획값 기록 |
| 2 | 개선 | 다음 미사용 ID로 실행 패키지 작성 | 번호 중복 확인, A017 model/env identity 지원, reward 단일 diff, LF/bash -n/CRC/SHA/report 회수 테스트 |
| 3 | 개선 | seed42,4096env,1000iter from-scratch screening | 배포 train/play/task 불변, seed·환경·선별 규칙 동일, 학습 종료 후 원 report 보존 |
| 4 | 개선 | 고정 69case seed101/202/303 평가 | candidate 69case·32env·20초, A027 baseline 조건 동일. 새로운 evaluator면 양쪽 재평가 |
| 5 | 개선 | 승자만 seed43 대조 재현 | baseline와 candidate를 seed43 각각 학습, 동일 평가. 이후 3k/5k 재계획, 자동 연장 없음 |
| 6 | 필수(제출요건) | 최종 평가·문서·3종 제출 준비 | 현재 미완료: ▲ 제출 불가 — 최종 후보 및 문서 감사 즉시 해소 대상. 이 실험 성공만으로 제출 승격하지 않음 |

최소 screening 학습 예산은 1×1000iter, 1차 재현까지 계획 예산은 총3×1000iter(기존 baseline42 재사용).
실제 서버 잔여 예산/TTL은 이번에 새로 확인되지 않았다. 발행 시 원장의 잔여 벽시계와 학습·평가·압축·회수 여유를 대조한다.
평가 rollout만의 하한은 69×20초=23분이며 프로세스 초기화·렌더·포장·다운로드를 제외하므로 실행시간 견적으로 쓰지 않는다.
회수 가능한 종료 시각을 runner에 동결한다. TTL 임박/비유한값/학습 프로세스 실패 시 보존 checkpoint·로그·부분 bundle 회수 후 중단.
500iter는 중간 보존 확인점이지 평균 reward만으로 성능 조기종료하는 기준이 아니다. 1000iter에서 반드시 재평가한다.

### 사전등록 내부 screening 기준 (공식 통과 기준 아님)
- 성공: G3 최저 case 생존이 baseline보다 **≥.10** 개선, G3 최저 곱 점수 증가.
  각 평가 seed의 G3 최저 곱이 baseline 이상이며, 69case 각각 survival 감소≤1/32, tracking 감소≤.02.
  총 역사 proxy 변화≥+1.0/70. G3 진행거리 중앙값은 같은 case/seed 대비 비열등.
- 메커니즘 보강: rough_lateral base-contact 종료 개체 수가 세 seed 각각 baseline(17/14/17)보다 감소.
  q만 감소한 경우는 성공이 아니다. 영상은 동작 확인용이며 통계적 인과 증명이 아니다.
- G4/G5 영상·진행량·추종 회귀는 필수 부작용 판독. G5 하강 라벨로 실제 하강을 주장하지 않는다.
- 실패: 명확한 비열등 한계 초과/평지 붕괴 또는 충분한 자료에서 개선 기준 미달이면 이번 후보를 승자로 채택하지 않는다.
- INCONCLUSIVE: identity/evaluator 불일치, 필수 영상·telemetry 누락, 높이 경계가 개선 판정을 좌우하는 경우.
  데이터 결손을 효과 없음으로 판정하지 않는다. 단일 학습 seed 성공은 exploratory뿐이다.
- 실패 시 A017 보존, -1 후보 장기 승급 금지. INCONCLUSIVE이면 결측만 보완하고 자동 재학습하지 않는다.

이득 **민감도**: G3 tracking .75736 고정·현재 최저 case 불변 가정에서 생존+.10이면 약
`70×.20×.75736×.10=1.06/70`. 이는 달성 확률을 포함한 기대 이득이 아니다.
감사의 .29 역시 RMSE 5% 개선을 가정한 조건부 계산이지 통계적 기대값은 아니다.

### 필수 회수와 서버 종료 게이트
- 학습 원본 report를 평가 이전 `_keep/<새 튜닝명칭>/exported/report.html`로 보존. 학습 로그·env·model·policy·tfevents·identity/manifest와 단일 결과 ZIP/SHA에 포함.
- candidate 69case telemetry/summary/log 전체와 영상 21개: G1 nominal,G2 diagonal_left,G3 rough_lateral,G4 +20°,G5 stairs_10_down·stairs_15_down,G6 push_neg_y 각각 seed101/202/303.
  G7 DR 영상도 각 seed 하나씩 추가하여 **총24개**, 4env·20초, 정책/조건 대응 기록. 정량32env rollout과 영상4env는 개체별 동일 증거가 아님을 표시.
- 영상 판정: 필수 / 생성 결과: 파일 수·재생 확인 / 다운로드 결과: 단일 ZIP+SHA 로컬 도착 / 로컬 검증: 내부 manifest·모델 대응·report 비어있음/이전 run 여부 / 미측정 G1~G7: 누락 case 명시.
- 위 회수 항목 확인 전 서버 종료 가능으로 보고하지 않는다. 실패 시 원인 로그와 재현 artifact 먼저 회수.
- 이번에는 실행 ZIP·명령·완료 표식을 발행하지 않았다. 계획 완료를 패키지 완료로 표현하지 않는다.

## 6. 검증 및 정확한 NEXT

이번 검증: A013/A025/A018 총42개 summary의 schema/source 직접 조회, A018 원 결정,
A027 A017 report·9개 CSV(rough_forward/rough_lateral/stairs_15_down ×3seed), A017 원 로그, Pilot HTML 본문 직접 열람.
코드/배포 reward/기존 review 수정 없음. 새 패키지 테스트·서버 실행·영상 신규 판독 없음.

NEXT: **계획값 flat 0→-1의 새 번호 current 실행 패키지 구현·검증**. A029 -0.008 재발행·과거 HTML 재검색·review ZIP 생성으로 되돌아가지 않는다.
현재 요청의 종료점은 이 근거 있는 튜닝 계획과 원장 동기화다. 실행 패키지 발행 작업과 구분한다.

### 재현: G3 최초 종료 직전 기울기

저장소 루트에서 아래 Python을 실행한다. 표준 라이브러리만 사용하며 읽기 전용이다.

```python
import csv, collections, statistics
from pathlib import Path
for seed in (101, 202, 303):
    path = Path(f"workspace/_keep/go2_a017_full_suite/evaluation/a017/cases/seed_{seed}/rough_lateral/steps.csv")
    history, first, terms, contacts, values = collections.defaultdict(list), set(), set(), set(), []
    with path.open() as stream:
        for row in csv.DictReader(stream):
            env = row["env_id"]
            if row["term_base_contact"] == "1":
                contacts.add(env)
            if row["terminated"] == "1":
                terms.add(env)
                if env not in first:
                    first.add(env)
                    values.extend(max(0, 1-float(r["proj_grav_z"])**2)
                                  for r in history[env][-25:])
            history[env].append(row)
    print(seed, len(terms), len(contacts), statistics.mean(values), statistics.median(values))
```

출력 기대: 101/17/17/.688471/.771251, 202/14/14/.627949/.657381,
303/17/17/.660327/.717148 (표시 자릿수 반올림). 이 통계는 영상 판독이나 인과 검증이 아니다.

### 계획 검토 결과
- 별도 critic 읽기 전용 검토: 중대 수정 요구 없음. 인과/연관 구분, G3 우선 근거, 탐색값 근거, 판정/회수 기준 정합성을 확인했다. 패키지 검증이나 성능 판정은 아니다.
- 문서의 Python 재현 코드를 실제 실행하여 3seed 표 수치를 재현했다. UTF-8 읽기 검사 및 git diff --check 성공. 배포 train/play/task/reward diff 없음.
