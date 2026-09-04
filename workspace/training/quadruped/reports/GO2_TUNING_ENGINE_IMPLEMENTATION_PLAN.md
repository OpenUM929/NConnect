# Go2 고정 튜닝 엔진 구현 계획 — G-A010

## 목표

G-A009에서 실험마다 복제하던 runner·builder·reporter를 `go2_tuning_engine_v1.zip` 한 벌로
고정하고, G-A010부터는 검증된 `experiment.json`만 교체한다. 서버 작업은 engine ZIP과 JSON
업로드, 한 줄 실행, 자동 생성된 결과 ZIP 다운로드로 제한한다.

## 보존할 동작

1. Default-01 iter 800의 고정 baseline model/env 및 repaired-v2 G1~G6 telemetry를 사용한다.
2. candidate 7 case + baseline repaired-G7 1 case의 tier-1 평가를 먼저 수행한다.
3. G1 proxy 개선 `+0.05`, 전체 점수 비회귀, scenario survival 회귀 `0.10` 이하를 모두 만족할
   때만 seed 202·303의 14 case를 추가한다.
4. G1 forward-fast seed 101 영상 1개는 항상 생성한다.
5. 성공·실패 모두 checkpoint·source·experiment 원문/SHA·engine 식별자·telemetry·영상·lineage를
   단일 결과 ZIP과 `.sha256`으로 자동 묶는다.

## 구현 순서

1. 계약 테스트로 schema, 단일변수 제한, reward 렌더링, tier 판정, engine/spec 분리, 결과 계약을 잠근다.
2. JSON validator/materializer와 generic tier reporter를 구현한다.
3. generic server runner와 deterministic engine builder를 구현한다.
4. G-A010 JSON·PRD를 작성하고 ZIP/JSON SHA, CRC, manifest, Python compile, `bash -n`, CRLF를 검증한다.
5. 네 원장에 package 경로·SHA·한 줄 명령·결과 ZIP·서버 종료 게이트를 동기화한다.

## 중단 조건

- JSON이 Default-01 기준에서 정확히 한 reward만 바꾸지 않으면 실행 금지.
- engine version, baseline model/env SHA, canonical 7 case, 영상 계약이 다르면 실행 금지.
- 로컬 검증 중 하나라도 실패하면 서버 지침을 발행하지 않는다.

