(async () => {
  const parameters = new URLSearchParams(location.search);
  const language = parameters.get('lang') === 'en' ? 'en' : 'ko';
  const copy = await (await fetch('locales/' + language + '.json')).json();
  const records = parameters.get('empty') === '1' ? [] : ['배송 안내', '교환 절차', '정기 배송 일정'];
  const query = document.getElementById('query');
  const interpolate = text => text.replaceAll('{query}', query.value);
  function render() {
    const matches = records.filter(title => title.includes(query.value));
    document.getElementById('results').replaceChildren(...matches.map(title => {
      const item = document.createElement('li'); item.textContent = title; return item;
    }));
    document.getElementById('count').textContent = matches.length + '개 자료';
    const empty = document.getElementById('empty');
    empty.hidden = matches.length > 0;
    const title = document.getElementById('empty-title');
    title.textContent = interpolate(records.length ? copy.empty_title : copy.never_title);
    title.setAttribute('aria-label', interpolate(records.length ? copy.empty_name : copy.never_title));
    document.getElementById('empty-body').textContent = interpolate(records.length ? copy.empty_body : copy.never_body);
    empty.dataset.state = records.length ? 'no-match' : 'never-populated';
  }
  query.addEventListener('input', render);
  render();
  document.documentElement.dataset.ready = 'true';
})();
