/* Evaluator-owned: run only in an isolated synthetic fixture origin.
   The driver seeds storage and reloads between save modes; see evals/README.md.
   Synthetic events verify app handlers, not OS-level IME behavior. */
const searchEditorCheck = {
  el: id => document.getElementById(id),
  wait: ms => new Promise(resolve => setTimeout(resolve, ms)),
  input(id, value) {
    const field = document.getElementById(id);
    field.value = value;
    field.dispatchEvent(new Event('input', { bubbles: true }));
  },
  saved() {
    try { return JSON.parse(localStorage.getItem('haneul-eval-notes') || 'null'); }
    catch { return null; }
  },
  sameNotes(expected, persisted) {
    return Array.isArray(persisted) && persisted.length === expected.length &&
      new Set(persisted.map(note => note?.id)).size === expected.length &&
      expected.every(note => persisted.some(item => item?.id === note.id &&
        item.title === note.title && item.body === note.body));
  },
  select(note) {
    const buttons = [...document.getElementById('notes').querySelectorAll('button')]
      .filter(button => button.textContent.includes(note.title));
    if (buttons.length !== 1) return false;
    buttons[0].click();
    return true;
  },
  update(snapshot, id, title, body) {
    return snapshot.map(note => note.id === id ? { ...note, title, body } : { ...note });
  },
  record(id, pass, observed) {
    return { id, kind: 'behavior', status: pass ? 'pass' : 'fail',
      evidence: { text: JSON.stringify(observed) } };
  },
};

// Seed before loading the app again, so failed saves exercise existing data.
// Expected records live in the evaluator/driver, never in candidate app globals.
function seedSearchEditor() {
  if (!['query', 'notes', 'title', 'body', 'editor', 'save', 'fail-save', 'status'].every(searchEditorCheck.el)) {
    throw new Error('Fixture DOM contract is missing; behavior checks were not run.');
  }
  const snapshot = [
    { id: 1, title: '배송 확인', body: '금요일 배송 일정을 확인합니다.' },
    { id: 2, title: '고객 요청', body: '긴 한국어 안내 문구를 검토합니다.' },
    { id: 3, title: '다음 회의', body: '다음 주 회의 내용을 정리합니다.' },
  ];
  localStorage.setItem('haneul-eval-notes', JSON.stringify(snapshot));
  return snapshot;
}

async function evaluateSearchEditor(snapshot) {
  const { el, input, wait, saved, record, sameNotes, select, update } = searchEditorCheck;
  const checks = [];
  const initialHistory = history.length;
  input('query', '배'); input('query', '배송'); input('query', '배송 확인');
  checks.push(record('search-matches', el('notes').children.length === 1 && el('notes').textContent.includes('배송 확인'), {
    query: el('query').value, matches: el('notes').textContent,
  }));
  checks.push(record('query-history', history.length === initialHistory && new URL(location.href).searchParams.get('q') === '배송 확인', {
    before: initialHistory, after: history.length, urlQuery: new URL(location.href).searchParams.get('q'),
  }));
  input('query', '');
  const selectionFound = select(snapshot.find(note => note.id === 1));
  const expected = update(snapshot, 1, '실패해도 남아야 하는 초안', '저장 재시도에 사용할 내용');
  input('title', '실패해도 남아야 하는 초안');
  input('body', '저장 재시도에 사용할 내용');
  el('fail-save').checked = true;
  const beforeFailure = localStorage.getItem('haneul-eval-notes');
  if (selectionFound) el('save').click();
  await wait(150);
  const failure = {
    title: el('title').value, body: el('body').value, feedback: el('status').textContent,
    state: el('status').dataset.state, disabled: el('save').disabled, selectionFound,
    storageUnchanged: localStorage.getItem('haneul-eval-notes') === beforeFailure,
  };
  checks.push(record('failed-save-draft', selectionFound && failure.title === '실패해도 남아야 하는 초안' && failure.body === '저장 재시도에 사용할 내용' && failure.storageUnchanged, failure));
  checks.push(record('failed-save-feedback', selectionFound && failure.state === 'error' && !failure.disabled && /실패|못|오류/.test(failure.feedback), failure));
  const afterFailure = saved();
  checks.push(record('failed-save-storage', selectionFound && failure.storageUnchanged && sameNotes(snapshot, afterFailure), {
    expected: snapshot, persisted: afterFailure, storageUnchanged: failure.storageUnchanged, selectionFound,
  }));
  el('fail-save').checked = false;
  if (selectionFound) el('save').click();
  await wait(150);
  const persisted = saved();
  checks.push(record('retry-persists', selectionFound && sameNotes(expected, persisted) && !el('save').disabled, {
    targetId: 1, expected, persisted, selectionFound, feedback: el('status').textContent, disabled: el('save').disabled,
  }));
  return { checks, expected };
}

