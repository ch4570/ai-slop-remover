const storageKey = 'haneul-eval-notes';
const initialNotes = [
  { id: 1, title: '배송 확인', body: '금요일 배송 일정을 확인합니다.' },
  { id: 2, title: '고객 요청', body: '긴 한국어 안내 문구를 검토합니다.' },
  { id: 3, title: '다음 회의', body: '다음 주 회의 내용을 정리합니다.' },
];
const el = id => document.getElementById(id);
let notes = JSON.parse(localStorage.getItem(storageKey) || 'null') || initialNotes;
let selectedId = 1;
let pending = false;
el('query').value = new URL(location.href).searchParams.get('q') || '';

function showStatus(state, message) {
  el('status').dataset.state = state;
  el('status').textContent = message;
}
function openNote(id) {
  selectedId = id;
  const note = notes.find(item => item.id === id);
  el('title').value = note.title;
  el('body').value = note.body;
  showStatus('idle', '');
}
function renderNotes() {
  const query = el('query').value.trim();
  const matches = notes.filter(note => `${note.title} ${note.body}`.includes(query));
  el('notes').replaceChildren();
  for (const note of matches) {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = note.title;
    button.addEventListener('click', () => openNote(note.id));
    item.append(button);
    el('notes').append(item);
  }
  el('count').textContent = matches.length ? `${matches.length}개 메모` : '일치하는 메모가 없습니다. 검색어를 바꿔보세요.';
}
el('query').addEventListener('input', () => {
  const url = new URL(location.href);
  if (el('query').value) url.searchParams.set('q', el('query').value);
  else url.searchParams.delete('q');
  history.pushState({}, '', url);
  renderNotes();
});
window.addEventListener('popstate', () => {
  el('query').value = new URL(location.href).searchParams.get('q') || '';
  renderNotes();
});
el('title').addEventListener('keydown', event => {
  if (event.key === 'Enter') {
    event.preventDefault();
    el('editor').requestSubmit();
  }
});
el('editor').addEventListener('submit', async event => {
  event.preventDefault();
  if (pending) return;
  pending = true;
  el('save').disabled = true;
  const draft = { id: selectedId, title: el('title').value, body: el('body').value };
  const shouldFail = el('fail-save').checked;
  showStatus('pending', '저장 중…');
  try {
    await new Promise(resolve => setTimeout(resolve, 30));
    if (shouldFail) throw new Error('연습용 저장 실패');
    const updated = notes.map(note => note.id === draft.id ? draft : note);
    localStorage.setItem(storageKey, JSON.stringify(updated));
    notes = updated;
    renderNotes();
  } catch {
    openNote(selectedId);
  } finally {
    pending = false;
    el('save').disabled = false;
    showStatus('success', '메모를 저장했습니다.');
  }
});
openNote(selectedId);
renderNotes();
