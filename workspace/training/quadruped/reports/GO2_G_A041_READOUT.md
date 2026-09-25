# G-A041 회수 판독 — 2026-09-21

## 결론
- ARTIFACT_VERIFIED: 실행 ZIP이 아니라 실제 결과 ZIP의 외부 SHA·CRC·내부 SHA 187/187, 풀린 파일 188/188 일치. campaign ZIP도 SHA·CRC·내부 SHA 5/5 일치.
- INTERNAL_GATE_FAIL: 로컬 `verify_go2_basic_motion_harvest.py` 재계산, artifact_faults/stage_faults 없음, sentinel 5/5 일치. 학습/러너 RC=0. 후보 승급하지 않고 A033 유지.
- 정보 수확: A033 조건에서 ang_vel_xy_l2 -0.05→-0.04로 재학습한 seed42 정책의 10cm 계단 성능은 악화. 강화가 해로웠으므로 완화는 좋아질 것이라는 방향 예측이 반박됨. 모든 seed/가중치 구간의 일반법칙이나 직접 기전은 확정하지 않는다.
- 회수 완결은 PARTIAL: 사양 `preregistered.required_records`의 15cm 계단 telemetry·등반수·전진거리 없음. target FAIL로 full stage가 실행되지 않아 생긴 사양/실행 경로 불일치다. 다운로드 손상이 아니다. 이 공백을 채웠다고 서버 종료 승인하지 않는다.

## 식별·학습 report
원본: `workspace/_keep/go2_g_a041_a033_ang_vel_xy_m004/`.
REPORT_READ_STATUS=READ_MATCHED (동일 run 학습 보고서; 평가 iter와는 다름).
`exported/report.html` 본문 직접 읽음: 2026-09-21 10:02~10:59, 57분22초, 총1000, reward-best iter700; 최고19.79@681, 최종terrain4.61, base_contact 기반 학습낙상17.4%, std0.585. launcher의 best step681→model700, report 생성경로, TRAIN_STATUS 및 env -0.04와 대응.
평가 고정 iter900 SHA `f4c0b929d6daed1c834da1760638faa2b28aaac605f4aa898369a3e1df63c8e8`; reward-best iter700 SHA `e010cf027ed2fe4f439c4cfcbd4117b8240e3966cba2620b97626123e970d764`. HTML은 iter900 성능 보고서가 아니다.
A033 원본 `workspace/_keep/go2_g_a033_a017_track_lin_vel_xy_150/exported/report.html`도 본문 직접 읽음(최고19.28@651, 마지막terrain4.71, 학습낙상17.1%, std0.613). 이번 검토에서는 A033 HTML 전체 lineage를 새로 재감사하지 않음. 비교 정책은 고정 model SHA와 sentinel로 확인.
reward_only.diff는 ang_vel_xy_l2 한 줄만, 나머지 5개 참가자 항은 유지. 로컬 검증 JSON에 env·checkpoint·evaluator 지문 보존. 학습 로그 terrain@700/800/900/999 = 3.4536/4.2239/4.5214/4.6058; A033 @900=4.4937(기존 TERRAIN_AT_PIN). 평균 유사성은 지형 노출 동일성 증거가 아니다.

## 예측과 실측
모집단: 학습 seed42 한 정책씩, 평가 seed101/202/303 각32대. 아래 proxy는 표적 case 평균이며 G1~G7 전체 점수가 아니다.

| 항목 | A033 | A041 | 판독 |
|---|---:|---:|---|
| 10cm 오르기 ≥1단 | 90/96 | 34/96 | 개선 예측 반박 |
| 10cm 오르기 ≥2단 | 43/96 | 8/96 | 개선 예측 반박 |
| 10cm 자세 포함 낙상 | 34/96 | 93/96 | 악화 |
| 10cm 전진거리 seed101/202/303 (m) | 2.126/2.217/2.215 | 1.704/1.558/1.516 | 셋 모두 감소 |
| 험지 옆걸음 자세 포함 낙상 | 59/96 | 52/96 | 감소 관측; 직접 흔들림 속도 개선과 동의어 아님 |
| 험지 전진 자세 포함 낙상 | 4/96 | 8/96 | 증가 관측 |
| 앞 밀침 표적 평균 proxy 변화 | 기준 | -0.018081 | seed별 +,-,+; 일관 악화 아님 |