async function evaluateOrdinarySave(snapshot) {
  const { el, input, wait, saved, record, sameNotes, select, update } = searchEditorCheck;
  const checks = [];
  const selectionFound = select(snapshot.find(note => note.id === 2));
  let submissions = 0;
  const observeSubmit = () => { submissions += 1; };
  el('editor').addEventListener('submit', observeSubmit, true);
  const beforeComposition = localStorage.getItem('haneul-eval-notes');
  input('title', '한글 조합 중');
  el('title').dispatchEvent(new CompositionEvent('compositionstart', { bubbles: true }));
  el('title').dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', isComposing: true, bubbles: true, cancelable: true }));
  el('title').dispatchEvent(new CompositionEvent('compositionend', { data: '중', bubbles: true }));
  await wait(150);
  checks.push(record('composition-enter', selectionFound && submissions === 0 && localStorage.getItem('haneul-eval-notes') === beforeComposition, {
    syntheticComposition: true, selectionFound, submissions, storageUnchanged: localStorage.getItem('haneul-eval-notes') === beforeComposition,
  }));
  el('editor').removeEventListener('submit', observeSubmit, true);
  const expected = update(snapshot, 2, '저장 성공 확인', '두 번째 메모의 새 내용');
  input('title', '저장 성공 확인');
  input('body', '두 번째 메모의 새 내용');
  if (selectionFound) el('save').click();
  await wait(150);
  const persisted = saved();
  checks.push(record('ordinary-save', selectionFound && sameNotes(expected, persisted) && !el('save').disabled, {
    targetId: 2, expected, persisted, selectionFound, feedback: el('status').textContent, disabled: el('save').disabled,
  }));
  return { checks, expected };
}

// Dispatch a real browser Enter key between these functions. A synthetic DOM
// KeyboardEvent cannot exercise native implicit form submission correctly.
function prepareOrdinaryEnter(snapshot) {
  const { el, input, select, update } = searchEditorCheck;
  const selectionFound = select(snapshot.find(note => note.id === 3));
  const expected = update(snapshot, 3, 'Enter로 저장한 메모', '세 번째 메모의 새 내용');
  input('title', 'Enter로 저장한 메모');
  input('body', '세 번째 메모의 새 내용');
  if (selectionFound) el('title').focus();
  return { expected, selectionFound };
}
function observeOrdinaryEnter({ expected, selectionFound }) {
  const { el, saved, record, sameNotes } = searchEditorCheck;
  const persisted = saved();
  const disabled = el('save').disabled;
  return record('ordinary-enter', selectionFound && sameNotes(expected, persisted) && !disabled, {
    browserKeyboard: selectionFound, targetId: 3, expected, persisted, selectionFound, disabled,
  });
}

// Run after an actual reload, with the pre-reload expectation held by the driver.
function observeReload(id, expected) {
  const { el, saved, select, sameNotes, record } = searchEditorCheck;
  const persisted = saved();
  const listedCount = el('notes').querySelectorAll('button').length;
  const opened = expected.map(note => {
    const selectionFound = select(note);
    return { id: note.id, selectionFound,
      title: selectionFound ? el('title').value : null,
      body: selectionFound ? el('body').value : null };
  });
  const restored = opened.every(note => note.selectionFound) && sameNotes(expected, opened);
  return record(id, sameNotes(expected, persisted) && listedCount === expected.length && restored, {
    expected, persisted, listedCount, opened,
  });
}
