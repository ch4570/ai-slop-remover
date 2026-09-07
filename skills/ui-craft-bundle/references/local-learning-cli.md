# 로컬 평가·개선 CLI

설치된 `ui-craft-bundle/scripts/local_learning.py`는 **수동 증거 제출 → 적격 판정 → 명시적 채택·복귀**를 실행한다. Python 3.9 이상을 사용하며 외부 패키지나 API 키는 필요 없다. 개념과 확장 설계는 [로컬 개선 게이트](local-learning.md), [구현 계약](local-learning-contract.md)을 참고한다.

현재 모드는 `propose`, 평가 프로파일은 `reviewed-local`만 지원한다. 모델 실행기, 자동 관찰·후보 생성·회귀 감시, 자동 채택, 호스트 지침 주입, 권한으로 강제한 실험 격리는 구현되지 않았다. 별도 검토자가 실제 결과를 재현하고 원시 증거를 확인해야 한다. 해시·스키마 검증은 기록의 일관성을 확인하며 **관찰의 진실성이나 검토자 독립성을 인증하지 않는다.** 판정의 `evidence_level`은 `declared-records`다.

증거 판정에는 `O_NOFOLLOW`와 `dir_fd` 기반 파일 열기를 지원하는 환경이 필요하다. 미지원 환경에서는 정상 기록도 `incomplete`로 남고 채택할 수 없다. 현재 검증은 macOS에서 수행했으며 Windows의 전체 평가·채택 지원을 주장하지 않는다.

## 시작과 저장 위치

`--project`에는 실제 제품 프로젝트의 루트를 지정한다. 기록은 그 아래 `.lutriva/local/`에 저장한다. 지정한 스킬 기반 디렉터리 안에서 초기화하는 요청은 거부한다. `--base`는 `ui-craft-bundle` 등을 포함한 **스킬들의 부모 디렉터리**다. 생략하면 실행 중인 스크립트가 속한 스킬들의 부모를 사용한다. 제품 프로젝트가 `.agents/skills/` 같은 설치 경로를 포함하는 일반적인 구조는 허용한다.

`init`은 정책·활성 포인터와 후보·평가·릴리스·전환 기록 디렉터리를 만들고 로컬 `.gitignore`에 `*`를 기록한다. 기존 저장소는 덮어쓰지 않으며 Git에서 이미 추적한 저장 경로는 거부한다. Git 저장소의 추적 여부를 검사할 수 없을 때도 기록을 시작하지 않는다. 정상적인 비Git 디렉터리와 Git 실행파일이 없는 환경은 지원한다. 이후의 강제 Git 추가나 클라우드 동기화까지 차단하지 않으므로 기록 위치와 허용된 증거 범위를 먼저 확인한다. 다른 프로젝트나 사용자에게 자동 전파하지 않는다.

아래는 **명령 사용 예시이며 실행·개선 증거가 아니다.** 경로를 실제 값으로 바꾸고, `spec.json`, `rules.md`, `report.json`, `evidence/`는 아래 계약에 따라 실제 과업과 관찰에서 작성한다.

```sh
lutriva_cli="/path/to/skills/ui-craft-bundle/scripts/local_learning.py"
learning_project="/path/to/product"
learning_inputs="/path/to/local-evaluation-inputs"
python3 "$lutriva_cli" init --project "$learning_project" --max-runs 6 --max-seconds 1200
python3 "$lutriva_cli" propose --project "$learning_project" \
  --rules "$learning_inputs/rules.md" --spec "$learning_inputs/spec.json"
```

`propose`가 출력한 `candidate_id`, `plan`, `plan_sha256`를 보존한다. 후보에는 현재 호환 활성 규칙과 새 규칙을 함께 고정한다. 기존 규칙을 대체하려면 `spec.replaces`에 활성 규칙 ID를 지정한다. 제안 뒤 규칙·계획 파일을 직접 고치지 말고 변경이 필요하면 새 후보를 만든다.

## 제안 입력: spec.json

알 수 없는 필드와 중복 JSON 키는 거부한다. 다음 필드는 모두 필수이며 `replaces`만 선택 사항이다.

| 필드 | 값과 조건 |
| --- | --- |
| `scope` | `skill_ids`, `platforms`, `task_kinds`를 가진 객체. 각 값은 중복 없는 비어 있지 않은 ID 배열이다. |
| `profile` | `"reviewed-local"`. |
| `target_pairs` | 같은 과업을 반복 비교할 고유 ID 정확히 2개. |
| `transfer_pairs` | 전이·반례 비교 ID 1개 이상. 대상 ID와 구분한다. |
| `required_checks` | 모든 baseline/candidate 실행에서 확인할 검사 ID 배열. |
| `improvement_checks` | 개선을 주장할 검사 ID 배열. `required_checks`의 부분집합이다. |
| `context` | 대상 비교의 과업·시작 fixture·모델·설정·도구를 고정한 객체. 아래 형식을 사용한다. |
| `transfer_contexts` | 각 `transfer_pairs` ID를 해당 context 객체에 대응시킨다. 대상과 다른 fixture 해시를 지정한다. |
| `replaces` | 선택 사항. 이번 후보가 대체할 현재 활성 규칙 ID 배열. |

