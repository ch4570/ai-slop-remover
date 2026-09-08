원본 블라인드 검수입니다. X=후보, Y=기준이며 아래 이미지 경로는 압축의 `color-layout-v1/blind-review/` 기준입니다. 원래 링크를 포함한 문서도 압축에 보존했습니다.

지정된 폴더 안의 BRIEF·계획, 원본/X/Y 스크린샷 **58장**을 직접 열고 두 제품의 HTML/CSS와 공통 동작 소스를 대조했습니다. 새 브라우저·검사 스크립트는 실행하지 않았습니다.

Y는 넓은 화면의 여섯 주문 동시 비교와 문제 중심 상세 순서가 강점입니다. X는 모바일의 단일 스크롤 흐름과 조금 큰 목록 글자가 강점입니다. 두 버전 모두 원본보다 개요 면적을 줄여 업무 영역을 먼저 보이게 했습니다. 조건 전체를 포괄하는 단일 승자는 정하지 않았습니다.

| 사전 항목 | X/Y 판단 |
|---|---|
| brand | 동률 |
| color_roles | 동률 |
| task_hierarchy | Y 우위 |
| comparison | 동률 |
| group_alignment | Y 소폭 우위 |
| narrow_access | X 소폭 우위 |

**brand**

원본: 주황색 m 마크, 굵은 어두운 브랜드명과 따뜻한 회색 바탕이 원본의 식별 요소다. 원본의 넓은 파스텔 요약·행 배경은 마크보다 화면 면적을 많이 차지한다.

X: 기존 m·마루 배송을 유지하고 흰색/따뜻한 회색 작업 면 위에 주황색 마크·작업 버튼을 남겼다. 원본 브랜드를 알아볼 수 있다.

Y: 같은 마크와 중성 바탕을 유지하고 상세 패널 상단에도 주황 선을 썼다. X보다 로고/브랜드 글자는 작지만 세 viewport에서 이름과 마크가 온전히 보인다.

판단: 둘 다 브랜드를 유지하면서 의미 없는 파스텔 면적을 줄였다. 식별력의 우열을 가를 이미지 근거는 부족하다.

이미지 근거: `original/wide-initial-viewport.png`, `version-x/screenshots/wide-initial-viewport.png`, `version-y/screenshots/wide-initial-viewport.png`, `version-x/screenshots/narrow-floor-initial-viewport.png`, `version-y/screenshots/narrow-floor-initial-viewport.png`.

**color_roles**

원본: 보라/녹색/베이지 행 배경이 주문 상태와 일관되게 대응하지 않는다. 선택 테두리·확인 필요 배지·문제 박스·완료 버튼이 주황 계열을 공유한다. 완료의 녹색과 초점의 검은 외곽선은 원본에서도 구분된다.

X: 실행은 진한 주황+흰 글씨, 선택은 옅은 주황 면+왼쪽 선, 확인 필요는 황갈색 배지, 완료는 녹색 배지와 '처리 완료됨' 문구로 나뉜다. 문제 박스의 황갈색 선·제목도 경고 의미를 보탠다. 필터 선택은 흰 면과 테두리로 표시된다.

Y: 실행·선택·대기·완료의 역할은 X와 비슷하게 분리된다. 현재 필터의 검은 면/흰 글씨는 X보다 눈에 띈다. 문제 박스는 중성 회색으로 읽히며 상태는 별도 배지가 전달한다. 세 크기에서 완료 버튼의 검은 초점 링이 명확하다.

판단: Y는 필터 선택과 하단 알림의 눈에 띄는 정도에서, X는 문제 박스의 경고 표지와 약간 큰 목록 글자에서 장점이 있다. 역할 분리 전체는 동률로 본다.

결함·한계:

