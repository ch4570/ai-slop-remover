# Cycle 6 최종 아카이브 독립 검토

검토자: `/root/cycle6_archive_review`, 2026-09-09 KST. 검토한 문서·보존 자료·별도 재실행 사이에 남은 필수 문서 수정 사항을 발견하지 못했다. 한글 CSV 파일명의 추출 표현 차이는 최초 실패를 보존하고 최종 소스 기록에 명시했다. 이는 제품 결함이나 아카이브 내용 손상을 입증하는 실패가 아니다.

이번 검토는 기존 제품 판정의 범위와 증거 보존을 확인한다. 두 원래 검수의 제한된 제품 `pass`는 320×800 조건의 실제 포커스 가장자리 회귀를 없애지 않는다. 새 스킬 버전 비교·반복 실험·사용자 연구를 실행하지 않았으므로 일반적인 스킬 향상도 주장하지 않는다.

## 압축과 추출본 무결성

검토 대상은 저장소의 `evals/records/2026-09-08-feedback-loop/cycle-6.tar.gz`와 `cycle-6-inventory.json`이다.

- 압축: 4,454,143바이트, SHA-256 `b7b2f938a9c60d138a6d56d82e96115153550f3185a306c3f1cc2ea00a0a57e4`.
- 목록: 66,476바이트, SHA-256 `f036a673a59adf50283121b8616ef30095e02209c83cea6ea99a2049a8ddd892`.
- 저장소의 기존 엄격 검사기를 변경 없이 실행해 exit 0 / `verified`, schema 1의 정확한 일반 파일 393개·11,170,827바이트를 확인했다. tar 내부 경로와 inventory의 원시 문자열·크기·해시 대조가 통과했다.

실제 명령은 저장소 루트에서 `python3 -B scripts/check_evidence_archive.py evals/records/2026-09-08-feedback-loop/cycle-6-inventory.json evals/records/2026-09-08-feedback-loop/cycle-6.tar.gz`였다. 결과는 `archive-verification.json`에 있다. 검증 후 새 `/tmp/lutriva-cycle6-final-review-kkVkw8/extracted`에 해제했다.

최초 파일시스템 원시 경로 대조는 exit 1이었다. inventory의 NFC `개인 메모.csv` 두 이름이 macOS의 `readdir`에서 NFD `개인 메모.csv`로 반환되어 누락 2개/추가 2개로 잡혔다. 나머지 경로와 내용 불일치는 없었다. 이 원시 결과는 `extraction-before.json`에 그대로 보존했다. 압축·원본·추출 파일이나 저장소 검사기를 수정하지 않았다.

별도 감사 스크립트에 명시적 NFC 경로 대조와 정규화 충돌 거부를 적용했다. 충돌은 0개이며 두 별칭 외의 차이는 없다. 재실행 전후 각각 393개 파일의 NFC 경로·크기·SHA-256이 inventory와 일치했다. 추출 트리의 원시 경로·크기·해시 자체도 전후 동일했다. 두 관계를 구분하며, 추출본과 inventory의 원시 파일명 문자열까지 같다고 주장하지 않는다.

`extraction-before-nfc.json`, `extraction-after-nfc.json`, `extraction-comparison.json`은 전후 전체 목록과 별칭, 압축·inventory·Chrome 실행 파일 해시 보존을 기록한다. Chrome 실행 파일의 해시 보존은 전체 앱 번들 또는 네트워크 활동 감사가 아니다. 원래 자료 9개 디렉터리 및 8개 단일 파일도 추출본과 다시 대조했다. 보존된 밀도 입력 83개·306,313바이트, 문구 입력 81개·312,867바이트는 각각 frozen과 같으며 양쪽 스킬 65개와 harness는 Git `59c22c39ed441bb97252f523bdb03b8f2e67106e`의 실제 바이트와 같다.

## 추출한 휴대용 진단의 실제 재실행

추출 루트에서 다음 세 명령을 서로 다른 새 출력에 실행했고 모두 exit 0이었다. 원래 절대 경로를 가진 blind 수집기는 실행하지 않았다.

```sh
node arrow-diagnostic/recheck-arrow-portable.mjs density-input /tmp/lutriva-cycle6-final-review-kkVkw8/arrow-replay
node copy-parent/check-copy-states.mjs copy-input/baseline /tmp/lutriva-cycle6-final-review-kkVkw8/copy-baseline
node copy-parent/check-copy-states.mjs copy-input/release /tmp/lutriva-cycle6-final-review-kkVkw8/copy-release
```