`scope` 예시는 `{"skill_ids":["ux-flow-refine"],"platforms":["web"],"task_kinds":["form"]}`다. 플랫폼·과업 ID는 프로젝트에서 정한 값을 이후 `context` 명령에도 똑같이 사용한다. 조건 세 개가 모두 일치해야 규칙이 선택된다.

각 context는 정확히 다음 필드를 가진다. 해시는 임의 문자열 대신 실제 비교 입력의 SHA-256 소문자 64자리로 기록하고, 파일 묶음은 재현 가능한 같은 목록·해시 방식을 사용한다. 이 CLI가 과업·fixture·도구 원본을 받아 해시의 진실성까지 확인하는 것은 아니다.

```json
{
  "task_sha256": "실제 과업 해시로 교체",
  "fixture_sha256": "실제 시작 fixture 해시로 교체",
  "model": "실제로 비교에 사용한 모델",
  "settings": {"viewport": [390, 844], "locale": "ko-KR"},
  "tools_sha256": "실제 도구와 검사 계약 해시로 교체"
}
```

위 자리표시자는 유효한 입력이 아니다. 전이·반례는 별도 fixture에서 규칙의 적용 범위와 기존 동작 보존을 확인하며, `model`, `settings`, `tools_sha256`는 대상 context와 같아야 한다. 같은 fixture의 이름만 바꾼 기록으로 대체하지 않는다. 검토자는 고정된 계획·규칙을 기준으로 비교 작업 공간과 평가 자료를 준비하며, 이 CLI가 작업 공간이나 미공개 사례를 생성·격리하지 않는다.

## 실제 비교와 report.json

baseline에는 현재 사용하는 공통 스킬과 호환 활성 규칙, candidate에는 같은 공통 스킬과 제안된 규칙 집합을 제공한다. `context --candidate`로 후보에 맞는 조건부 규칙을 확인할 수 있다. 실행·화면 검수·별도 검토를 마친 뒤 아래 형식으로 기록한다. 통과하도록 `pass`나 검토 플래그를 채우지 않는다.

| 객체 | 필수 필드 |
| --- | --- |
| report | `schema: 1`, 제안 출력의 `plan_sha256`, `plan.candidate_sha256`와 같은 `candidate_sha256`, `pairs`, `review` |
| pairs의 각 항목 | 계획의 `pair_id`, `kind` (`target` 또는 `transfer`), 해당 계획과 같은 `context`, `baseline`, `candidate` |
| baseline / candidate | 전체 보고서에서 고유한 `run_id`, 실제 `duration_seconds`, `checks` 배열 |
| checks의 각 항목 | 계획의 검사 `id`, `status` (`pass` / `fail` / `not-run`), 실제 관찰 또는 미실행 이유인 `reason`, 증거 상대경로 `evidence` |
| review | 실제 수행 여부를 나타내는 boolean `independent`, `reproduced`, `evaluator_isolated`, `holdout_unseen`과 검토 기록 상대경로 `evidence` |

`not-run`은 `evidence`를 생략할 수 있다. 다른 상태에는 비어 있지 않은 실제 증거 파일이 필요하다. 모든 계획된 비교 쌍·검사를 포함하고 실패한 실행을 빼지 않는다. 대상 pair의 context는 `plan.context`, 전이 pair는 `plan.transfer_contexts[pair_id]`와 같아야 한다. 현재 수동 적격에는 `independent`와 `reproduced`가 실제로 참이어야 하며, 나머지 플래그도 관찰한 사실대로 기록한다.

`evidence` 경로는 제출할 `evidence/` 디렉터리 아래의 정규 상대경로다. 경로 탈출·symlink·특수 파일은 허용하지 않는다. 검토 기록에는 고정 자료 대조와 독립 재현 결과를 담는다. 파일 존재나 자기 보고만으로 검토를 대신하지 않는다. CLI는 제출 디렉터리를 평가 기록에 복사하므로 필요한 자료만 넣는다.

```sh
# ID는 앞선 명령의 실제 JSON 출력값을 사용한다.
learning_candidate="c-실제후보ID"
python3 "$lutriva_cli" evaluate --project "$learning_project" \
  --candidate "$learning_candidate" --report "$learning_inputs/report.json" \
  --evidence "$learning_inputs/evidence"
```

