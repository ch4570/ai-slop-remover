# 실제 범위 평가 기록 · 2026-09-07

네 사례를 baseline/candidate 각각 두 번 실행한 **16개 독립 Codex native context와 8개 비교 쌍**의 기록이다. 최종 집계 판정은 **`pass`**이며 관찰된 개별 검사 변화는 회귀 0개, 개선 0개다. 두 번의 결과로 일반적인 스킬 우월성이나 인과 효과를 주장하지 않는다.

[사례별 집계](summary.json) · [16개 실행 색인](runs.json) · [원본 압축](evidence.tar.gz) · [압축 내 파일 inventory](archive-inventory.json) · [재현 검증](replay-verification.json) · [기록 파일 해시](SHA256SUMS) · [합성 대조군 요약](controls-summary.json)

## 사례와 반복별 결과

각 실행의 분모에는 사례가 요구하는 source·브라우저·독립 품질 검사가 모두 포함된다. diff가 비어 있는 `audit-read-only`의 통과 근거는 제품 내용·종류·모드의 최종 inventory 일치와 진단 검수다.

| 사례 | 반복 | baseline | candidate | 비교 판정 | 개별 검사 변화 |
| --- | --- | --- | --- | --- | --- |
| `narrow-spacing` | 1 | pass 3/3 ([t01](patches/t01.patch)) | pass 3/3 ([t02](patches/t02.patch)) | `pass` | 회귀 0 / 개선 0 |
| `narrow-spacing` | 2 | pass 3/3 ([t04](patches/t04.patch)) | pass 3/3 ([t03](patches/t03.patch)) | `pass` | 회귀 0 / 개선 0 |
| `audit-read-only` | 1 | pass 3/3 ([t05](patches/t05.patch)) | pass 3/3 ([t06](patches/t06.patch)) | `pass` | 회귀 0 / 개선 0 |
| `audit-read-only` | 2 | pass 3/3 ([t08](patches/t08.patch)) | pass 3/3 ([t07](patches/t07.patch)) | `pass` | 회귀 0 / 개선 0 |
| `empty-state-copy-only` | 1 | pass 3/3 ([t09](patches/t09.patch)) | pass 3/3 ([t10](patches/t10.patch)) | `pass` | 회귀 0 / 개선 0 |
| `empty-state-copy-only` | 2 | pass 3/3 ([t12](patches/t12.patch)) | pass 3/3 ([t11](patches/t11.patch)) | `pass` | 회귀 0 / 개선 0 |
| `master-page-consistency` | 1 | pass 5/5 ([t13](patches/t13.patch)) | pass 5/5 ([t14](patches/t14.patch)) | `pass` | 회귀 0 / 개선 0 |
| `master-page-consistency` | 2 | pass 5/5 ([t16](patches/t16.patch)) | pass 5/5 ([t15](patches/t15.patch)) | `pass` | 회귀 0 / 개선 0 |

`summary.json`은 개별 회귀·개선 ID, candidate 실패와 누락을 그대로 보존한다. `runs.json`은 실행별 검사 상태, 변경 경로, 실제 native context ID와 원본 파일의 해시를 연결한다. 의미·화면 판정은 구현 에이전트와 분리한 **Codex native AI 검수**다. 사람이 검수한 결과로 표현하지 않는다.

`master-page-consistency`의 통과는 지정한 밀도 변경과 기존 동작 보존 범위에 한정한다. 초기 좁은 표에서는 버튼과 포커스 오른쪽이 잘리는 기존 제약이 남았고, 실제 가로 스크롤 후의 버튼 노출·Tab/Enter/Space 접근을 별도로 확인했다. `t16`에는 스크롤 전 첫 Tab 포커스의 전후 캡처 쌍이 없으며 ArrowRight만으로의 복구도 미검증이다. 그 trial에서 가로 포커스 잘림이 기존 경계라는 판단은 불변 DOM·공통 CSS·폭을 함께 본 추론이고, 실제 전후 직접 관찰과 구분했다. 이 통과를 초기 접근성 문제 해결로 해석하지 않는다. 자세한 증거는 압축의 `actual/trials/t13`~`t16/review.md`에 있다.

