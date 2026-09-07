# AI Slop Remover

AI가 만든 듯 획일적인 화면을 다듬고, 사용자가 편하게 작업을 끝낼 수 있는 UI/UX를 만드는 스킬 세트입니다. 정보 위계, 조작 흐름, 피드백, 오류 복구, 문구, 실제 화면 검수를 연결합니다.

부드러운 UX는 입력에 바로 반응하고, 화면과 포커스가 불필요하게 튀지 않으며, 실패해도 하던 작업을 이어갈 수 있는 경험입니다. 애니메이션은 필요한 곳에만 씁니다.

## 스킬 구성

| 호출 | 역할 |
| --- | --- |
| `$ai-slop-remover` | 필요한 스킬을 연결해 개선부터 검수까지 실행 |
| `$ui-slop-audit` | 근거와 사용자 영향을 중심으로 읽기 전용 진단 |
| `$ui-visual-refine` | 레이아웃·정보 위계·밀도·타이포 정리 |
| `$ux-flow-refine` | 상태·피드백·모션·오류 복구 개선 |
| `$ux-writing` | 버튼·안내·오류·빈 상태 문구 개선 |
| `$ui-quality-gate` | 구현 결과의 화면·동작을 읽기 전용 검수 |
| `$ui-craft-bundle` | 기존 통합 흐름과 공통 웹·네이티브 참조 |

카드, 그라디언트, 특정 글꼴이나 색상을 일괄 금지하지 않습니다. 기존 브랜드와 사용 목적을 먼저 확인합니다. 버튼 간격 하나를 고치는 요청에 전체 리디자인을 요구하지 않습니다.

## 2.1에서 보강한 흐름

- **디자인 결정 재사용:** 기존 `DESIGN.md`와 실제 토큰·컴포넌트를 함께 읽고, 공통 기준과 페이지별 예외를 구분합니다. 문서와 코드가 다르면 근거와 요청 범위로 조정합니다.
- **작업에 맞는 구조 선택:** 비교·탐색·읽기·편집 등의 작업을 기준으로 레이아웃과 밀도를 선택합니다. 브랜드 참고 자료를 제품 화면에 그대로 덮어씌우지 않습니다.
- **구체적인 UX 사례 8개:** 한글 조합 입력, 검색 히스토리, 스크롤·포커스 복귀, 안정적인 로딩, 연속 입력, 재시도, 붙여넣기·자동완성을 실제 결과로 확인합니다.
- **컴포넌트 사전 확인:** 큰 변경은 기존 미리보기에서 긴 한국어·오류·키보드·모션 축소 상태를 확인한 뒤 다른 화면으로 적용합니다.
- **실행 평가:** 결함을 심은 작은 UI와 외부 검사, 기존·새 버전 결과 비교 도구를 소스에 추가했습니다. 설치 검사와 실제 UI 결과를 구분합니다.

UI UX Pro Max·Vercel·getdesign.md에서 유용한 방법을 선별해 기존 7개 스킬에 연결했습니다. 외부 스킬 설치나 새로운 npm 의존성은 요구하지 않습니다.

## 설치

Node.js 20 이상과 Python 3.9 이상이 있으면 npm으로 바로 실행합니다.

```bash
npx ai-slop-remover-skills --list
npx ai-slop-remover-skills --repo "/path/to/project" --agent codex --dry-run
npx ai-slop-remover-skills --repo "/path/to/project" --agent codex
```

npm 명령은 함께 배포한 Python 설치기를 실행합니다. Python은 미리 설치되어 있어야 하며, PATH에서 찾지 못하면 `AI_SLOP_PYTHON`에 실행 파일의 정확한 경로를 지정하세요. npm 런타임 의존성이나 자동 postinstall 작업은 없습니다. Claude Code는 `--agent claude`로 설치합니다.

저장소 clone 또는 ZIP으로도 설치할 수 있습니다. `install.py`가 있는 폴더에서 아래 명령을 실행하세요. Python 설치기에는 별도 패키지나 API 키가 필요하지 않습니다.

```bash
python3 install.py --list
python3 install.py --repo "/path/to/project" --agent codex --dry-run
python3 install.py --repo "/path/to/project" --agent codex
```

Codex는 `프로젝트/.agents/skills/`, Claude Code는 `--agent claude`로 `프로젝트/.claude/skills/`에 설치합니다. 설치 후 호스트에서 스킬을 다시 탐색하거나 세션을 새로 여세요. 파일 복사는 실제 발견·실행의 증거가 아닙니다.

필요한 스킬만 선택하면 공통 참조 의존성도 함께 설치됩니다.

```bash
python3 install.py --repo "/path/to/project" --agent codex --skill ux-writing
python3 install.py --repo "/path/to/project" --agent codex --skill ui-slop-audit --skill ui-quality-gate
```

`--skill`을 반복해서 여러 스킬을 고를 수 있습니다. 기본값과 `--skill ai-slop-remover`는 전체 7개 스킬을 설치합니다.

기존 단일 번들 설치 명령도 유지합니다.

```bash
python3 install.py --dest "/absolute/path/to/skills/ui-craft-bundle"
```

형제 패키지가 필요한 스킬은 `--repo --agent`로 설치하세요. `--dest`의 기본 대상은 기존 `ui-craft-bundle` 하나입니다.

