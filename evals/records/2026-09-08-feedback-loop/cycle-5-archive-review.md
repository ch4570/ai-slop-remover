# Cycle 5 최종 아카이브 독립 검토

검토자: `/root/cycle5_archive_review`, 2026-09-09 KST. 저장소·아카이브·추출 파일을 수정하지 않고 새 임시 경로에서 검증했다. 검토한 범위에서 불일치를 발견하지 못했다.

저장소의 `evals/records/2026-09-08-feedback-loop/cycle-5.tar.gz` SHA-256은 `63d89f459a7323dfca7e06eed812781692b6775e0af5663a8368ba3f56500c96`이며, 압축 파일 크기는 13,510,662바이트다. 외부 `cycle-5-inventory.json`의 SHA-256은 `694c5d4b16b5530225c88849a44945ef33754d49368ac5953a8e325db7563c91`이다.

저장소 루트에서 다음 명령을 독립 실행해 exit 0 / `verified`를 확인했다. 인수 순서는 inventory, archive다.

```sh
python3 -B scripts/check_evidence_archive.py evals/records/2026-09-08-feedback-loop/cycle-5-inventory.json evals/records/2026-09-08-feedback-loop/cycle-5.tar.gz
```

schema 1의 정확한 1,077개 일반 파일, 비압축 파일 합계 21,722,377바이트가 일치했다. 검증 후 새 `/tmp/lutriva-cycle5-final-review-dbqsjg/extracted`에 추출했다. 별도 감사 스크립트로 전체 파일 집합·크기·SHA-256을 실행 전후 각각 inventory와 비교해 모두 일치함을 확인했다. `final-tools/`의 57개 파일도 모두 현재 저장소의 대응 파일과 같다. 전후 감사 결과는 시각 필드를 제외하고 동일하며 아카이브·inventory·Chrome 실행 파일 해시도 유지됐다.

추출 루트에서 `node parent-observations/verify-scope.mjs trial parent-observations/frozen-inputs.json /Users/rex/Desktop/personal/lutriva`도 exit 0이었다. 고정 입력 71개, 스킬 65개와 harness의 Git `6514ff3` 바이트 일치, 허용된 제품 네 파일 및 선언된 소스 보존 범위를 확인했다.

## 추출한 도구의 실제 재실행

추출한 `final-tools/`에서 다음을 실행했다.

```sh
node --test tests/browser-input.test.mjs tests/browser-startup.test.mjs
PYTHONPATH=tests AI_SLOP_BROWSER_TESTS=1 AI_SLOP_BROWSER_EVIDENCE=/tmp/lutriva-cycle5-final-review-dbqsjg/actual-chrome python3 -B -m unittest test_browser_checks.BrowserCheckTests.test_bounded_keyboard_helper_uses_trusted_browser_defaults -v
```

Node 검사는 12/12 통과·실패/건너뜀 0, 실제 Chrome 검사는 1/1 통과였다. 환경은 Node v26.8.1, Python 3.9.6, Chrome/152.0.7977.83이었다. Chrome 원시 JSON에서 Tab/Shift+Tab 포커스 순서, trusted Enter 제출, trusted Space 체크 변경, 18개 trusted 키 이벤트와 Escape 쌍을 확인했다. 페이지 target 전후 목록은 같고 예상하지 않은 target/navigation 기록은 없었다. 테스트 내부 runtime exception 단언도 통과했다. 브라우저 프로토콜 버전은 이 검사 시작 시 기록되었으며 별도 실행 파일 버전/해시는 전체 검사 전후 동일했다.

추출한 `startup-diagnosis/replay-before/`와 `replay-after/` 각각에서 `node --test tests/browser-startup.test.mjs`도 실행했다. 같은 재구성된 세 검사에서 수정 전은 예상대로 1 통과·2 실패(exit 1), 수정 후는 3/3 통과(exit 0)였다. 실패는 불완전 endpoint를 즉시 WebSocket 생성에 사용한 경로다. 이 startup 검사는 가짜 process/socket을 사용하는 소스 회귀 검사이며, 세 검사 파일은 원래 실행 당시 별도로 보존된 원본이 아닌 명시된 재구성본이다.

## 원시 기록과 한계

이번 검토의 임시 원시 기록은 `/tmp/lutriva-cycle5-final-review-dbqsjg/`에 있다: `archive-verification.log`, `extraction-verification.log`, `audit-extracted.mjs`, `extraction-before.json`, `extraction-after.json`, `extracted-scope.log`, `node-targeted.log`, `actual-chrome.log`, `startup-replay-before.log`, `startup-replay-after.log`. 실제 브라우저 JSON은 `actual-chrome/run-g77hm3t6/bounded-keyboard/keyboard-control.json`이다. 이 최종 검토 보고서와 원시 기록은 검토 대상 tar 밖에 생성했다.

파일 무결성 검증은 관찰의 진실성이나 인간 독립 검토를 인증하지 않는다. 이번 최종 추출 단계에서는 지정한 도구 검사만 수행했으며 전체 Python/npm, CI, 필터 제품 42개 비교를 다시 실행하지 않았다. 앞선 staging 제품 재실행 28/42→42/42 및 반례 41/42의 보고서·원시 결과는 이번에 검증한 아카이브에 포함되어 있다. 실제 Chrome 검사는 headless 프로토콜 입력으로 제한되며 물리 장치·OS IME·네이티브 select 메뉴·스크린리더·다른 브라우저·네트워크/업데이트 격리까지 검증하지 않는다.
