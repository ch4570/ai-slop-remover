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
  if (!['query', 'notes', 'count', 'title', 'body', 'editor', 'save', 'fail-save', 'status'].every(searchEditorCheck.el)) {
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

async function evaluateSearchEditor(snapshot, onCheck = () => {}) {
  const { el, input, wait, saved, record, sameNotes, select, update } = searchEditorCheck;
  const checks = [];
  // Publish only completed records, before a later operation can throw or navigate.
  const collect = check => { checks.push(check); onCheck(check); };
  const initialHistory = history.length;
  input('query', '배'); input('query', '배송'); input('query', '배송 확인');
  // Let this fixture's short async input work settle before checking the final URL.
  await wait(150);
  collect(record('search-matches', el('notes').children.length === 1 && el('notes').textContent.includes('배송 확인'), {
    query: el('query').value, matches: el('notes').textContent,
  }));
  const query = observeQueryState(snapshot, '배송 확인');
  collect(record('query-history', history.length === initialHistory && query.pass, {
    before: initialHistory, after: history.length, settleMs: 150, ...query.observed,
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
  collect(record('failed-save-draft', selectionFound && failure.title === '실패해도 남아야 하는 초안' && failure.body === '저장 재시도에 사용할 내용' && failure.storageUnchanged, failure));
  collect(record('failed-save-feedback', selectionFound && failure.state === 'error' && !failure.disabled && /실패|못|오류/.test(failure.feedback), failure));
  const afterFailure = saved();
  collect(record('failed-save-storage', selectionFound && failure.storageUnchanged && sameNotes(snapshot, afterFailure), {
    expected: snapshot, persisted: afterFailure, storageUnchanged: failure.storageUnchanged, selectionFound,
  }));
  el('fail-save').checked = false;
  if (selectionFound) el('save').click();
  await wait(150);
  const persisted = saved();
  collect(record('retry-persists', selectionFound && sameNotes(expected, persisted) && !el('save').disabled, {
    targetId: 1, expected, persisted, selectionFound, feedback: el('status').textContent, disabled: el('save').disabled,
  }));
  return { checks, expected };
}

// Match listed records through their unique seeded titles and opened editor
// values. The fixture exposes no note IDs in the DOM; do not read app globals.
function observeQueryState(snapshot, query) {
  const { el, select, sameNotes } = searchEditorCheck;
  const expected = snapshot.filter(note => `${note.title} ${note.body}`.includes(query.trim()));
  const listed = [...el('notes').querySelectorAll('button')].map(button => button.textContent);
  const opened = expected.map(note => {
    const selectionFound = select(note);
    return { id: note.id, selectionFound,
      title: selectionFound ? el('title').value : null,
      body: selectionFound ? el('body').value : null };
  });
  const urlQuery = new URL(location.href).searchParams.get('q') || '';
  const inputQuery = el('query').value;
  const countText = el('count').textContent;
  const count = countText.match(/\d+/);
  const reportedCount = count ? Number(count[0]) : null;
  return {
    pass: urlQuery === query && inputQuery === query && listed.length === expected.length &&
      reportedCount === expected.length && opened.every(note => note.selectionFound) && sameNotes(expected, opened),
    observed: { expectedQuery: query, expected, urlQuery, inputQuery, listed, opened, countText, reportedCount },
  };
}

async function prepareSearchHistory() {
  const { input, wait } = searchEditorCheck;
  input('query', '배송 확인');
  await wait(150);
  // Only evaluator-owned entries on this synthetic origin are traversed. Starting
  // with three states makes missing restoration visible in both directions.
  return ['', '고객', '배송 확인'].map((query, entry) => {
    const url = new URL(location.href);
    if (query) url.searchParams.set('q', query); else url.searchParams.delete('q');
    const state = { searchEditorEntry: entry };
    if (entry === 0) history.replaceState(state, '', url);
    else history.pushState(state, '', url);
    return { query, url: url.href, entry };
  });
}

async function evaluateHistoryTraversal(id, snapshot, direction, destinations) {
  const { wait, record } = searchEditorCheck;
  const navigations = [];
  for (const destination of destinations) {
    const started = performance.now();
    const navigation = await new Promise(resolve => {
      const finish = observed => {
        clearTimeout(timer);
        window.removeEventListener('popstate', onPopstate);
        resolve({ ...observed, elapsedMs: performance.now() - started });
      };
      const onPopstate = event => {
        if (!event.isTrusted) return;
        const completed = location.href === destination.url && event.state?.searchEditorEntry === destination.entry;
        finish({ completed, trustedPopstate: true, eventUrl: location.href, eventState: event.state,
          ...(completed ? {} : { reason: 'History reached an unexpected entry.' }) });
      };
      const timer = setTimeout(() => finish({ completed: false, trustedPopstate: false,
        reason: 'Trusted popstate observation timeout after 1000ms.' }), 1000);
      window.addEventListener('popstate', onPopstate);
      try {
        if (direction === 'back') history.back(); else history.forward();
      } catch (error) {
        finish({ completed: false, trustedPopstate: false, reason: String(error) });
      }
    });
    // Observe after the entire popstate dispatch, including the app's handlers.
    await wait(50);
    try {
      const state = observeQueryState(snapshot, destination.query);
      navigations.push({ direction, destination, ...navigation, stateMatches: state.pass, ...state.observed });
    } catch (error) {
      navigations.push({ direction, destination, ...navigation, stateMatches: null, observationError: String(error) });
    }
  }
  const failed = navigations.some(step => step.stateMatches === false || (step.trustedPopstate && !step.completed));
  const complete = navigations.length > 0 && navigations.every(step => step.completed && step.stateMatches);
  const check = record(id, complete, { navigations });
  if (!failed && !complete) {
    check.status = 'not-run';
    check.reason = 'History observation incomplete: ' + [...new Set(navigations
      .flatMap(step => [step.reason, step.observationError]).filter(Boolean))].join(' ');
  }
  return check;
}

function observeQueryRestoration(id, snapshot, query) {
  const state = observeQueryState(snapshot, query);
  return searchEditorCheck.record(id, state.pass, state.observed);
}

async function evaluateOrdinarySave(snapshot, onCheck = () => {}) {
  const { el, input, wait, saved, record, sameNotes, select, update } = searchEditorCheck;
  const checks = [];
  const collect = check => { checks.push(check); onCheck(check); };
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
  collect(record('composition-enter', selectionFound && submissions === 0 && localStorage.getItem('haneul-eval-notes') === beforeComposition, {
    syntheticComposition: true, selectionFound, submissions, storageUnchanged: localStorage.getItem('haneul-eval-notes') === beforeComposition,
  }));
  el('editor').removeEventListener('submit', observeSubmit, true);
  const expected = update(snapshot, 2, '저장 성공 확인', '두 번째 메모의 새 내용');
  input('title', '저장 성공 확인');
  input('body', '두 번째 메모의 새 내용');
  if (selectionFound) el('save').click();
  await wait(150);
  const persisted = saved();
  collect(record('ordinary-save', selectionFound && sameNotes(expected, persisted) && !el('save').disabled, {
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
