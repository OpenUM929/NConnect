# G-A028 P1 실행 범위 동결 — 2026-09-13

기존 A027 후속 계획의 P1을 구현한다. P2 가중치 변경/학습은 포함하지 않는다.

- 등급: 조사. 단계0의 report 대응 공백을 유지하면서 허용된 기존 정책 진단을 수행한다.
- 기준: G-A027 current ZIP SHA `e7749d0f6adc4abb2b32fca9393523b8059b8954cec068ba2c7c2930af0a7d15`.
- 모델·env·play·task·telemetry·지형 명령은 동결 release에서 그대로 재사용한다. 학습 경로 변경 없음.
- 2정책(A017/Pilot) × G5 10cm/15cm 하강·G4 +20도 × seed101/202/303 =18회.
- 각4env·1000step, 영상 약20초와 동일 replay의 steps.csv·summary·로그를 함께 회수한다.
- 기존 A027 32env 정량138건은 재실행하지 않는다. 기존 영상은 이18조건의 동시 telemetry를 보장하지 않아 새로운 관측에 사용하지 않는다.
- 자료 성공: 모든18건의 영상·4000행 telemetry·종료0·자세 계측 계약 확인. 이는 내부 성능 성공이 아니다.
- 실패: 프로세스/파일/계측 결함이면 즉시 중단, 현재 영상·로그·보존 model/env를 PARTIAL ZIP으로 회수한다.
- 후속 판독: 하강 전 정지/주저앉음/전도·진행과 자세의 시간 대응을 관찰한다. 판독 불가 VIDEO_UNKNOWN.
- wx/wy·발접촉 채널 없음: 몸통 회전 인과나 특정 reward를 이 데이터만으로 확정하지 않는다.
- 전용 G1/G2/G3/G6/G7 및 G4 반대 경사는 측정하지 않으며 /70 점수를 산출하지 않는다.
- 신규 학습 HTML은 NOT_APPLICABLE. A017 과거 HTML MISSING/Pilot READ_UNMATCHED는 보존한다. 새 학습 회수에는 별도 공용 runner의 report 필수 게이트를 적용한다.
- 예상15~30분은 계획 추정이며 서버 미실측. 첫 case 비용을 확인하고 회수 여유가 부족하면 Ctrl-C 후 PARTIAL ZIP 회수.
- 서버 초기화 전 결과ZIP·SHA를 로컬로 회수한다. 18영상·18summary·18steps.csv·로그·model/env의 로컬 검증 전 종료 가능 판정 금지.
- 결과가 가설을 지지해도 학습 report 대응·독립 검토·단일변수 계약이 닫히기 전 P2 자동 착수 없음.
- 배포: `upload/G-A028/current/`의 ZIP·SHA·RUN_GUIDE·CURRENT_UPLOAD·UPLOAD_MANIFEST.
- 원시 회수: `workspace/server_returns/G-A028/` 격리. 승인 release/history는 불변 보존.