Arrow 수집기의 exit 0은 복구 단언이 아니므로 별도 `verify-replay.mjs`에서 원시 필드를 검사했다. 원본 진단·압축 안 portable 검증·이번 재실행 모두 각 조건의 `recoveryObserved` 7개가 true다. 각 단계에서 버튼 좌표와 computed outline 3px + offset 2px로 네 변을 다시 계산했고 기록된 여유·전체 포함 판정과 일치했다.

| 이번 재실행 조건 | scrollLeft 전→후 / 최대 | 외곽선 오른쪽 여유 전→후 |
| --- | --- | --- |
| 결과 M-101, 320×800 | 338→353 / 353 | −8.1875→+6.8125px |
| 결과 긴 이름 M-103, 320×800 | 1224→1239 / 1239 | −7.953125→+7.046875px |
| 원본 M-101, 320×864 | 338→353 / 353 | −8.1875→+6.8125px |

복구 후 네 변의 여유는 모두 0 이상이다. 긴 이름 M-103의 아래 여유는 4.25px다. 선택 행·결과 문구·`:focus-visible`이 유지되고, 각 조건에서 trusted ArrowRight keydown/keyup 한 쌍과 `keyCode:39`를 확인했다. 25개 target guard 모두 safe이며, 캡처 직전/직후 측정도 같다. 원본·압축 안 portable·이번 실행의 전체 단계별 측정/이벤트 배열이 정확히 같다. 세 실행 묶음 모두 예외 0, 입력 전체 해시 보존, 각 조건의 Browser.getVersion 전후 동일을 확인했다.

이번 실제 브라우저는 Chrome/152.0.7977.83, revision `@79460ebecaa5625e57a5fb679a735659e73dc687`, V8 15.2.124.21, Node v26.8.1, macOS arm64다. Arrow 조건은 DPR 1, `mobile:false`, 요소별 computed CSS 글자 두 배이며 OS 크기·페이지 zoom 검사가 아니다.

문구 부모 어댑터는 원본/결과 모두 정확히 20개 pass, collectionErrors 0이며 Browser.getVersion 전후 .83이다. 이 어댑터는 DOM `.value/.checked/.click()`과 320×900 `mobile:true`, Blob `response.text()`를 사용한다. 다운로드 링크를 누르지 않았고 20개에는 예외 검사 하나가 포함된다. false cloud/all-device 문구를 가진 원본도 이 상태 검사를 통과하므로 문장 의미의 정확성 점수로 읽을 수 없다. 저장소의 전체 테스트나 원래 blind 28조건/38검사를 이번에 다시 실행한 것은 아니다.

`replay-assertions.json`의 134/134는 위 원본 자료 대조·입력/Git 무결성·원본/portable/replay 복구 측정·부모 상태 결과·밀도 false 분류를 확인하는 감사 단언 수다. 134개의 독립 제품 과업이나 새로운 blind 검수 점수가 아니다.

## CSV와 원래 결과의 범위

별도 하위 바이트 검토 `/root/cycle6_archive_review/copy_bytes_scope`가 원본과 추출본의 실제 CSV, 수집기, JSON을 직접 읽어 기대값을 재구성했다. 그 보고서와 raw JSON도 이 최종 검토에서 읽었다. 원본과 추출본의 두 실제 CSV는 각각 168바이트, UTF-8 BOM `efbbbf`, SHA-256 `4cd715a7864f9666193242193f6190dc5f403c24a24b45bf2360fad49ea7c495`로 같다. 긴 제목에 내부 ASCII 큰따옴표가 없어 이 다운로드에서는 doubling을 자극하지 않았다.

release 마지막 22번째 검사는 `수요일 "프로젝트" 회의, 준비물 확인`을 다시 저장한 뒤 미저장 편집값과 구분하여 생성한 추가 Blob을 검사한다. doubling 기대값의 재구성은 84바이트 / SHA-256 `9023c175170d6d4d7dc3bc20b91db8b654b7429b4e03bb14165c92fafc466477`이며 원시 Blob 해시와 같다. doubling 없는 82바이트 반대 기대값은 `ae7a1e495aa398e5516b8569cbb0490776b1e3788e489ccdacd098509e325946`으로 다르다. 당시 transient Blob을 이번에 다시 얻은 것이 아니라 기록된 바이트 assertion과 해시를 오프라인 재구성한 대조다. 그 Blob의 두 번째 실제 다운로드는 없다.

