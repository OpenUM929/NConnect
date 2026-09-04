Go2 Default-01 vs Pilot-01 — 사용자 실행 지침
================================================

목적
- Default reward, seed 42, 4096 env, 1000 iter를 from-scratch로 학습합니다.
- Default-01과 Pilot-01을 동일한 G1~G7 evaluator로 각각 69 telemetry 평가합니다.
- 정책별 최악 case 영상 7개와 비교 보고서를 생성합니다.
- 모든 결과를 다운로드 1회용 ZIP 하나로 자동 묶습니다.

1) 업로드할 로컬 파일
   workspace/training/quadruped/go2_default_vs_pilot_v1.zip

2) 서버 업로드 위치
   /workspace/go2_default_vs_pilot_v1.zip

3) 서버에서 복사·실행할 한 줄
   cd /workspace && unzip -oq go2_default_vs_pilot_v1.zip && cd /workspace/go2_default_vs_pilot_v1 && bash server_run_go2_default_vs_pilot_v1.sh

4) 진행 확인
   tmux attach -t go2_default_vs_pilot_v1

   예상시간(사전 추정): 약 1.5~3시간.
   이유: 1,000-iter 학습 1회 + 고정 정책 평가 138 case + worst-case 영상 14개.
   서버 GPU/Isaac Sim 시작 시간에 따라 달라지며 첫 실행 전 실측값은 아닙니다.

   같은 서버에서 PARTIAL 이후 이어서 실행할 때만:
   cd /workspace/go2_default_vs_pilot_v1 && GO2_RESUME=1 bash server_run_go2_default_vs_pilot_v1.sh

5) 완료 표식
   [DONE] GO2_DEFAULT_VS_PILOT_RESULT_READY

6) 다운로드할 필수 파일 — 결과는 이 ZIP 하나에 모두 포함
   /workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip

   전송 SHA companion(가능하면 함께 다운로드, 결과 ZIP과 별도 산출)
   /workspace/_keep/GO2_DEFAULT_VS_PILOT_RESULT.zip.sha256

7) 서버 종료 조건
- 위 결과 ZIP을 로컬에 다운로드한 뒤 화면에 출력된 SHA 또는 companion과 일치해야 합니다.
- ZIP 안 RUNNER_STATUS.txt가 RUNNER_RC=0이어야 합니다.
- 정책별 telemetry 69개, 영상 7개, POLICY_LINEAGE.json이 있어야 합니다.
- 이 확인 전에는 서버 종료 가능 판정을 내리지 않습니다.

주의
- 내부 proxy는 공식 점수가 아닙니다.
- 영상은 자동 생성되지만 VIDEO_UNKNOWN 상태로 회수됩니다. 사람이 확인해야 VIDEO_OBSERVED가 됩니다.
- PARTIAL ZIP이 생겨도 평가 완료가 아닙니다. 실패 로그와 복구용 artifact 회수본입니다.
