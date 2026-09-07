for (const button of document.querySelectorAll('[data-order]')) button.addEventListener('click', () => {
  document.getElementById('detail').textContent = button.dataset.order + ' 주문을 선택했습니다.';
});
