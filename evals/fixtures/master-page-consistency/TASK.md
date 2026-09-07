# 주문 비교 화면의 밀도 예외

$ui-visual-refine 브랜드와 공통 토큰을 유지하면서 주문 비교 화면만 더 많은 행을 볼 수 있도록 밀도를 높여 주세요. 기본 주문 화면은 기존 기준을 유지합니다.

제품 루트는 `product/`입니다. `compare.css`의 `.comparison-table th, .comparison-table td` 규칙에 있는 `padding-block` 값만 현재 16px에서 8~12px 사이의 정수 px로 줄일 수 있습니다. 새 선택자·선언·파일, 공통 tokens.css/components.css, master.html, 데이터·행 동작과 TASK 수정은 범위 밖입니다.

`DESIGN.md`의 `<!-- comparison-exception:start -->`와 `<!-- comparison-exception:end -->` 사이도 수정할 수 있습니다. 이 구역에 예외의 이유, 적용 페이지·선택자, 실제 적용한 규칙을 하나의 CSS 코드 블록으로 기록하세요. 나머지 디자인 기준은 유지합니다.

`master.html`과 `compare.html`을 함께 확인하고 좁은 화면의 행 동작과 키보드 포커스를 확인하세요. 도구로 확인하지 못한 부분은 최종 답변에 미검증으로 남깁니다.