- 공통: 저장 성공과 실패 피드백은 각 버전에서 동일한 외형을 사용한다. X는 흰 테두리 박스, Y는 주황 왼쪽 선의 하단 고정 박스다. 성공/실패는 문장을 읽어야 구분되며 저장 실패 전용 색·아이콘·제목은 없다.
- X: 완료된 주문에서도 수량 확인 박스의 황갈색 경고 외형은 유지된다. 녹색 완료 배지·설명과 함께 읽어야 해결 상태를 알 수 있다.
- 공통: 선택은 색과 왼쪽 선으로 표시되고 별도의 '선택됨' 문구는 없다. 스크린샷에서 텍스트가 읽히는 것과 수치 대비 기준 충족은 별개이며 대비값은 측정하지 않았다.

이미지 근거: `original/wide-initial-viewport.png`, `version-x/screenshots/wide-selected-viewport.png`, `version-y/screenshots/wide-selected-viewport.png`, `version-x/screenshots/wide-completed-viewport.png`, `version-y/screenshots/wide-completed-viewport.png`, `version-x/screenshots/narrow-floor-storage-error-viewport.png`, `version-y/screenshots/narrow-floor-storage-error-viewport.png`, `version-x/screenshots/narrow-floor-keyboard-resolve-viewport.png`, `version-y/screenshots/narrow-floor-keyboard-resolve-viewport.png`.

**task_hierarchy**

원본: 넓은 화면에서도 큰 요약 카드 아래 첫 두 주문만 온전히 보이고 완료 버튼은 하단에 걸린다. 390/320 초기 화면은 요약이 대부분을 차지해 주문 행을 읽기 시작하기 어렵다.

X: 요약을 낮은 한 묶음으로 바꿔 wide 초기 화면에서 다섯 주문과 완료 버튼을 보여준다. 390에서는 두 주문 대부분, 320에서는 첫 주문의 내용이 보인다. 모바일 목록-상세 이동 링크가 추가됐다.

Y: wide 초기 화면에 여섯 주문과 선택 상세·완료 버튼 전체가 보인다. 상세는 주문 ID 다음에 확인할 문제와 지시를 먼저 배치한다. 390에서는 세 번째 주문의 시작까지, 320에서는 두 번째 주문의 일부까지 보이며 두 크기에서 상세 이동 링크가 있다.

판단: Y는 화면 상단의 개요를 더 짧게 하고 확인 문제를 상세 상단에 배치하여, 무엇을 확인할지와 다음 실행을 함께 찾기 쉽게 만든다. 이는 화면 배치 관찰이며 처리 시간 단축을 측정한 결과는 아니다.

결함·한계:

- X: 320에서는 새로고침이 별도 줄로 내려가고 출고 예정도 행의 두 번째 줄로 내려가 첫 화면의 주문 노출량이 Y보다 적다.
- Y: 모바일 상세를 앞당기는 데 내부 목록 스크롤이 사용된다. 첫 화면의 밀도 이점과 여섯 주문 탐색의 부담을 함께 봐야 한다.

이미지 근거: `original/wide-initial-viewport.png`, `original/narrow-initial-viewport.png`, `original/narrow-floor-initial-viewport.png`, `version-x/screenshots/wide-initial-viewport.png`, `version-y/screenshots/wide-initial-viewport.png`, `version-x/screenshots/narrow-floor-initial-viewport.png`, `version-y/screenshots/narrow-floor-initial-viewport.png`, `version-y/screenshots/narrow-selected-viewport.png`.

**comparison**

원본: 여섯 주문의 확인 항목·택배사·출고 시각은 존재하지만 행마다 큰 간격과 배경색이 달라 연속 비교가 길어진다. 320 전체 이미지에서 일부 출고 시각은 날짜와 시간이 두 줄로 갈라진다.

X: wide/390 전체 목록에서 같은 필드가 같은 열에 반복되고 여섯 주문의 의미를 보존한다. 320은 확인 항목·택배사 두 열 아래 출고 예정 한 줄로 일관되게 재배치한다. 글자와 날짜는 읽기 편하지만 목록이 길어진다.

Y: wide에서는 여섯 기록이 한 viewport에 들어가 비교에 유리하다. 모바일도 확인 항목·택배사·출고 예정 세 열을 유지하며 긴 '배송 요청 확인', '묶음 배송 확인'을 생략하지 않는다. 다만 목록 높이가 제한돼 초기 전체 페이지 이미지에도 첫 두 행과 세 번째 행 일부만 보인다.

