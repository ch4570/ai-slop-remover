<p align="center">
  <img src="docs/assets/lutriva-hero.png" alt="Lutriva — 옥빛 물결을 따라 움직이는 아이보리색 수달" width="100%">
</p>

# Lutriva · 루트리바

[English](README.md) · [한국어](README.ko.md)

**덜 헤매고, 더 자연스럽게.**

Lutriva는 **Codex와 Claude Code**에서 제품 화면과 사용 흐름을 다듬는 7개 스킬입니다. 획일적인 화면의 원인을 찾고, 정보 위계와 문구를 정리하고, 입력부터 오류 복구까지 실제로 편해졌는지 확인합니다.

**7개 스킬 · 웹·네이티브 지침 · Codex / Claude Code · MIT**

기존 **AI Slop Remover**의 새 이름입니다. 물결을 가르는 수달처럼, 사용자가 막힘없이 작업을 이어가는 경험을 지향합니다. [이름과 호환성 안내](docs/naming.md).

[빠른 시작](#빠른-시작) · [사용 예시](#실제-작업을-맡겨보세요) · [스킬 선택](#필요한-범위만-선택) · [개선 기준](#어떤-경험을-만드나요) · [검증](#결과까지-확인합니다)

## 어떤 경험을 만드나요

- **다음 행동이 보이는 화면.** 정보 위계와 밀도, 문구가 사용자의 판단을 돕습니다.
- **하던 일을 이어가는 흐름.** 입력에 반응하고, 포커스가 튀지 않으며, 저장에 실패해도 초안이 남습니다.
- **제품다운 일관성.** 기존 브랜드와 토큰, 컴포넌트, 화면별 예외를 기준으로 개선합니다.
- **확인할 수 있는 결과.** 구현한 내용, 직접 본 화면, 실행한 동작 검사를 구분해 보고합니다.

현재 화면과 사용 목적부터 살핍니다. 간격 하나를 고칠 때는 그 범위에 집중하고, 리디자인이 필요하면 흐름 전체를 봅니다. 색상·카드·글꼴은 실제 맥락으로 판단합니다.

### AI-SLOP을 줄이는 방법과 공통 원칙

[14가지 개선 방법](skills/ui-craft-bundle/references/anti-slop-methods.md)을 **증상 → 수정 방법 → 유지할 것·확인 방법**으로 정리했습니다. [웹·모바일 공통 UI/UX 원칙](skills/ui-craft-bundle/references/ux-foundations.md)과 함께, 필요한 작업에서만 읽도록 7개 스킬에 연결했습니다.

| 관찰한 문제 | 적용하는 방법 |
| --- | --- |
| 큰 소개 영역과 반복 카드가 작업을 가림 | 실제 과업을 앞세우고 비교·탐색에 맞는 구조 선택 |
| 모든 버튼·배지가 똑같이 강조됨 | 행동의 중요도, 의미에 따른 묶음, 글자·간격의 역할 정리 |
| 업종 이름만 바꿔도 같은 화면이 됨 | 실제 데이터 관계·단위·용어·브랜드로 제품의 특성 표현 |
| 옵션은 많고 현재 선택은 보이지 않음 | 자주 쓰는 행동과 현재 상태를 드러내고 보조 옵션을 단계적으로 공개 |
| 아이콘·토스트만으로 조작과 결과를 설명함 | 알아볼 수 있는 컨트롤, 맥락 안의 피드백, 실제 상태에 맞는 문구 |
| 오류가 나면 입력과 맥락을 잃음 | 재입력 줄이기, 초안 보존, 가능한 취소·수정·복구 제공 |
| 데스크톱 축소본만 모바일로 제공함 | 공간에 맞는 구조, 터치 영역, 키보드·큰 글자·긴 한국어 확인 |
| 움직임과 샘플 데이터에서만 완성도가 보임 | 불필요한 대기 줄이기, 모션 감소, 실제 길이·수량·실패 상태로 검증 |

공통 원칙은 **기억에 의존하지 않는 선택, 일관된 용어와 위치, 정보 위계, 사용자 통제, 오류 예방·복구, 접근 가능한 조작**입니다. WCAG 2.2 기준과 Apple·Android 권장값은 단위와 예외를 구분합니다. NN/G, W3C, Apple, Android, GOV.UK 자료를 확인하고 [출처와 적용 범위](skills/ui-craft-bundle/references/sources.md)에 기록했습니다. 특정 색이나 카드 사용만으로 문제를 판정하지 않습니다.

**배색과 배치**도 구체적인 판단 순서로 다룹니다. [배색 구성](skills/ui-craft-bundle/references/color-composition.md)은 색의 역할과 전경·배경 조합, 인접 면, 색이 차지하는 면적과 강조를 함께 봅니다. [배치 구성](skills/ui-craft-bundle/references/layout-composition.md)은 실제 콘텐츠에 필요한 폭, 공통 정렬선, 그룹별 간격, 좁은 화면의 재배치를 다룹니다. 시각 스킬은 기존 브랜드를 유지하면서 실제 화면에서 두 구성을 함께 확인합니다.

**[토스 기술 블로그의 디자인 글 8개](skills/ui-craft-bundle/references/toss-design.md)**도 직접 확인해 반영했습니다. 다음 행동이 예상되는 한국어 문구, 키보드가 열린 가입 흐름, 드래그 대체 조작, 실제 상태를 설명하는 모션, 모바일·PC별 정보 구조, 컴포넌트 확장과 명세, 초기 사용성 검증을 다룹니다. 원문의 관찰과 프로젝트에 적용할 판단·확인 방법을 구분하고, 필요한 작업에서 찾아 읽도록 연결했습니다.

## 빠른 시작

npm 레지스트리 게시는 **아직 완료되지 않았습니다**. 지금은 소스를 받아 설치하세요. 저장소가 비공개인 동안에는 접근 권한이 필요합니다. Python 설치기는 **Python 3.9 이상**만 있으면 되며 별도 패키지나 API 키가 필요하지 않습니다.

```sh
git clone https://github.com/ch4570/lutriva.git lutriva
cd lutriva
python3 install.py --repo "/path/to/project" --agent codex --dry-run
python3 install.py --repo "/path/to/project" --agent codex
```

예시 경로를 실제 프로젝트 경로로 바꾸세요. Claude Code는 `--agent claude`를 사용합니다. 기본값은 공통 참조를 포함한 7개 스킬 전체입니다.

| 호스트 | 스킬 설치 위치 |
| --- | --- |
| Codex | `.agents/skills/` |
| Claude Code | `.claude/skills/` |

Codex에서는 `$ai-slop-remover`, Claude Code에서는 `/ai-slop-remover`로 시작합니다.

설치 후 스킬을 다시 탐색하거나 호스트를 재시작하세요. **설치는 터미널에서, 작업 요청은 Codex·Claude Code 안에서 합니다.** 호출 형식이 다르면 호스트의 스킬 선택기를 사용하세요.

<details>
<summary>npm CLI와 설치 옵션</summary>

새 npm 패키지와 기본 CLI 이름은 `lutriva`입니다. npm 실행에는 **Node.js 20 이상과 Python 3.9 이상**이 필요합니다. npm과 Git으로 저장소 버전을 직접 실행할 수도 있습니다.

```sh
npx --yes --package='git+https://github.com/ch4570/lutriva.git' -- lutriva --list
npx --yes --package='git+https://github.com/ch4570/lutriva.git' -- lutriva --repo "/path/to/project" --agent codex --dry-run
```

이 명령은 기본 브랜치를 따라가며 저장소 접근 권한이 필요합니다. `--dry-run`을 빼면 설치합니다. npm에 `lutriva@2.4.0`이 게시된 후에는 다음 명령을 쓸 수 있습니다.

```sh
npx lutriva@2.4.0 --repo "/path/to/project" --agent codex
```

같은 패키지에서 기존 `ai-slop-remover` CLI도 제공합니다. Python을 찾지 못하면 `AI_SLOP_PYTHON`에 실행 파일의 정확한 경로를 지정하세요. npm 런타임 의존성과 자동 postinstall 작업은 없습니다.

소스에서 필요한 스킬만 설치할 수도 있습니다.

```sh
python3 install.py --list
python3 install.py --repo "/path/to/project" --agent codex --skill ux-writing
python3 install.py --repo "/path/to/project" --agent codex --skill ui-slop-audit --skill ui-quality-gate
```

`--skill`을 반복해서 여러 스킬을 고르면 필요한 공통 참조도 함께 설치합니다. `ai-slop-remover`를 고르면 전체 7개를 설치합니다. 기존 단일 번들 설치 명령도 유지합니다.

```sh
python3 install.py --dest "/path/to/skills/ui-craft-bundle"
```

형제 스킬이 필요한 경우에는 `--repo --agent`를 사용하세요. 동일한 설치는 건드리지 않습니다. 수정되었거나 소유권을 확인할 수 없는 폴더는 새 파일을 복사하기 전에 거부합니다. 업데이트할 때는 기존 설치를 검토해 백업 위치로 옮긴 뒤 다시 설치하세요. 사용자 수정본을 자동으로 덮어쓰지 않습니다.

재설치 전에 선택한 스킬과 의존성 전체의 상태를 확인하세요.

```sh
python3 install.py --repo "/path/to/project" --agent codex --status
```

npm CLI에서도 같은 `--status` 옵션을 사용합니다. `--skill`로 범위를 좁히거나, 단독 스킬 하나는 `--dest`로 지정할 수 있습니다. 각 설치 경로와 설치·배포 버전, 다음 상태를 보여줍니다.

| 출력 상태 | 의미 |
| --- | --- |
| `not installed` | 설치 경로가 없습니다. |
| `identical installation` | 버전, 기록된 파일 목록, 실제 파일 내용이 같습니다. |
| `version only; skill contents identical` | 배포 버전만 다릅니다. 스킬 내용이 같은 2.1.0 → 2.2.0도 이렇게 표시합니다. |
| `release content changed` | 새 배포의 파일이 설치 기록과 다릅니다. |
| `user modifications` | 로컬 파일이 설치 기록과 다릅니다. |
| `release content changed; user modifications` | 배포와 로컬이 각각 바뀌었습니다. 사용자 수정본이 새 배포와 같아도 둘 다 표시합니다. |
| `unverifiable` | 소유권, 설치 기록, 안전한 파일 접근 여부를 확인할 수 없습니다. |

로컬 변경과 배포 변경을 나누어 추가·삭제·수정된 상대 파일 경로를 보여주며, 새로 생긴 빈 폴더도 표시합니다. 파일 원문은 출력하지 않습니다. 확인이 필요한 기존 설치에는 재설치 전 검토·백업할 경로를 안내합니다. 손상된 기록, symlink, 안전하지 않은 경로는 확인 불가로 남기고 나머지 스킬도 계속 진단합니다.

`--status`는 파일 내용과 수정 시각을 유지합니다. 충돌이나 확인 불가 항목이 있어도 전체 보고를 마치면 종료 코드 0을 반환합니다. 잘못된 옵션은 2, 배포 검증이나 프로젝트 경로 확인 실패는 1입니다. `--dry-run`, `--list`와 함께 쓸 수 없습니다. `--dry-run`과 실제 설치는 버전 차이, 사용자 수정, 소유권을 확인할 수 없는 경로를 계속 거부하며, 진단 결과가 자동 업데이트나 덮어쓰기를 허용하지는 않습니다.

설치기는 프로젝트 코드, `AGENTS.md`, `CLAUDE.md`, 전역 설정을 유지합니다. Python 설치기는 네트워크 다운로드를 하지 않습니다. 해시는 파일 변경을 확인하는 수단이며 배포자 서명은 아닙니다. [호환성 상세](docs/naming.md#compatibility).

</details>

## 실제 작업을 맡겨보세요

누가 사용하는 화면인지, 무엇을 끝내야 하는지, 무엇을 유지해야 하는지 알려주세요.

```text
$ai-slop-remover
여러 결과를 비교하는 사용자를 위해 검색 화면을 다듬어줘.
현재 화면부터 보고, 기존 브랜드와 기능은 유지해.
정보 위계, 검색·필터 피드백, 빈 결과와 실패 복구를 개선해.
좁은 화면, 키보드 조작, 검색부터 선택까지의 흐름을 확인해.
바꾼 내용과 실제로 검증한 결과를 구분해서 알려줘.
```

범위가 분명하면 해당 스킬을 바로 호출하세요.

| 필요한 작업 | Codex에서 보낼 요청 |
| --- | --- |
| 저장 실패 후 작업 보존 | `$ux-flow-refine` — 입력값과 포커스를 유지하고, 저장 상태와 재시도를 분명하게 해줘. |
| 자연스러운 한국어 문구 | `$ux-writing` — 버튼·오류·빈 상태 문구를 다듬어줘. 실제 동작과 제품 용어를 유지하고 다음 행동을 알려줘. |
| 구현된 화면 검수 | `$ui-quality-gate` — 주요 흐름, 키보드, 좁은 화면, 관련 실패 상태를 직접 확인해줘. |

Claude Code에서는 `$` 대신 `/`를 씁니다. 네이티브 앱은 플랫폼과 화면의 목적을 함께 알려주세요.

<details>
<summary>디자인을 이어 쓰거나 네이티브 앱을 다듬는 예시</summary>

```text
$ai-slop-remover
기존 DESIGN.md와 코드 토큰을 읽고 상세 화면을 추가해줘.
공통 기준과 페이지별 예외를 유지하고, 검색으로 돌아올 때
필터와 읽던 위치가 유지되게 해줘. 새 디자인 결정은 근거와 함께 남겨줘.
```

```text
$ai-slop-remover
Jetpack Compose 일정 편집 화면을 다듬어줘.
기존 내비게이션과 디자인 시스템을 유지해.
시간 수정, 순서 변경, 저장, 취소를 실제 상태와 연결하고
드래그 대체 조작과 저장 실패 후 입력 보존을 확인해.
에뮬레이터를 실행하지 못하면 그 검증은 미실행으로 표시해.
```

</details>

앱 실행과 화면 검수에는 프로젝트 개발 환경과 호스트가 허용한 브라우저·기기 도구가 필요합니다. Figma, 외부 디자인 스킬, 애니메이션 라이브러리는 선택 사항입니다.

## 필요한 범위만 선택

| 스킬 | 맡는 일 |
| --- | --- |
| [`ai-slop-remover`](skills/ai-slop-remover/SKILL.md) | 진단부터 개선·검수까지 필요한 스킬 연결 |
| [`ui-slop-audit`](skills/ui-slop-audit/SKILL.md) | 근거와 사용자 영향을 중심으로 읽기 전용 진단 |
| [`ui-visual-refine`](skills/ui-visual-refine/SKILL.md) | 배색·배치·위계·밀도·타이포·반응형 조정 |
| [`ux-flow-refine`](skills/ux-flow-refine/SKILL.md) | 상태·피드백·모션·실패 복구 개선 |
| [`ux-writing`](skills/ux-writing/SKILL.md) | 버튼·안내·오류·빈 상태 문구 개선 |
| [`ui-quality-gate`](skills/ui-quality-gate/SKILL.md) | 구현 결과의 화면과 동작을 읽기 전용 검수 |
| [`ui-craft-bundle`](skills/ui-craft-bundle/SKILL.md) | 통합 흐름과 공통 웹·네이티브 참조 |

[디자인 기억](skills/ui-craft-bundle/references/design-memory.md)은 `DESIGN.md`를 실제 토큰·컴포넌트에 연결합니다. [패턴 선택](skills/ui-craft-bundle/references/pattern-selection.md)은 사용자의 과업에서 출발하고, [상호작용 사례 8개](skills/ui-craft-bundle/references/interaction-recipes.md)는 입력과 내비게이션의 세부 동작을 다룹니다. 공통 변경은 [컴포넌트 예시](skills/ui-craft-bundle/assets/component-specimen.md)에서 확인한 뒤 다른 화면에 적용합니다.

UI UX Pro Max, Vercel, getdesign.md에서 유용한 방법을 선별해 연결했습니다. [출처와 적용 범위](skills/ui-craft-bundle/references/sources.md).

## 로컬에서 평가하고 발전시키기

[로컬 평가·개선 게이트](skills/ui-craft-bundle/references/local-learning.md)는 공통 배포 스킬을 보존하면서 프로젝트별로 조건부 보조 규칙을 발전시킵니다. 외부 패키지가 필요 없는 Python CLI를 `ui-craft-bundle`에 포함했습니다.

`사용 증거 → 개선 후보 → 같은 조건의 비교 → 회귀·다른 사례 검증 → 로컬 채택 → 문제 발생 시 이전 호환본 복귀`

- **개선과 통과를 구분합니다.** 기존·후보가 모두 통과하면 `no-change`입니다. 실제 개선과 필수 검사 보존이 확인되어야 채택할 수 있습니다.
- **각 프로젝트가 독립적입니다.** 저장 위치는 `.lutriva/local/`이며 설치 디렉터리·다른 프로젝트·다른 사용자에게 자동으로 규칙을 퍼뜨리지 않습니다.
- **후보와 계획을 고정합니다.** 적용 범위를 정해 비교하고, 적격 후보를 명시적으로 채택하거나 되돌립니다. 기반·정책·활성 세대가 달라지면 새 후보로 평가해야 합니다.

[CLI 안내](skills/ui-craft-bundle/references/local-learning-cli.md)에 `init`, `propose`, `evaluate`, `promote`, `rollback`, `status`, `context` 명령을 정리했습니다. 현재 `reviewed-local` 절차는 제출 기록·증거 해시·반복 개선·회귀 검사·별도 전이 fixture·신고한 실행 수와 시간을 확인합니다. 관찰의 진실성이나 검토자 독립성까지 인증하지는 않습니다. `context`가 반환한 규칙은 과업과 함께 명시적으로 제공해야 합니다.

모델 실행, 자동 관찰·채택, 호스트 지침 주입, 권한으로 강제한 실험 격리는 아직 구현하지 않았습니다. [확장 구현 계약](skills/ui-craft-bundle/references/local-learning-contract.md)에서 현재 수동 CLI와 이후 자동화 범위를 구분합니다.

## 결과까지 확인합니다

2.1의 제한된 비교에서 **관찰된 회귀는 없었습니다.** 기존 지침과 새 지침을 적용한 결과 모두 브라우저 동작 8개와 화면·키보드 검수를 통과했습니다. 단일 사례로 전반적인 UI 품질 향상을 입증한 것은 아닙니다. [검증 기록](docs/verification.md).

소스에는 [행동 사례 계약 22개](evals/skill-cases.json), 결함을 심은 작은 UI, 외부 브라우저 검사, 결과 비교기가 있습니다. 사례 형식 검증과 실제 에이전트 실행 평가는 구분합니다. 유지보수자는 [평가 절차와 실제 실행 기록](https://github.com/ch4570/lutriva/blob/main/evals/README.md)을 참고하세요. 평가 개발 도구는 설치되는 스킬에서 제외합니다.

<details>
<summary>기여자용 검사와 ZIP 내보내기</summary>

소스 체크아웃에서 실행합니다.

```sh
python3 -m unittest discover -s tests -q
npm test
npm run check
python3 scripts/export_bundle.py --output dist/lutriva-2.4.0.zip
npm pack --dry-run
```

배포 파일을 의도적으로 수정했다면 `python3 scripts/update_manifest.py`로 해시를 갱신하고 검토한 뒤 다시 검사합니다. 내보내기는 검증을 통과한 설치기·스킬·사용 안내를 새 ZIP으로 만듭니다. Git 메타데이터, 개발 스크립트, 테스트는 넣지 않습니다.

선택 도구인 `scripts/run_browser_checks.mjs`에는 기존 Chrome과 Node 22 이상이 필요합니다. 새 패키지를 설치하지 않습니다. npm 게시 절차는 `docs/npm-release.md`에 있습니다.

</details>

## 프로젝트 안내

[이름과 아트워크](docs/naming.md) · [변경 이력](CHANGELOG.md) · [검증 기록](docs/verification.md) · [MIT 라이선스](LICENSE)

직접 작성한 지침과 코드는 MIT로 제공합니다. 배너의 생성 기록은 [assets/README.md](docs/assets/README.md)에 있습니다. 외부 스킬 원문·폰트·아이콘은 포함하지 않습니다. 패키지 형식은 [Agent Skills 명세](https://agentskills.io/specification)를 참고합니다.
