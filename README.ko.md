# UI Craft Bundle 1.0.0

앱·웹 화면의 AI 티를 줄이고, 사용자가 조작하면 실제 결과가 바뀌는 UI를 만들기 위한 통합 스킬입니다. 디자인 방향 → 인터랙션 상태 → 플랫폼 구현 → 실제 화면 검수를 하나의 작업 흐름으로 연결합니다.

외부 스킬 원문을 합친 배포본이 아니라, 아래 공개 스킬과 공식 가이드를 검토하고 별도로 작성한 통합 번들입니다. 외부 패키지, API 키, Figma, MCP 서버 없이 지침을 사용할 수 있습니다. 실제 앱 실행·화면 캡처에는 해당 프로젝트의 개발 및 테스트 환경이 필요합니다.

## 어떤 스킬을 추가하면 좋은가

| 용도 | 추천 | 적용 시점 |
| --- | --- | --- |
| AI 티 제거·시각적 완성도 | [Impeccable](https://github.com/pbakaus/impeccable) | 선택적 디자인 주력 |
| 더 가벼운 디자인 지침 | [Anthropic frontend-design](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) | Impeccable의 대안 |
| 웹 접근성·폼·포커스 검토 | [Vercel web-design-guidelines](https://github.com/vercel-labs/agent-skills/tree/main/skills/web-design-guidelines) | 웹 검수 시 |
| React/Next 성능 | [vercel-react-best-practices](https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices) | 해당 스택의 성능 개선 시 |
| Compose 등 여러 스택 참조 | [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | 필요할 때 참조 검색 |

추천 시작점은 이 번들 하나입니다. 디자인 전문 스킬을 더한다면 Impeccable 또는 frontend-design 하나를 선택하세요. 여러 스킬의 색상·글꼴·모션 지침을 동시에 강제하면 서로 충돌할 수 있습니다. 기존 브랜드와 프로젝트 요구사항을 우선합니다. 위 스킬은 자동 설치되지 않습니다.

## 포함된 모듈

| 모듈 | 달라지는 작업 방식 |
| --- | --- |
| Art direction | 실제 사용 목적에 맞게 구조·밀도·타이포·위계를 선택 |
| Interaction design | 검색·필터·수정·저장·취소의 상태 변화와 실패 복구 구현 |
| Motion | 상태를 설명하는 모션, 반복 입력과 모션 축소 설정 처리 |
| Web | 모바일 레이아웃, 키보드·포커스, 폼·드래그 대체 조작 |
| Native | Compose/Android, iOS, React Native, Flutter별 적용 경계 |
| Verification | 화면을 실제로 열어 보고, 주요 조작 결과를 확인한 증거 기록 |
| Sources | 추천 upstream 스킬, 적용 조건, 공식 문서 링크 |

스킬은 필요한 모듈만 읽습니다. 버튼 간격 하나를 고치는 요청에 전체 리디자인이나 불필요한 테스트 문서 작성을 요구하지 않습니다.

## 로컬 프로젝트 설치

Python 3.9 이상이 필요합니다. ZIP을 풀고 `install.py`가 있는 폴더에서 실행합니다. 경로는 본인 프로젝트로 바꾸세요.

Codex:

```bash
python3 install.py --repo "/path/to/project" --agent codex --dry-run
python3 install.py --repo "/path/to/project" --agent codex
```

설치 위치: `프로젝트/.agents/skills/ui-craft-bundle/`.

Claude Code:

```bash
python3 install.py --repo "/path/to/project" --agent claude
```

설치 위치: `프로젝트/.claude/skills/ui-craft-bundle/`.

다른 에이전트나 사용자 공용 위치를 쓰려면, 해당 도구가 지원하는 **정확한 스킬 폴더**를 확인한 뒤 지정하세요. 이 옵션은 설치 경로만 정하며, 모든 에이전트의 자동 인식을 보장하지 않습니다.

```bash
python3 install.py --dest "/absolute/path/to/skills/ui-craft-bundle"
```

설치기는 파일 해시를 확인하고, 이미 동일하게 설치되어 있으면 아무것도 변경하지 않습니다. 기존 내용이 다르거나 사용자가 수정한 폴더는 덮어쓰지 않습니다. 교체가 필요하면 기존 폴더를 직접 검토·백업하고 다른 경로로 옮긴 뒤 새로 설치하세요. `AGENTS.md`, `CLAUDE.md`, 프로젝트 코드, 전역 설정을 수정하지 않으며 네트워크 다운로드도 하지 않습니다.

직접 설치하려면 ZIP 안의 `skills/ui-craft-bundle` 폴더를 도구의 스킬 경로로 복사할 수 있습니다. 설치기 사용 시 무결성 검사를 함께 수행합니다. 해시는 패키지의 우발적 변경을 확인하는 수단이며 배포자 서명은 아닙니다.

Codex 경로는 [OpenAI 문서](https://learn.chatgpt.com/docs/build-skills), Claude Code 경로는 [공식 문서](https://code.claude.com/docs/en/skills)를 기준으로 확인했습니다. ChatGPT의 개인 스킬 설치와 로컬 프로젝트 설치는 별개입니다.

## 바로 쓰는 프롬프트

### 기존 웹앱 리디자인

```text
$ui-craft-bundle
이 프로젝트의 [화면 이름]을 개선해줘.
사용자는 [누구]이고 핵심 작업은 [무엇]이야.
기존 스택과 기능을 유지하고, 현재 화면을 먼저 확인해.
콘텐츠 구조와 정보 위계를 잡고, 주요 조작이 실제 결과로 이어지게 구현해.
모바일·키보드·오류/빈 상태를 확인하고,
직접 열어 본 화면과 실행한 인터랙션의 검수 결과를 알려줘.
```

### Kotlin/Compose 앱

```text
$ui-craft-bundle
Kotlin/Jetpack Compose로 만든 일정 앱의 일정 편집 화면을 개선해줘.
핵심 작업은 시간 수정, 항목 순서 변경, 저장, 취소야.
현재 디자인 시스템과 네비게이션을 유지해.
드래그 이외의 이동 조작도 제공하고, 키보드가 올라와도 편집과 저장이 가능하게 해.
저장 실패 시 입력값을 보존해. 실제 에뮬레이터 검증이 불가능하면 미검증으로 명시해.
```

### 제한된 수정

```text
$ui-craft-bundle
현재 화면에서 모바일 검색 필터와 빈 결과 상태만 개선해줘.
브랜드 색상과 나머지 레이아웃은 유지하고, 관련 동작만 확인해.
```

### 디자인 전문 스킬과 함께 사용

```text
$ui-craft-bundle
Impeccable이 설치되어 있으면 시각적 방향과 critique에 활용해.
이 프로젝트의 브랜드와 요구사항을 우선하고,
인터랙션 상태 구현과 검수는 UI Craft Bundle의 흐름으로 진행해.
추가 스킬이 없어도 현재 도구로 작업을 완료해.
```

호스트가 `$이름` 호출을 지원하지 않으면 스킬 선택기에서 선택하거나 “UI Craft Bundle을 사용해서…”라고 요청하세요. Claude Code에서는 설치 후 `/ui-craft-bundle`로 호출할 수 있습니다.

## 완료 결과에서 확인할 것

- 화면의 주 작업을 실제로 완료할 수 있는가?
- 필터·탭·저장 버튼이 데이터/상태를 바꾸는가?
- 실패 후 재시도·취소·입력 보존이 가능한가?
- 좁은 화면과 키보드/터치에서도 필수 조작에 접근할 수 있는가?
- “구현함”, “빌드 통과”, “이미지 확인”, “동작 테스트”를 구별해서 보고했는가?

스킬만으로 특정 미감이나 품질이 보장되지는 않습니다. 구체적인 핵심 작업과 참고 화면을 주고, 실제 실행 환경에서 검수할수록 판단 근거가 좋아집니다. 이 번들은 실패를 숨기거나 점수만 매겨 완료하는 대신, 확인한 결과와 미검증 범위를 남기도록 설계했습니다.

## 배포 범위

검토 기준일: 2026-09-07. 새로 작성된 번들 파일은 `assets/LICENSE`의 MIT 조건으로 이용·수정·재배포할 수 있습니다. upstream 원문·코드·아이콘·폰트는 포함하지 않습니다. 외부 프로젝트를 나중에 직접 포함한다면 해당 시점의 라이선스·고지와 revision을 별도로 관리해야 합니다.