원래 문구 수집기의 baseline 16/16, release 22/22와 별도 runtimeExceptions 0을 확인했다. 결과 전용 6개 때문에 전후 점수 향상으로 세지 않는다. 부모의 최초 CSV 해석과 철회 기록은 모두 보존됐다. 현재 문서가 실제 다운로드와 추가 Blob을 구분한 설명은 증거와 맞는다.

밀도 `checks.json`도 직접 재집계하여 506개·488 true·18 false를 확인했다. false는 공통 390px 포커스 포함 12개, 결과 320px 확대 조건의 오른쪽 잘림 2개, 최초 wheel 관찰 4개다. 이전 Tab→Shift+Tab 실패는 별도 경로이며 후속 ArrowRight 성공으로 지워지지 않는다. master 390px 보충 실행은 wheel로 먼저 복구한 뒤 ArrowRight를 보냈으므로 방향키 단독 효과의 근거가 아니다. 원문의 애매한 가장자리/방향키 표현은 소스 요약에서 이 범위로 한정된다.

## 직접 연 화면과 문서 대조

이번 Arrow 재실행의 세 조건 각각 `*-before-arrow.png`, `*-after-arrow.png`, 총 viewport PNG 6개를 직접 열었다. 세 쌍 모두 오른쪽 외곽선의 초기 잘림과 복구 후 네 변 노출을 확인했고 버튼 문구·선택 상태는 유지됐다. `copy-release/save-error-320.png`와 `copy-release/export-ready-320.png`도 직접 열었다. 긴 오류 안내가 카드 안에 줄바꿈되고 준비 문구·다운로드 링크가 서로 겹치지 않았다. 이 두 이미지는 full-page 캡처이며 키보드 포커스나 viewport 전체 포함의 근거로 세지 않는다. 정확한 8개 목록은 `visual-review.json`에 있다. 원래 검수자의 27개/25개 이미지 개수에 더하지 않는다.

현재 `docs/verification.md`, `manifest.json`, records README와 최종 `cycle-6.md`를 대조했다. 마지막 파일은 15,176바이트 / SHA-256 `12089fe1faf0351ae370cbb6fd9fed51e02ec784974a482ad7de8e6437f09328`이며 동시 작성 중의 초기 지문과 구분했다. docs/verification.md의 실제 SHA-256 `2ddc5c487cf77c4601667d098b2be04a234ec57dd9b2d707bff5e33ca39d77d1`은 manifest와 같다. 제한된 제품 pass, 남은 회귀, 상태 검사와 의미 판정, 스킬 향상 미입증, Unicode 추출 차이, 이번 재실행의 정확한 범위가 구분돼 있다.

보존된 repository-checks 및 별도 post-archive npm 로그의 20/20·정적 check 결과도 읽었다. 이번 검토자가 해당 npm 검사를 새로 실행했다고 주장하지 않는다. 저장소 `git diff --check`는 이번 읽기 전용 검토에서도 exit 0이었다.

## 원시 자료와 한계

최종 검토 원시는 `/tmp/lutriva-cycle6-final-review-kkVkw8/`에 있다: `archive-verification.json`, `extraction-command.json`, 최초 실패 `extraction-before.json`, NFC 전후 목록, `extraction-comparison.json`, 세 `*-command.json`, `replay-assertions.json`, `visual-review.json`, `arrow-replay/`, `copy-baseline/`, `copy-release/`와 감사 스크립트다. 하위 바이트 검토는 `/tmp/lutriva-cycle6-byte-scope-audit-YMvwJZ/`의 `REPORT.md`, `raw-checks.json`, `archive-checks.json`, 두 검증 스크립트다. 이 최종 보고서·새 원시 로그·재실행 자료는 검토 대상 tar 밖에 생성했다.

저장소·제품·원래 보고서·추출 증거를 수정하거나 설치·전역 설정 변경·업데이트 UI 조작·사용자 프로필 연결·외부 쓰기·커밋·푸시를 하지 않았다. 기존 Chrome의 새 임시 프로필/로컬 서버만 사용했다. 프로필과 target guard가 네트워크 또는 업데이트의 완전한 격리를 보장하지 않는다. 파일 일치는 증거 의미의 진실성이나 대화 문맥의 독립성을 인증하지 않는다. 물리 기기·다른 브라우저·OS/페이지 zoom·IME·스크린리더·전체 WCAG·원격 CI는 이 검토 범위 밖이다.