판단: wide 비교는 Y 우위, 모바일에서 여섯 주문을 하나의 연속 페이지로 훑는 방식은 X 우위다. 전체 항목은 동률로 판정한다. Y에서 숨겨진 데이터가 삭제됐다고 판단하지 않는다.

결함·한계:

- Y: 390/320의 initial-full에는 2403행이 필드 위에서 잘리고 2404~2406은 내부 스크롤 아래에 있다. keyboard-resolve-full에서는 반대로 2404 일부와 2405~2406이 보인다. 목록 안의 별도 이동 없이는 여섯 기록을 훑을 수 없다.
- Y: 모바일 목록 필드 값은 CSS상 12px, 라벨은 11px로 X의 13px/12px보다 작다. 밀도 이점과 작은 글자 부담이 함께 있다.
- X: 320의 출고 시각 별도 줄은 읽기와 일관성을 확보하지만 여섯 행 비교에 필요한 세로 공간을 늘린다.

이미지 근거: `original/wide-initial-full.png`, `original/narrow-floor-initial-full.png`, `version-x/screenshots/wide-initial-full.png`, `version-x/screenshots/narrow-initial-full.png`, `version-x/screenshots/narrow-floor-initial-full.png`, `version-y/screenshots/wide-initial-viewport.png`, `version-y/screenshots/narrow-initial-full.png`, `version-y/screenshots/narrow-floor-initial-full.png`, `version-y/screenshots/narrow-keyboard-resolve-full.png`, `version-y/screenshots/narrow-floor-keyboard-resolve-full.png`.

**group_alignment**

원본: 확인 항목·택배사·출고 예정이 반복되지만 넓은 카드 간격과 가변적인 필드 위치 때문에 같은 열을 계속 따라가기 어렵다. 상세의 긴 문제 문장은 원본 320에서 어절 중간 줄바꿈이 보인다.

X: 목록을 같은 구분선과 열 폭으로 정리하고, 수령인/지역과 확인 필드를 안정적으로 묶었다. 상세의 라벨/값 정렬, 구분선, 문제 박스 간격이 일관된다. 좁은 상세에서 긴 지시도 박스 안에 온전히 줄바꿈된다.

Y: 주문 ID·상태·수령인 묶음과 비교 필드가 짧은 행 안에 반복된다. 목록 제목·필터·행이 하나의 패널에 묶이고, 상세는 문제/지시 → 사실 정보 → 구분선 → 실행으로 읽는 순서가 뚜렷하다. 넓은 상세 너비 덕분에 긴 문제 문장도 덜 잘게 나뉜다.

판단: 두 버전 모두 원본보다 반복 정렬이 안정적이다. Y는 목록 전체 묶음과 상세의 문제-정보-실행 구획이 더 명료해 소폭 우위로 본다.

결함·한계:

- Y: 모바일 내부 스크롤의 위·아래 경계가 행의 ID 또는 필드 중간을 자르므로, 그 경계에서는 한 주문 묶음이 시각적으로 끊긴다.
- X: wide에서 상태 배지가 주문 ID와 행의 양 끝에 떨어져 있다. Y의 인접한 ID·배지에 비해 둘을 묶어 읽는 거리가 길다.

이미지 근거: `original/wide-selected-viewport.png`, `original/narrow-floor-keyboard-resolve-viewport.png`, `version-x/screenshots/wide-selected-viewport.png`, `version-y/screenshots/wide-selected-viewport.png`, `version-x/screenshots/narrow-floor-selected-viewport.png`, `version-y/screenshots/narrow-floor-selected-viewport.png`, `version-y/screenshots/narrow-floor-selected-full.png`.

**narrow_access**

원본: 390/320 모두 선택 상세·완료 버튼은 스크롤된 이미지에 온전히 나온다. 그러나 초기에는 목록 위에 긴 요약이 있고 목록과 상세 사이의 직접 이동 링크가 보이지 않는다.

