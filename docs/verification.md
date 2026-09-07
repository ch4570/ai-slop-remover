# 검증 범위

검증일: 2026-09-07. 원본은 `47a1fdd`, 작업 브랜치는 `feature/ai-slop-skill-set`이다.

## 실행 결과

| 검사 | 결과 | 확인한 범위 |
| --- | --- | --- |
| 변경 전 회귀 테스트 | 18개 통과 | 원본 설치기의 dry-run·설치·재설치·보존·거부 계약 |
| 최종 `python3 -m unittest discover -s tests -q` | 63개 통과 | schema 1 API, schema 2, 의존성, 사전 충돌, 파일·mtime 보존, 해시·경로·심볼릭 링크·메타데이터 경계 |
| `python3 scripts/update_manifest.py --check` | 통과 | 배포 파일 목록과 SHA-256 |
| `python3 scripts/check_package.py` | 통과 | 7개 스킬 메타데이터, KB 라우팅, 배포·설치 상대 링크, 12개 사례 계약, Python 문법 |
| 설치된 공식 `quick_validate.py` | 7개 통과 | SKILL.md 형식 및 이름·설명; 별도로 openai.yaml 파싱과 호출명 확인 |
| NVIDIA SkillEvaluator 0.2.1 Tier 1 | 7개 통과, exit 0 | schema·PII·license·unicode·quality·lint, 보고서 overall_status=passed |
| 실제 ZIP 내보내기 및 해제 | 통과 | manifest와 파일 목록 일치, Git·OMX·개발 도구·Finder 파일 제외 |
| ZIP → 임시 Codex/Claude 프로젝트 | 모두 통과 | 각 7개 스킬 dry-run·설치·동일 재설치, 프로젝트 지침 파일 무변경 |
| `git diff --check` | 통과 | 공백 오류 |

공식 validator는 이미 설치된 SkillEvaluator 환경의 PyYAML을 사용했다. 프로젝트에 의존성을 추가하지 않았다. SkillEvaluator 원본 보고서는 로컬 임시 경로 `agentlab-skillevaluator.MFmKx8/<skill>/`에 생성했으며 배포 파일에 넣지 않았다.

정적 평가에는 권장 섹션명, 추가 metadata, 설명 길이, LICENSE 위치 등에 관한 비차단 권고가 남았다. 실제 절차·예시·제약은 본문과 연결된 참조에 있고, 메타데이터는 `name`·`description` 계약을 유지한다. 기존 `verification.md`의 템플릿 링크도 실제 배포·설치 경로 검사로 확인했다. 권고 점수는 실제 UI 품질 측정치가 아니며 점수를 올리려고 중복 섹션을 추가하지 않았다.

## 증거의 한계

행동 사례 JSON 검증은 사례 계약의 구조 검증이다. 실제 에이전트가 제품 화면을 수정하는 실행 평가는 별도이며 이번 작업에 제품 UI 구현은 포함되지 않는다. 설치 복사 결과를 런타임 발견, 스킬 실행, 실제 UI 개선 효과로 보고하지 않는다.

- 실제 호스트의 스킬 발견·실행과 제품 UI 전후 비교, 브라우저/기기 E2E는 미실행이다.
- Tier 2/3, 전용 보안 스캐너, 성능·접근성 적합성 평가는 미실행이다. Tier 1을 완전한 보안 감사로 해석하지 않는다.
- 설치기의 파일 시스템 경쟁 상태와 설치 중 강제 종료 복구는 검증하지 않았다. 여러 스킬 설치는 사전 충돌 검사를 제공하며 전체 작업의 원자성을 보장하지 않는다. 중단 후에는 오류 원인을 확인하고 재실행한다.
- 별도 formatter·type checker가 구성되어 있지 않아 Python 문법·실행 회귀 테스트로 검증했다.