## 비교 조건과 원본

- baseline 스킬: `78c0726fcb0d8058e10f16b6de24120c8024d768` (`snapshots/source-a/skills/`).
- candidate 스킬: `69149804ea292a8a8589c9dde0ebf164d0dde8fc` (`snapshots/source-b/skills/`).
- 평가기: `7ae3d287dfb0cd2b83a3ab608a74b0b96cb350e0`. 실행 전에 고정한 **41개 파일**의 해시와 해당 커밋 바이트를 대조했다. TASK·fixture도 이 snapshot에 들어 있다.
- 모든 실행은 `fork_turns=none`, `snapshot-direct`다. 사례별 fixture/TASK, 공통 prompt template와 도구 조건을 맞췄고 반복 1은 baseline→candidate, 반복 2는 candidate→baseline 순서로 launch했다.
- 모델·reasoning은 같은 부모 runtime을 상속했다. 별도 모델 override는 없으며 child별 모델 식별자·숨겨진 sampling/seed 값은 API에서 제공되지 않아 추정하지 않았다.
- 실행 환경: macOS 15.5 arm64, Node 25.2.1, Python 3.14.7, npm 11.7.0, Chrome 152.0.7977.82. 실제 설치된 Chrome을 임시 프로필과 loopback 합성 제품에서 실행했다.

압축은 약 16.0 MiB다. `scope-v1/actual/`은 원본 `issue-6-evals/`에 대응하고, 내부 상대 구조와 원래 절대 경로 문자열을 그대로 보존한다. 압축 해시: `9ff96da5265de930e31b0f37077afe5f703dd8b55427a22c5f365351869a72ee`.

| 압축 내부 경로 (`scope-v1/` 기준) | 보존한 자료 |
| --- | --- |
| `actual/trials/tNN/prompt.md`, `native-launch.json`, `native-completion.json` | 실제 prompt, native 요청/응답의 task_name, 완료 수신 기록 |
| `actual/trials/tNN/agent-output.md` | 부모가 수신한 최초 native 최종 응답 |
| `actual/trials/tNN/scratch/` | 구현 에이전트의 상세 `agent-output.md`, 실제 기록한 `commands.log`, 임시 검증 스크립트·이미지·관찰 자료 |
| `actual/trials/tNN/product/`, `before-manifest.json`, `after-manifest.json`, `diff.patch` | 실제 제품과 내용·종류·모드의 전후 inventory, 실제 diff |
| `actual/trials/tNN/source-checks.json`, `browser.json`, `external-executions.jsonl`, `images/` | 평가자 소유 source/Chrome 관찰, 실행한 수집 명령과 stdout/stderr, 화면 자료 |
| `actual/trials/tNN/review.md`, `review.json` | 독립 AI가 실제로 열어 본 이미지와 사례별 의미·화면 판정 |
| `actual/snapshots/`, `*-snapshot*.json`, `environment.json`, `shared-settings.json`, `native-tool-contract.json` | 두 스킬, 초기 fixture, 도구·41파일 평가기 snapshot과 실행 조건 |
| `controls/`, `controls-summary.json` | 실제 trial과 분리한 합성 harness 검사 로그·변이 patch·source inventory·browser JSON·이미지·검사 소스 |

전체 도구 호출 transcript는 native API에서 제공되지 않았다. launch/final, 에이전트가 작성한 명령 로그와 외부 수집 로그를 각각 보존했으며 누락된 transcript를 재구성하지 않았다. 원본 경로가 들어 있는 과거 명령은 당시 실행의 기록이므로 새 경로에서 그대로 재실행하는 명령으로 해석하지 않는다.

## Metadata 정정