X: 두 크기에서 필터·첫 주문·상세 이동 링크가 초기 화면에 보인다. 전체 목록은 단일 페이지 흐름이고 '주문 목록으로' 링크가 상세 상단에 있다. 선택 상세·완료·오류·초점 이미지는 양옆 내용 잘림 없이 읽힌다. 320의 더 긴 목록은 이동 링크로 보완하는 구조다.

Y: 두 크기에서 필터와 주문이 X보다 일찍 보이고 상세/완료 버튼 이미지도 읽힌다. 320에서 날짜/시각을 한 줄로 유지한다. 다만 페이지와 내부 목록을 각각 스크롤하는 구조이며 목록 복귀 링크가 상세 맨 아래에 있다.

판단: X는 단일 스크롤 목록, 조금 큰 목록 글자, 상세 진입 직후 보이는 목록 복귀 링크로 탐색이 더 예측 가능하다. 좁은 화면의 접근 방식에 한정해 소폭 우위다. Y의 더 빠른 상세 노출을 무시하는 절대적 우위는 아니다.

결함·한계:

- Y: 초기 전체 이미지와 selected-full에서 내부 목록 경계가 행 중간을 자른다. 가는 스크롤바를 알아차리고 목록 안을 별도로 이동해야 한다.
- Y: 복귀 링크의 href는 #order-list여서 소스상 필터 아래 목록으로 향한다. X는 #orders-panel로 향한다. 실제 초점 이전·복귀 후 키보드 순서는 이번 리뷰에서 실행 검증하지 않았다.
- Y: 하단 고정 저장 실패 알림은 390/320 캡처에서 상세 패널 하단 여백 위에 겹치지만 완료 버튼이나 복귀 링크의 글자를 가리지는 않는다. 다른 스크롤 위치의 가림 여부는 미확인이다.
- X: 320에서 완료 후 캡처는 상세 상단의 복귀 링크 일부가 viewport 밖에 있다. 전체 페이지에서는 링크가 존재하며 이것은 이미지의 스크롤 위치에 따른 상단 이탈이지 삭제 증거가 아니다.

이미지 근거: `original/narrow-selected-viewport.png`, `original/narrow-floor-selected-viewport.png`, `version-x/screenshots/narrow-initial-full.png`, `version-x/screenshots/narrow-floor-initial-full.png`, `version-x/screenshots/narrow-floor-selected-viewport.png`, `version-y/screenshots/narrow-selected-full.png`, `version-y/screenshots/narrow-floor-selected-full.png`, `version-y/screenshots/narrow-floor-storage-error-viewport.png`, `version-x/screenshots/narrow-floor-keyboard-resolve-viewport.png`, `version-y/screenshots/narrow-floor-keyboard-resolve-viewport.png`.

**동작·연구와의 경계**

선택 이미지의 MD-260908-2402·수량 확인·6개, 완료 이미지의 처리 완료/처리 완료됨·녹색 표시, 오류 이미지의 저장 실패 문구·확인 필요 상태 유지, keyboard 이미지의 완료 버튼 초점 링을 확인했다.

이 상태들이 렌더링됐다는 관찰을 실제 조작 전 과정의 통과로 환산하지 않았습니다. 클릭·필터·키보드 전체 흐름, 저장/새로고침/재로드 지속성, 링크의 초점 이동, 내부 스크롤 도달성은 이번 리뷰에서 독립 검증하지 않았습니다. X/Y app.js 파일끼리는 `cmp` 결과 동일하지만 원본 app.js가 이 폴더에 없어 원본 대비 불변 계약은 미판정입니다.

scrollWidth/clientWidth는 원본·X·Y 모두 이 리뷰에서 미측정(null)입니다. 캡처에 수평 페이지 잘림이 보이지 않는다는 관찰과 무오버플로 통과를 구분합니다. 텍스트 대비 수치, 스크린리더 전달, 고정 알림의 모든 위치에서의 가림 여부도 미검증입니다. 이미지별 전체 열람 목록과 구조화된 판정은 [review.json](review.json)에 있습니다.

단일 합성 제품의 한 관찰자 시각 판단이다. 독립 사용자 선호, 실제 업무 속도·오류율, 다른 제품 전반의 효과를 입증하지 않는다.