출력의 `decision`에서 `verdict`, `improvements`, `regressions`, `missing`, `errors`, `limitation`을 확인한다. 같은 사전 지정 검사가 두 대상 비교에서 모두 `fail → pass`로 바뀌고, 필수 검사와 전이·반례 보존 및 검토 조건이 충족돼야 `eligible`이다. 양쪽 통과는 `no-change`; 후보 실패·계획 위반은 `rejected`; 실행·증거·검토 부족은 `incomplete`다. `eligible`도 아직 활성화된 상태는 아니다.

`max_runs`와 `max_seconds`는 **제출된 보고서의 실행 수와 시간 합계**를 검사한다. 실행기를 중단하거나 보고하지 않은 비용·여러 후보의 누적 사이클 예산을 강제하지 않는다. 실행 예산은 실제 비교를 수행하는 쪽에서도 지켜야 한다.

## 채택·조회·복귀

```sh
learning_evaluation="e-실제평가ID"
python3 "$lutriva_cli" promote --project "$learning_project" --evaluation "$learning_evaluation"
python3 "$lutriva_cli" status --project "$learning_project"
python3 "$lutriva_cli" context --project "$learning_project" \
  --skill ux-flow-refine --platform web --task-kind form
# 채택 전 후보의 규칙을 조회할 때는 위 context 명령에 다음 옵션을 붙인다.
# --candidate "$learning_candidate"
python3 "$lutriva_cli" rollback --project "$learning_project"
```

`promote`는 수동 적격, 원시 증거·후보·정책·기반 해시, 활성 generation과 부모를 다시 확인한 뒤 릴리스와 전환 기록을 보존하며 활성 포인터를 바꾼다. 평가 이후 변경이나 동시 채택으로 부모가 달라지면 새 후보·평가가 필요하다. `context`는 조건에 맞는 규칙을 JSON으로 반환한다. 작업을 수행하는 사용자가 이를 과업과 함께 명시적으로 제공하며, 호스트가 자동으로 읽거나 지침으로 주입하지 않는다. 사용자 요구·제품 기준과 적용 제외 조건도 함께 판단한다.

`rollback`은 직전 호환 릴리스로 돌아가며, 없거나 손상됐거나 기반이 다르면 공통본만 사용하는 `base-only`로 전환한다. 현재 규칙 파일이 손상됐더라도 포인터와 전환 기록이 유효하면 복귀할 수 있다. `--release 실제릴리스ID`로 특정 호환본을 고를 수 있으며, 명시한 릴리스가 비호환·손상이면 거부한다.

`status`와 `context`는 읽기 전용이다. 공통 스킬 변경을 발견하면 `status`는 계산된 `suspended` 상태를 반환하고 기본 `context`는 이전 로컬 규칙을 제외하지만, 조회가 `active.json`을 수정하지는 않는다. 후보 조회도 현재 세대·부모와 같아야 하며, 다른 후보가 채택된 뒤에는 오래된 후보 조회를 거부한다.

활성 포인터와 전체 전환 기록의 세대·이전/이후 상태를 대조한다. 오래된 포인터만 복원하거나 전환 기록이 끊기면 규칙을 제공하지 않는다. `prepared` 상태에서 중단된 전환도 자동 복구하지 않으며, 현재 포인터가 이전/이후 상태 중 어느 쪽인지 오류에 표시하고 조회·변경을 중단한다. 포인터 손상이나 기록 누락은 원본을 보존하고 유효한 백업과 전체 전환 기록을 확인해 복구한다. 같은 사용자가 전체 저장소를 다시 작성하는 행위를 인증·방지하는 기능은 아니다.

## 출력과 운영 한계

정상 처리와 게이트 판정은 stdout에 JSON 객체 하나를 출력한다. 종료 코드는 성공·`eligible`·`no-change`가 `0`, `rejected`가 `1`, 입력·저장소·채택 오류가 `2`, `incomplete`가 `3`이다. 따라서 `0`만으로 채택 가능 여부를 판단하지 않는다. 처리 오류와 잘못된 CLI 옵션은 stderr의 JSON `error`와 종료 코드 `2`를 반환한다.

초기화 이후 쓰기 연산은 `.lutriva/local/.lock`으로 겹침을 거부한다. SIGKILL 등으로 남은 잠금은 소유 프로세스와 관련 실행이 끝났는지 확인한 뒤 수동으로 복구하며, 시간 경과만으로 삭제하지 않는다. 원자적 포인터 교체와 전환 기록은 있지만 전원 손실 뒤 파일시스템의 완전한 복구까지 입증한 구현은 아니다.

소스 전용 `scripts/compare_evals.py`는 기존 평가 schema 1을 사용하며 이 CLI의 spec/report와 호환되지 않는다. 같은 `schema: 1`이라도 그대로 넘기거나 필드를 덧붙이지 않는다. 기존 실행·증거를 원본으로 보존하고 위 로컬 보고서를 별도로 작성하며, 기존 비교기의 `pass`를 로컬 `eligible`로 바꾸지 않는다.
