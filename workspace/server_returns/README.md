# 서버 결과 격리 구역

이 디렉터리는 휘발성 대회 서버에서 내려받은 원본을 로컬 정본과 분리해 보존하는 곳이다.

## 규칙

1. run별로 `<RUN_ID>/original/`과 `<RUN_ID>/extracted/`를 만든다.
2. 다운로드한 tar는 `original/`에 그대로 보존한다.
3. `workspace/training`에 직접 압축을 풀거나 전체 덮어쓰지 않는다.
4. SHA256·`STATUS.txt`·`TRAIN_RC`·source hash·params·checkpoint·tfevents 검증 후에만 선택 병합한다.
5. 작업 상태와 병합 파일 목록은 루트 `ARTIFACT_MANAGEMENT.md`에 기록한다.

현재 대기 RUN_ID:

```text
train_260831-06_run05cfg_10000
```
