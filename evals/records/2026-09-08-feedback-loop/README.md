# 자율 피드백 루프 기록

사용자 목표: “밤새 스스로 피드백 루프 돌명서 스스로 개선하고 발전해봐”.

2026-09-08 23시대 KST에 변경 없는 `76e4aee`에서 시작했다. 작업 브랜치는
`work/overnight-feedback-2026-09-08`이다. 현재 목표는 진행 중이며, 이 기록은
저장소에서 확인한 실패와 수정 결과를 다음 사이클로 이어가기 위한 기록이다.

아래는 첫 사이클(`fb256bc`)의 기록이다. 다음 사이클의 수정·최종 검증·
네이티브 정적 진단 자료는 [두 번째 사이클](cycle-2.md)에 별도로 기록한다.
문구·밀도 시험에서 발견한 포커스 증거 문제와 수정은 [세 번째 사이클](cycle-3.md)에 기록한다.
수집 중단 보고와 압축 검증은 [네 번째 사이클](cycle-4.md)에 기록한다. 첫 두
압축의 전체 파일 집합에 대한 새 검증 결과와 이전 검증의 한계도 그곳에 명시했다.

## 확인한 문제와 수정

| 문제 | 수정 전 실제 관찰 | 수정과 검증 |
| --- | --- | --- |
| macOS 기본 Python에서 npm 검증 중단 | Python 3.9.6의 framework 빌드가 `venv --copies`를 거부해 npm 8개 중 1개 실패 | venv의 플랫폼 기본 방식을 사용. 공백 경로의 실제 Python 실행·CLI 전달을 유지하며 npm 8개 통과 |
| 정확한 시간 예산을 초과로 판정 | `100.01`초 6회를 `600.0600000000001`로 더해 `600.06`초 예산에서 `incomplete`; 작은 실제 초과가 합계에서 사라지는 반대 문제도 재현 | 해석된 숫자의 십진 표현을 정확히 합산·비교. gate 45개와 실제 CLI lifecycle 50개 통과 |
| 브라우저 수집 중단 시 이전 관찰 유실 | 저장 후 reload 실패로 결과 JSON 없이 이미지 하나만 남음 | 완료 관찰을 보존하고 나머지 필수 검사를 `not-run` 처리. Chrome 21개 통과; 재현 결과 5 pass / 1 fail / 10 not-run |
| 잘못된 호스트 기록이 비교 집계 전체 중단 | host coverage의 `null`에 AttributeError, CLI traceback/exit 1 | 타입 오류를 기록하고 집계 지속. 관련 23개 통과; 불완전 JSON/exit 3 및 별도 후보 실패 보존 확인 |
| 반복 실행에서 이전 이미지 혼합 | Chrome이 없는 재실행이 새 미실행 JSON 옆에 이전 스크린샷을 남김 | 기존 브라우저 산출물과 원자적 시작 표식으로 재사용 거부. 기존 내용·mtime, 동시 예약, 중단과 prepared scope 경로 검증 |

기본 상태에서 Python 240개 중 28개 브라우저 전용 검사를 건너뛰고 나머지가 통과했다.
그 뒤 별도로 기존 Chrome 검색 편집기 18개와 범위 검사 10개가 모두 통과했다.
위 표의 변경 후 결과는 각 수정에 대한 검증이며 최종 전체 검증과 구분한다.

## 제품 동작 시험

현재 스킬 지침의 동작도 별도 새 문맥 `/root/flow_trial`에서 시험했다.
`snapshot-direct` 방식이며, 원본 search-editor 과업에 저장 대기 중 추가 입력과
다른 메모 선택의 연속성을 명시했다. 수정 허용 경계는 원래 네 제품 파일이다.
스킬과 평가 도구는 제품 작성자의 수정 경계 밖에 두었다.

