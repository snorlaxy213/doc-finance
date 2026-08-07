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
  const publicationStatus = document.querySelector('#publicationStatus');
  const disclaimerText = document.querySelector('#disclaimerText');

  const normalize = (value) => String(value || '').trim().toLocaleLowerCase('zh-CN');

  function dateLabel(isoDate) {
    if (!isoDate) return '日期未提供';
    const date = new Date(isoDate);
    return Number.isNaN(date.getTime()) ? isoDate.slice(0, 10) : date.toLocaleDateString('zh-CN');
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
      return String(right.modifiedAt).localeCompare(String(left.modifiedAt));
    });
  }

  function createReportCard(item) {
    const article = document.createElement('article');
    article.className = 'report-card';

    const meta = document.createElement('div');
    meta.className = 'report-meta';
    [item.rootLabel, item.code, item.version].forEach((label, index) => {
      const badge = document.createElement('span');
      badge.className = `badge${index === 2 ? ' latest' : ''}`;
      badge.textContent = label;
      meta.append(badge);
    });

    const heading = document.createElement('h3');
    const titleLink = document.createElement('a');
    titleLink.href = item.href;
    titleLink.textContent = item.title;
    titleLink.setAttribute('aria-label', `打开报告：${item.title}`);
    heading.append(titleLink);

    const date = document.createElement('p');
    date.className = 'report-date';
    date.textContent = `源文件更新：${dateLabel(item.modifiedAt)}`;

    const summary = document.createElement('p');
    summary.className = 'summary';
    summary.textContent = item.summary;

    const openLink = document.createElement('a');
    openLink.className = 'open-report';
    openLink.href = item.href;
    openLink.textContent = '阅读报告 →';
    openLink.setAttribute('aria-label', `阅读报告：${item.title}`);

    article.append(meta, heading, date, summary, openLink);
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
      disclaimerText.textContent = catalog.disclaimer || disclaimerText.textContent;
      publicationStatus.textContent = `目录更新于 ${dateLabel(catalog.generatedAt)} · 已公开 ${state.items.length} 份最新报告`;
      render();
    } catch (error) {
      console.error(error);
      catalogList.setAttribute('aria-busy', 'false');
      loadError.hidden = false;
      publicationStatus.textContent = '公开目录暂时无法加载。';
    }
  }

  queryInput.addEventListener('input', render);
  rootFilter.addEventListener('change', render);
  sortOrder.addEventListener('change', render);
  resetButton.addEventListener('click', resetFilters);
  document.querySelector('#searchForm').addEventListener('submit', (event) => event.preventDefault());
  loadCatalog();
})();
