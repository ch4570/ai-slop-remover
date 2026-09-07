document.getElementById('order-search').addEventListener('input', event => {
  for (const row of document.querySelectorAll('tbody tr')) row.hidden = !row.dataset.search.includes(event.target.value);
});
for (const button of document.querySelectorAll('[data-order]')) button.addEventListener('click', () => {
  document.getElementById('detail').textContent = button.dataset.order + ' 상세를 확인 중입니다.';
});