독립 Chrome 관찰의 원본 결과는 저장 대기 중 다른 메모로 이동한 뒤 실패할 때
현재 메모의 새 제목·본문을 잃었다. 대기 중 추가 입력이 저장소에 아직 없는데도
저장 성공 문구가 표시됐고, 다른 메모의 완료 결과가 현재 메모의 피드백을 덮었다.
작성 완료 후 부모의 별도 실행에서 추가 시나리오의 데이터/조작 단언 18개와
기존 suite의 행동 검사 16개가 모두 통과했다. 문구·화면은 실제 이미지 6개를
열어 별도로 검토했다. [검토 결과](flow-review.md), [제품 변경](flow-product.patch),
[고정 파일 목록과 해시](flow-inventory.json), [원본 압축](flow-trial.tar.gz)을 보존한다.
제품 작성자 자체 검사는 원문 보고와 자료를 압축에 별도로 담았다.

이 제품 시험은 단일 스킬 실행이며 버전 간 비교·반복·전이 시험은 아니다.
코드·판정기 수정의 회귀 통과를 일반적인 스킬 품질 향상으로 세지 않는다.

## 최종 검증

- `python3 -B -m unittest discover -s tests -q`: 255개 중 브라우저 전용 36개를 건너뛰고 나머지 219개 통과.
- `AI_SLOP_BROWSER_TESTS=1 python3 -m unittest discover -s tests -p test_browser_checks.py -v`: 24개 통과.
- `AI_SLOP_BROWSER_TESTS=1 python3 -m unittest discover -s tests -p test_scope_browser_checks.py -v`: 12개 통과.
- `npm test`: 기본 Python 3.9.6에서 8개 통과. `AI_SLOP_PYTHON=/opt/homebrew/bin/python3.12 npm test`도 8개 통과.
- `npm run check`, `npm run check:js`: 배포 해시·75개 배포 파일, 7개 스킬·24개 정적 사례 계약, 링크·의존성과 구문 검사 통과.
- 이 디렉터리의 `shasum -a 256 -c SHA256SUMS`: 압축 해시 통과. 새 임시 디렉터리에 해제한 77개 고정 파일이 `flow-inventory.json`의 해시와 모두 일치했다.
- 압축을 해제한 새 경로에서도 추가 관찰기를 실행해 원본 16 pass / 2 fail, 결과 제품 18 pass / 0 fail을 재현했다. 양쪽 수집 오류는 0개였다.
- 별도 새 문맥 `/root/final_review`의 읽기 전용 코드 검토에서 추가 수정이 필요한 정확성·호환성 결함은 발견되지 않았다. 이 검토는 테스트 재실행을 포함하지 않는다.

압축에는 원본/결과 제품, 스킬 snapshot, 부모 추가 관찰기와 브라우저 자료,
작성자의 최종 보고와 자체 검사 자료가 있다. 부모의 추가 관찰은 압축을 새
디렉터리에 푼 뒤 다음처럼 재현할 수 있다(기존 Chrome과 Node 22+ 필요).

```sh
node check-interruption.mjs original-product /tmp/new-original-evidence
node check-interruption.mjs product /tmp/new-result-evidence
```

첫 명령은 의도된 원본 결함 때문에 종료 코드 1, 두 번째는 0을 반환했다.
정식 `search-editor-v3` 검사는 소스 체크아웃의 `scripts/run_browser_checks.mjs`로
압축 안의 `product`를 지정해 재현한다. 압축은 npm/설치 payload에 포함되지 않는다.

## 다음 사이클

이번 사이클은 재현한 다섯 결함의 수정과 검증, 한 제품 과업의 독립 재검증을
완료했다. 밤샘 목표는 계속 활성 상태다. 다음에는 다른 실제 과업에서 현재
지침의 실패를 찾고, 발견한 원인이 제품 구현인지 지침 누락인지 구분한다.
지침 보강이 필요하면 같은 조건의 비교와 다른 사례의 보존 근거부터 마련한다.

실행 환경: macOS, Python 3.9.6, Node 26.8.1/npm 11.19.0,
Chrome 152.0.7977.76. 별도 Windows/Linux 실행 및 원격 CI는 이 기록에 포함하지 않는다.
`skill-creator`의 실제 실패 중심 수정과 행동 검증 지침을 적용했다.
공식 `quick_validate.py`는 PyYAML 부재로 실행하지 못했으며, 기존 저장소의
스킬 메타데이터·참조·구문 검사와 실제 스크립트 검증으로 보완한다.
