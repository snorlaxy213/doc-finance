(() => {
  'use strict';

  const state = { items: [], catalog: null };
  const queryInput = document.querySelector('#query');
  const rootFilter = document.querySelector('#rootFilter');
  const sortOrder = document.querySelector('#sortOrder');
  const resetButton = document.querySelector('#resetFilters');
  const catalogList = document.querySelector('#catalogList');
  const resultSummary = document.querySelector('#resultSummary');
  const loadError = document.querySelector('#loadError');

  const normalize = (value) => String(value || '').trim().toLocaleLowerCase('zh-CN');

  function dateLabel(isoDate, precision = 'minute') {
    if (!isoDate) return '时间待核实';
    const date = new Date(isoDate);
    if (Number.isNaN(date.getTime())) return '时间待核实';
    const options = { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' };
    if (precision !== 'day') Object.assign(options, { hour: '2-digit', minute: '2-digit', hour12: false });
    return new Intl.DateTimeFormat('zh-CN', options).format(date);
  }

  function selectedItems() {
    const query = normalize(queryInput.value);
    const root = rootFilter.value;
    const sort = sortOrder.value;
    const items = state.items.filter((item) => {
      const matchesQuery = !query || normalize(item.searchText).includes(query);
      const matchesRoot = root === 'all' || item.root === root;
      return matchesQuery && matchesRoot;
    });

    return items.sort((left, right) => {
      if (sort === 'title') return left.title.localeCompare(right.title, 'zh-CN');
      if (sort === 'code') return left.code.localeCompare(right.code, 'zh-CN');
      return (Date.parse(right.modifiedAt) || 0) - (Date.parse(left.modifiedAt) || 0) || right.code.localeCompare(left.code);
    });
  }

  function createReportCard(item) {
    const article = document.createElement('article');
    article.className = 'report-row';
    const content = document.createElement('div');
    content.className = 'report-content';
    const heading = document.createElement('h3');
    const link = document.createElement('a');
    link.href = item.href;
    link.textContent = item.company || item.title;
    link.setAttribute('aria-label', `阅读报告：${item.title}`);
    const code = document.createElement('span');
    code.className = 'report-code';
    code.textContent = item.code;
    heading.append(link, code);
    const title = document.createElement('p');
    title.className = 'report-title';
    title.textContent = item.title;
    content.append(heading, title);
    const date = document.createElement('time');
    date.className = 'report-date';
    if (item.modifiedAt) date.dateTime = item.modifiedAt;
    date.textContent = dateLabel(item.modifiedAt, item.timePrecision);
    date.title = '报告生成时间（北京时间）';
    article.append(content, date);
    return article;
  }

  function render() {
    const items = selectedItems();
    catalogList.replaceChildren();
    catalogList.setAttribute('aria-busy', 'false');
    resultSummary.textContent = `共 ${items.length} / ${state.items.length} 份报告`;

    if (!items.length) {
      const template = document.querySelector('#emptyState');
      catalogList.append(template.content.cloneNode(true));
      return;
    }
    items.forEach((item) => catalogList.append(createReportCard(item)));
  }

  function populateRoots(items) {
    const roots = new Map(items.map((item) => [item.root, item.rootLabel]));
    roots.forEach((label, value) => {
      const option = document.createElement('option');
      option.value = value;
      option.textContent = label;
      rootFilter.append(option);
    });
  }

  function resetFilters() {
    queryInput.value = '';
    rootFilter.value = 'all';
    sortOrder.value = 'newest';
    render();
    queryInput.focus();
  }

  async function loadCatalog() {
    try {
      const response = await fetch('data/catalog.json', { cache: 'no-cache' });
      if (!response.ok) throw new Error(`catalog request failed: ${response.status}`);
      const catalog = await response.json();
      if (!Array.isArray(catalog.items)) throw new Error('catalog items missing');
      state.catalog = catalog;
      state.items = catalog.items;
      populateRoots(state.items);
      rootFilter.closest('.field').hidden = new Set(state.items.map(item => item.root)).size <= 1;
      render();
    } catch (error) {
      console.error(error);
      catalogList.setAttribute('aria-busy', 'false');
      loadError.hidden = false;
    }
  }

  queryInput.addEventListener('input', render);
  rootFilter.addEventListener('change', render);
  sortOrder.addEventListener('change', render);
  resetButton.addEventListener('click', resetFilters);
  document.querySelector('#searchForm').addEventListener('submit', (event) => event.preventDefault());
  loadCatalog();
})();
