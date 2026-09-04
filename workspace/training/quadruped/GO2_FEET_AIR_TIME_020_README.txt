Go2 feet_air_time=0.20 단일변수 1,000-iter screening — 사용자 실행 지침
============================================================================

목적
- 검증된 Default-01 reward에서 feet_air_time만 0.01→0.20으로 변경합니다.
- seed 42, 4096 env, 1000 iter로 from-scratch 학습합니다.
- candidate를 G1~G7 69 telemetry로 평가하고 worst-case 영상 7개를 생성합니다.
- 검증된 Default-01 report와 사전등록 기준으로 비교 보고서를 만듭니다.
- 모든 결과를 다운로드 1회용 ZIP 하나로 자동 묶습니다.

1) 업로드할 로컬 파일
   C:\dev\Nconnect\workspace\training\quadruped\go2_feet_air_time_020_v1.zip

2) 서버 업로드 위치
   /workspace/go2_feet_air_time_020_v1.zip

3) 서버에서 복사·실행할 한 줄
   cd /workspace && unzip -oq go2_feet_air_time_020_v1.zip && cd /workspace/go2_feet_air_time_020_v1 && bash server_run_go2_feet_air_time_020_v1.sh

4) 진행 확인
   tmux attach -t go2_feet_air_time_020_v1

   예상 실행 창: 약 1시간 35분~2시간.
   근거: 이전 같은 서버에서 1k 학습 약 65분 + 정책 1개의 69-case 평가 약 22분
         + 영상 7개 약 4분 + 시작/패키징 여유.
   전체 서버 생성~종료 과금 시간을 보장하지 않습니다.

   같은 서버에서 PARTIAL 이후 이어서 실행할 때만:
   cd /workspace/go2_feet_air_time_020_v1 && GO2_RESUME=1 bash server_run_go2_feet_air_time_020_v1.sh

5) 완료 표식
   [DONE] GO2_FEET_AIR_TIME_020_RESULT_READY

6) 다운로드할 필수 파일 — 결과는 이 ZIP 하나에 모두 포함
   /workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip

   전송 SHA companion(반드시 함께 다운로드)
   /workspace/_keep/GO2_FEET_AIR_TIME_020_RESULT.zip.sha256

7) 서버 종료 조건
- 결과 ZIP과 SHA companion을 로컬 workspace\_keep에 다운로드합니다.
- 로컬 SHA가 companion과 일치해야 합니다.
- ZIP 안 RUNNER_STATUS.txt가 RUNNER_RC=0이어야 합니다.
- candidate telemetry 69개, 영상 7개, policy.pt, POLICY_LINEAGE.json이 있어야 합니다.
- 이 확인 전에는 서버를 종료하지 않습니다.

주의
- 단일 GPU 학습/play 프로세스만 실행합니다. 4096 env는 Isaac Lab 내부 병렬 환경 수입니다.
- 내부 proxy는 공식 점수가 아닙니다.
- 영상은 VIDEO_UNKNOWN으로 회수되며 사람이 확인해야 VIDEO_OBSERVED가 됩니다.
- PARTIAL ZIP은 평가 완료가 아니라 실패 로그와 복구 artifact입니다.