부모가 공통 `settings.tool_contract_sha256`에 실제 파일과 다른 해시 `13c5c8fa…`를 기록한 오류를 최종 대조에서 발견했다. 초기 환경 기록과 실제 `native-tool-contract.json`의 해시 `34c9fd66…`를 근거로 16개 invocation과 공통 settings를 정정하고 파생 result를 다시 수집했다. 정정 전 metadata/result는 `actual/metadata-before-digest-correction/`, 변경 전후 해시·이유는 `actual/metadata-correction.json`에 보존했다. 요청·응답·제품·TASK·스킬·도구·평가기 파일을 바꾸거나 에이전트를 다시 실행한 것은 아니다. 이 정정은 metadata의 추적 가능성을 보완하며, 제공되지 않은 전체 runtime trace를 대신하지 않는다.

## 압축 확인과 결과 재현

저장소 root에서 실행한다. Python과 `tar`, `shasum`만 필요하며 이 집계 명령은 Chrome이나 모델을 다시 실행하지 않는다.

```sh
(cd evals/records/2026-09-07-scope-v1 && shasum -a 256 -c SHA256SUMS)
scope_replay="$(mktemp -d)"
tar -xzf evals/records/2026-09-07-scope-v1/evidence.tar.gz -C "$scope_replay"
(cd "$scope_replay/scope-v1" && shasum -a 256 -c SHA256SUMS)
python3 -B "$scope_replay/scope-v1/actual/snapshots/evaluator/scripts/summarize_scope_trials.py" \
  "$scope_replay/scope-v1/actual/manifest.json" --output "$scope_replay/summary.json"
cmp evals/records/2026-09-07-scope-v1/summary.json "$scope_replay/summary.json"
```

종료 코드 0은 candidate 필수 검사 통과, 1은 관찰된 candidate 실패, 3은 누락으로 인한 `incomplete`다. 통합 시 새 임시 폴더에서 압축 inventory/해시, 두 스킬과 41파일 평가기의 커밋 일치, 16개 고유 context·8쌍, 16개 제품 전후 inventory·source report·diff, result의 evidence 경로를 확인했다. 이 집계의 출력은 보존한 `summary.json`과 바이트가 같았다. 파일 순서·mtime·소유자와 gzip 헤더를 고정해 같은 파일 집합으로 같은 압축 바이트를 만든다. 캐시·브라우저 프로필·무관한 자료는 제외하며 symlink를 따라 외부 파일을 묶지 않는다.

## 합성 대조군과 한계

source/summary 20개, comparator 23개, 기존 Chrome 18개와 scope Chrome 10개 검사는 **합성 harness control**이다. scope Chrome은 초기 9개와 추가 root-symlink 1개를 나누어 실행했다. 일반 Python 발견 149개 중 Chrome 28개는 명시적으로 건너뛰었고 npm CLI 8개는 통과했다. 실제 16개 스킬 실행의 수나 결과에 이 검사들을 합산하지 않는다. scope 변이의 원본 patch·inventory와 browser 자료를 보존했다. 기존 Chrome 대조군은 browser JSON·이미지와 변이 정의의 테스트 소스를 보존하며, 없는 원본 제품 snapshot이나 별도 전체 도구 로그를 만들지 않았다.

- `installed-host-explicit`와 `automatic-discovery`는 각각 **`not-run`**이다. 지정한 snapshot을 직접 읽은 결과로 호스트의 발견/라우팅을 검증했다고 주장하지 않는다.
- 제품 final inventory의 일치는 최종 상태만 증명한다. 전체 transcript 없이 중간 쓰기가 전혀 없었다고 증명할 수 없다.
- source 판정은 선언된 수정 계약을 검사한다. 정해진 허구 복구 문구 변이의 검출은 자연어 의미 전반의 통과 증거가 아니다. 별도 AI 검수가 의미와 화면을 판단했다.
- Chrome 화면 크기·CDP Tab/Enter·AX 이름 관찰은 실제 휴대 기기, OS 한글 IME, 스크린리더 사용 검증이 아니다. 다른 OS·최소 지원 runtime에서 이 16개 실행을 반복하지 않았다.
- 판정 재현과 파일 해시는 증거의 내용이 진실하다는 자동 보증이 아니다. 두 번의 반복은 이 네 합성 제품과 이 runtime에 한정한다.
- 이 source 전용 기록은 npm 설치·오프라인 스킬 export에 포함하지 않는다. 실제 PR CI는 이 기록과 별도로 실행한다.