험지 전진+옆걸음 묶음 평균 Δ=-0.002129. 묶음 평균만 보고 서로 반대인 두 행동을 지우지 않는다. 평지 전진 한 case proxy 0.949372→0.959960은 보행 전반 개선의 증거가 아니다.
부분 보상 margin 증가와 실제 행동 개선은 다른 명제다. 보상 수식은 고정 궤적의 비용 변화를 말하며 재학습 후 궤적을 보장하지 않는다. A038 강화와 A041 완화 모두 계단이 나빠졌다는 조건부 관측이지 -0.05의 전역 최적성 증명이 아니다.

## 원시 채널·영상·미측정
- `evidence/go2_a041_20260921/FALL_CHANNEL_PER_ENV.csv`, `FALL_CHANNEL_ROLLUP.csv`: 기존 `go2_a038_reread.fall_channel_attribution`/`channel_rollup`을 A041 경로에 재사용(출력 arm은 A041로 명시). 0.5초 grace/hold, 높이0.18m·proj_grav_z -0.5 기준. A041 10cm height-only=30/32/29, both=0/0/2, tilt-only=0/0/0. **이 분해는 base_contact를 합친 summary 낙상수와 다른 모집단/정의**다. 낮은 높이 채널이 주로 발화했음을 말하며 원인으로 확정하지 않는다. tilt 채널이 없으면 reward 영향이 없다는 사양 문구는 부당한 인과 배제다.
- `STAIRS_PROGRESS.json`: 마지막200step 속도는 각 seed6400행 전체(종료 후 포함), 생존 로봇만의 평균 아님. A033 .11354/.09255/.09486 → A041 .02045/.03922/.04113 m/s.
- 후보4·기준선2 영상, 각499frame/50fps, 파일마다4지점 디코드 확인(`VIDEO_DECODE.json`). 계단 비교 contact sheet 직접 관찰: 후보가 첫 계단 부근 낮은 자세에 머무르는 표본을 확인. 전 영상 연속 재생·모든 로봇 관찰은 미완료이므로 시나리오 VIDEO_UNKNOWN 유지.
- G1 일부/G3 두 case/G5 10cm 오르기/G6 앞 밀침은 내부 정량 확보. G2·G4·G7 후보 정량, G5 15cm 및 나머지 전수69case 미측정. 후보 경사 영상 존재가 G4 정량을 대신하지 않는다. 모든 공식 결과 미측정. 총 /70 산출하지 않는다.

## PM 결정·후속
성능 개선 실험으로는 INTERNAL_GATE_FAIL, 보상→행동 예측 반증 자료로는 유효한 수확이다. A033 유지, A041 장기 승급/제출 후보화하지 않는다. 새 가중치는 이번 검토에서 선택하지 않는다.
기록 필수 항목은 승급 성공 여부와 독립적으로 수집하도록 다음 패키지의 종료 분기를 수정해야 한다. 기존 실행 release·회수 ZIP은 불변 보존한다. 15cm 효과는 미측정이며 같은 checkpoint를 이용한 별도 평가로만 보완 가능(재학습은 필요 없음).

## 재현
`python -B tools/verify_go2_basic_motion_harvest.py G-A041 --harvest workspace/_keep/go2_g_a041_a033_ang_vel_xy_m004 --out workspace/training/quadruped/reports/GO2_G_A041_LOCAL_VERIFY.json`
실행 exit1은 INTERNAL_GATE_FAIL을 뜻하며 검증기 고장이 아니다. tar 전용 `verify_download_artifact.py`는 ZIP을 거부해 zipfile SHA/CRC/manifest 대체 검사 사용. 새로운 training 정본 병합/덮어쓰기 없음.