설치기는 해시를 검증하며 동일한 설치는 건드리지 않습니다. 수정되었거나 소유권을 확인할 수 없는 기존 폴더가 있으면 새 파일을 복사하기 전에 거부합니다. 업데이트할 때는 기존 설치를 검토해 백업 위치로 옮긴 뒤 다시 설치하세요. 사용자 수정본을 자동으로 덮어쓰지 않습니다.

`AGENTS.md`, `CLAUDE.md`, 프로젝트 코드, 전역 설정을 수정하지 않고 네트워크 다운로드도 하지 않습니다. 해시는 우발적 변경을 확인하는 수단이며 배포자 서명은 아닙니다. Git 메타데이터와 개발용 도구는 설치 대상에서 제외합니다.

## 바로 쓰는 요청

### 기존 화면 개선

```text
$ai-slop-remover
이 프로젝트의 검색 화면에서 AI 티와 사용 중 불편을 줄여줘.
사용자는 여러 항목을 비교하고 원하는 결과를 찾는 사람이야.
기존 브랜드와 기능을 유지하고 현재 화면부터 확인해.
정보 위계, 검색·필터 피드백, 빈 결과와 실패 복구를 개선해.
좁은 화면과 키보드 조작을 확인하고, 실제로 확인한 결과를 알려줘.
```

### 흐름과 모션만 개선

```text
$ux-flow-refine
편집 화면에서 저장 중인지 헷갈리고, 실패하면 입력이 사라져.
입력값과 포커스를 유지하고 재시도할 수 있게 해줘.
모션은 상태를 설명할 때만 쓰고 연속 클릭과 모션 축소 설정도 확인해.
```

### 기존 디자인으로 다음 화면 만들기

```text
$ai-slop-remover
기존 DESIGN.md와 실제 코드 토큰을 먼저 읽고 상세 화면을 추가해줘.
공통 기준과 페이지별 예외를 유지해.
검색에서 상세 화면으로 갔다 돌아올 때 상태와 읽던 위치를 보존하고,
새로 결정한 디자인 규칙은 기존 문서에 근거와 함께 남겨줘.
```

### 문구만 개선

```text
$ux-writing
버튼, 오류 메시지, 빈 상태 문구만 자연스러운 한국어로 다듬어줘.
실제 동작과 제품 용어는 유지하고 사용자가 다음 행동을 알 수 있게 해줘.
긴 문구가 작은 화면에서 잘리지 않는지도 확인해.
```

### 네이티브 앱

```text
$ai-slop-remover
Jetpack Compose 일정 편집 화면을 더 편하게 만들어줘.
기존 내비게이션과 디자인 시스템을 유지해.
시간 수정·순서 변경·저장·취소를 실제 상태 변화와 연결하고,
드래그 대체 조작, 키보드, 저장 실패 후 입력 보존을 확인해.
에뮬레이터를 실행할 수 없으면 그 검증은 미실행으로 표시해.
```

호스트가 `$이름`을 지원하지 않으면 스킬 선택기나 해당 호스트의 호출 방식을 사용하세요. Claude Code에서는 `/ai-slop-remover`처럼 호출합니다. Figma, MCP 서버, 외부 디자인 스킬, 애니메이션 라이브러리 없이 지침을 적용할 수 있습니다. 실제 앱 실행과 화면 검수에는 프로젝트 개발 환경과 호스트가 허용한 도구가 필요합니다.

## 검증과 배포

아래 명령은 소스 체크아웃에서 실행합니다. 배포 ZIP에는 설치기·스킬·사용 안내를 넣고 개발용 스크립트와 테스트는 제외합니다.

```bash
python3 -m unittest discover -s tests -v
python3 scripts/update_manifest.py --check
python3 scripts/check_package.py
python3 scripts/export_bundle.py --output dist/ai-slop-remover.zip
npm test
npm pack --dry-run
```

배포 파일을 의도적으로 수정했다면 `python3 scripts/update_manifest.py`로 해시를 갱신한 뒤 다시 검증합니다. 내보내기는 검증을 통과한 manifest 파일만 ZIP에 넣습니다.

[행동 사례](evals/skill-cases.json)는 좁은 수정, 브랜드 유지, 저장 실패, 모션 축소, 한국어 줄바꿈, 도구 부재 등의 기대를 정의합니다. 사례 형식 검증은 실제 에이전트 실행 평가와 다릅니다. 이번 범위는 [검증 기록](docs/verification.md)에 남깁니다.

완료 보고에서는 구현, 빌드 검사, 화면 관찰, 동작 테스트, 미검증을 구분합니다. 스킬만으로 특정 미감이나 품질이 보장되지는 않습니다.

소스의 `evals/README.md`에는 결함이 있는 작은 UI로 기존·새 스킬을 비교하는 절차가 있습니다. `scripts/compare_evals.py`는 같은 조건의 결과와 증거 누락을 검사합니다. 선택 도구인 `scripts/run_browser_checks.mjs`는 이미 설치된 Chrome과 Node 22 이상을 사용하며 별도 패키지를 설치하지 않습니다. 평가 개발 도구는 npm 스킬 배포본에서 제외합니다. 한 번의 비교 결과를 모든 제품·모델에서의 품질 향상으로 해석하지 않습니다.

## 라이선스

새로 작성한 지침과 코드는 [MIT](LICENSE)로 제공합니다. 외부 스킬 원문·폰트·아이콘은 포함하지 않습니다. 패키지 형식은 [Agent Skills 명세](https://agentskills.io/specification)를 참고하며, 스킬별 역할과 작업 흐름은 이 프로젝트의 설계입니다.
