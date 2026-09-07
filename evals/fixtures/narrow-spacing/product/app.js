const field = document.getElementById('name');
const status = document.getElementById('status');
field.value = localStorage.getItem('display-name') || '민지';
document.getElementById('settings').addEventListener('submit', event => {
  event.preventDefault();
  const button = document.getElementById('save');
  button.disabled = true;
  status.dataset.state = 'saving';
  status.textContent = '저장 중입니다.';
  setTimeout(() => {
    localStorage.setItem('display-name', field.value);
    status.dataset.state = 'success';
    status.textContent = '변경 사항을 저장했습니다.';
    button.disabled = false;
  }, 30);
});
