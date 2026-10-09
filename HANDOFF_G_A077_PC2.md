<!-- PC2_HANDOFF
WORK_ID: G-A077
STATUS: READY
START_AFTER: G-A074-EVAL
START_MARKER: /workspace/_keep/go2_g_a074_report_policy/RUNNER_STATUS.txt
PACKAGE: workspace/training/quadruped/upload/G-A077/current/GO2_G_A077_FLAT_ORIENTATION_M0P225_v1.zip
PACKAGE_SHA256: c8e8d4f5ab3a5362a5d0a91179009f0be3230dcdb4b460a3a92ef44dc681f87f
-->

# G-A077 — 검증된 G-A074에서 flat 한 항 탐색

## 0. 한눈에

- 목적: G5 15cm 등반 proxy 개선과 기존 안정성·추종 보존을 함께 시험한다. 성공·최적값 예측이 아니다.
- 설계: G-A074 보상 설정에서 flat_orientation_l2 -0.25→-0.225만 변경. from-scratch 3000 iter, seed42, 4096env, 평가2400.
- 시작: G-A074-EVAL RUNNER_RC=0/FULL_69_COMPLETE, 선행 프로세스 없음, 패키지 검증 완료.
- 점 목록: flat_orientation_l2_m0p225 하나. 완료한 G-A074나 원래 -.20 학습을 반복하지 않는다.
- 예상: 직전 실측 학습4시간36분+평가약1시간24분; 새 실행의 완료시간 보장 아님.
- 판정: 계획 `workspace/training/quadruped/upload/plan/GO2_G_A077_PLAN_20261010.md`. 방향 가설 지지와 후보 채택을 분리한다.

## 1. 준비 확인

1. current 폴더의 `.zip.001`부터 번호 순서로 연결해 `/workspace/GO2_G_A077_FLAT_ORIENTATION_M0P225_v1.zip`을 복원한다. 원본 ZIP는 git에 추가하지 않는다.
2. sidecar의 SHA와 복원 ZIP의 `sha256sum`이 같을 때만 `/workspace`에 해제한다. 실행 ZIP는 이 PC의 `/workspace`에 보존한다.
3. 선행 marker와 PC2 원장 DONE을 확인하고 실제 train.py/play.py 프로세스가 없을 때만 실행한다. 기존 프로세스를 종료하지 않는다.
4. 대조 정책은 실제 G-A074 model SHA `d39b88e9a6b06fd08498c90bbba334a3aaaca1cc8e540102c7d0e284bac72211`, env SHA `992cdec9a322d7e8a5cfff8048d803116ce010ba4d0d4820cf95b49db9987005`다. A033이 아니다. 패키지의 69case와 10영상은 재사용하며 대조 정책을 재학습·재평가하지 않는다.
5. 기존 PC2 IsaacLab/venv/GPU, 최소 여유20GB를 확인한다. 외부 휘발 서버를 새로 켜지 않는다. USD 접근 실패면 학습 전 종료하며 자동 재시도하지 않는다.

## 2. 실행

Git Bash에서 실행 ZIP를 `/workspace/`로 복사·해제한 뒤 실행 한 줄:

```bash
PYTHONUTF8=1 PYTHONIOENCODING=utf-8 PATH=/workspace/isaaclab_venv/Scripts:$PATH bash /workspace/go2_g_a077_flat_orientation_m0p225/run_all.sh
```

기존 `run_point.sh`/runner를 사용한다. GPU는 `nvidia-smi`와 로그로 확인한다. 학습·평가를 중복 실행하지 않는다.
30분마다 `tools/watch_go2_pc2_progress.ps1 -Publish`가 실제 iter/3000, 완료case/69, 영상/10을 원장에 기록하고 commit/push한다. 이 작업은 Codex 호출·사용량에 의존하지 않으며 채팅 자동 발송 기능은 아니다.

## 3. 실패 처리

- rc20/21/22: 디스크·중복 프로세스·Isaac/GPU 차단. 기록 보존, 진행 중 프로세스 중단 금지.
- rc23/25: USD·identity·패키지 사전 검사 실패. 학습 시작 여부를 로그로 확인하고 자동 재학습 금지.
- rc30/31/32/33/34: 원 로그·부분 결과·checkpoint 보존. 완료한 학습을 새 번호로 다시 실행하는 우회 금지.
- runner의 legacy gate는 `NON_AUTHORITATIVE_EXECUTION_SAFETY_ONLY`다. 새 사전등록 비교 판정은 작성 담당이 실제 G-A074와 수행한다.

## 4. 회수

- `/workspace/_keep/go2_g_a077_flat_orientation_m0p225/`
- `/workspace/_keep/GO2_G_A077_FLAT_ORIENTATION_M0P225_RESULT.zip`와 `.sha256`
- 원 report.html, model/env/source/log/tfevents, candidate69case·10영상, 고정 G-A074 대조 증거, 상태/manifest를 검사한다.
- 100MB 초과 ZIP는 95MiB parts로 등재하며 SHA/CRC/manifest 검증 후 결과와 원장을 commit/push한다. 새 결과를 과거 run에 덮어쓰지 않는다.
- 영상·telemetry·bundle·SHA의 로컬 검증 전 서버 종료 가능 판정 금지. 로컬 PC2 실행은 휘발 서버 종료와 구분한다.

## 5. 보고와 후속

PC2는 시작/종료/rc/SHA/진행률만 보고하며 보상값을 새로 고르지 않는다. 결과 회수·푸시 뒤 작성 담당은 판독과 상태 원장 갱신을 수행한다. G-A077 결과가 보호 기준을 잃거나 불명확하면 G-A074를 보존하며 임의 중간값·추가 강화 학습을 자동 발행하지 않는다. 다음 선택은 결과별 사전등록 분기와 기존 사용자 지시에 따른다.
