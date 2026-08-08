import { createClient } from 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.49.1/+esm';

const config = window.PORTFOLIO_SUPABASE_CONFIG || {};
const TABLES = {
  accounts: 'portfolio_accounts',
  positions: 'portfolio_positions',
  closed: 'portfolio_closed_positions',
  watchlist: 'portfolio_watchlist',
  cashflows: 'portfolio_cashflows',
  snapshots: 'portfolio_asset_snapshots',
  audit: 'portfolio_audit_logs'
};
const state = { client: null, email: localStorage.getItem('portfolio.email') || '', accountId: '', accounts: [], positions: [], closed: [], watchlist: [], cashflows: [], snapshots: [], audit: [], activeTab: 'positions' };
const $ = (selector) => document.querySelector(selector);
const byId = (id) => document.getElementById(id);
const authGate = byId('authGate');
const portfolioApp = byId('portfolioApp');
const authForm = byId('authForm');
const authEmail = byId('authEmail');
const authPassword = byId('authPassword');
const authError = byId('authError');
const configNotice = byId('configNotice');
const editorDialog = byId('editorDialog');
const editorForm = byId('editorForm');
const editorFields = byId('editorFields');
const editorError = byId('editorError');
const confirmDialog = byId('confirmDialog');
const confirmFields = byId('confirmFields');
const confirmError = byId('confirmError');

function node(tag, options = {}, children = []) {
  const element = document.createElement(tag);
  Object.entries(options).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    if (key === 'className') element.className = value;
    else if (key === 'text') element.textContent = value;
    else if (key === 'htmlFor') element.htmlFor = value;
    else if (key === 'type') element.type = value;
    else if (key === 'value') element.value = value;
    else if (key === 'checked') element.checked = Boolean(value);
    else if (key === 'disabled') element.disabled = Boolean(value);
    else if (key === 'hidden') element.hidden = Boolean(value);
    else if (key.startsWith('on')) element.addEventListener(key.slice(2).toLowerCase(), value);
    else element.setAttribute(key, value);
  });
  children.flat().filter(Boolean).forEach((child) => element.append(typeof child === 'string' ? document.createTextNode(child) : child));
  return element;
}

function amount(value, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return new Intl.NumberFormat('zh-CN', { style: 'currency', currency: 'CNY', currencyDisplay: 'narrowSymbol', minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(parsed);
}

function numeric(value, digits = 2, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return new Intl.NumberFormat('zh-CN', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(parsed);
}

function percent(value, fallback = '—') {
  if (value === null || value === undefined || value === '') return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  return `${(parsed * 100).toFixed(2)}%`;
}

function dateLabel(value, withTime = false) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value).slice(0, withTime ? 16 : 10);
  return withTime ? date.toLocaleString('zh-CN', { hour12: false }) : date.toLocaleDateString('zh-CN');
}

function today() { return new Date().toISOString().slice(0, 10); }
function asNumber(value, fallback = 0) { const parsed = Number(value); return Number.isFinite(parsed) ? parsed : fallback; }
function classForPnl(value) { return asNumber(value) > 0 ? 'positive' : asNumber(value) < 0 ? 'negative' : ''; }
function reportUrl(symbol) { const code = String(symbol || '').match(/\d{6}/)?.[0]; return code ? `../reports/${code}/index.html` : ''; }
function setError(target, message) { target.textContent = message || ''; target.hidden = !message; }
function setStatus(message) { byId('dataAsOf').textContent = message; }

function configured() { return typeof config.url === 'string' && config.url.startsWith('https://') && typeof config.publishableKey === 'string' && config.publishableKey.length > 20; }

function configureAuthForm() {
  const hasEmail = Boolean(state.email);
  byId('emailField').hidden = hasEmail;
  byId('changeEmailButton').hidden = !hasEmail;
  authEmail.required = !hasEmail;
  authEmail.value = hasEmail ? state.email : '';
  byId('authHint').textContent = hasEmail
    ? `当前邮箱：${state.email}。输入密码后才能读取持仓数据。`
    : '持仓数据不会包含在公开页面中。首次使用请验证 Supabase 邮箱与密码。';
  byId('authSubmit').textContent = hasEmail ? '验证密码并打开持仓' : '验证并打开持仓';
}

async function boot() {
  if (!configured()) {
    configNotice.hidden = false;
    authGate.hidden = true;
    return;
  }
  state.client = createClient(config.url, config.publishableKey, { auth: { persistSession: true, autoRefreshToken: false, detectSessionInUrl: false } });
  await state.client.auth.signOut({ scope: 'local' });
  configureAuthForm();
  bindEvents();
}

function bindEvents() {
  authForm.addEventListener('submit', authenticate);
  byId('changeEmailButton').addEventListener('click', () => { localStorage.removeItem('portfolio.email'); state.email = ''; authPassword.value = ''; setError(authError, ''); configureAuthForm(); authEmail.focus(); });
  byId('lockPageButton').addEventListener('click', lockPage);
  byId('accountSelect').addEventListener('change', async (event) => { state.accountId = event.target.value; await refreshData(); });
  byId('addAccountButton').addEventListener('click', () => editAccount());
  byId('addPositionButton').addEventListener('click', () => editPosition());
  byId('updatePricesButton').addEventListener('click', editPrices);
  byId('recordSnapshotButton').addEventListener('click', () => editSnapshot());
  byId('quickSnapshotButton').addEventListener('click', () => editSnapshot());
  byId('addCashflowButton').addEventListener('click', () => editCashflow());
  byId('addWatchlistButton').addEventListener('click', () => editWatchlist());
  byId('exportBackupButton').addEventListener('click', exportBackup);
  byId('importBackupButton').addEventListener('click', () => byId('backupFileInput').click());
  byId('backupFileInput').addEventListener('change', importBackup);
  document.querySelectorAll('.tab-button').forEach((button) => button.addEventListener('click', () => switchTab(button.dataset.tab)));
  byId('closeEditorButton').addEventListener('click', () => editorDialog.close());
  byId('cancelEditorButton').addEventListener('click', () => editorDialog.close());
  byId('closeConfirmButton').addEventListener('click', () => confirmDialog.close());
  byId('cancelConfirmButton').addEventListener('click', () => confirmDialog.close());
}

async function authenticate(event) {
  event.preventDefault();
  setError(authError, '');
  const email = state.email || authEmail.value.trim().toLowerCase();
  const password = authPassword.value;
  if (!email || !password) { setError(authError, '请填写邮箱和密码。'); return; }
  byId('authSubmit').disabled = true;
  try {
    const { error } = await state.client.auth.signInWithPassword({ email, password });
    if (error) throw error;
    state.email = email;
    localStorage.setItem('portfolio.email', email);
    authPassword.value = '';
    authGate.hidden = true;
    portfolioApp.hidden = false;
    byId('lockPageButton').hidden = false;
    await refreshData();
  } catch (error) {
    setError(authError, `验证失败：${error.message || '请检查邮箱、密码和 Supabase 配置。'}`);
  } finally {
    byId('authSubmit').disabled = false;
  }
}

async function lockPage() {
  await state.client.auth.signOut({ scope: 'local' });
  portfolioApp.hidden = true;
  authGate.hidden = false;
  byId('lockPageButton').hidden = true;
  state.accounts = []; state.positions = []; state.closed = []; state.watchlist = []; state.cashflows = []; state.snapshots = []; state.audit = [];
  configureAuthForm();
  authPassword.focus();
}

async function query(table, accountId, order) {
  let request = state.client.from(table).select('*');
  if (accountId) request = request.eq('account_id', accountId);
  if (order) request = request.order(order.column, { ascending: order.ascending, nullsFirst: false });
  const { data, error } = await request;
  if (error) throw error;
  return data || [];
}

async function refreshData() {
  setStatus('正在加载私有持仓数据…');
  try {
    state.accounts = await query(TABLES.accounts, null, { column: 'created_at', ascending: true });
    if (!state.accounts.length) {
      state.accountId = '';
      renderAll();
      setStatus('尚未建立账户。请先新增账户，或按文档运行本地种子工具。');
      return;
    }
    if (!state.accounts.some((account) => account.id === state.accountId)) state.accountId = state.accounts.find((account) => account.is_active)?.id || state.accounts[0].id;
    [state.positions, state.closed, state.watchlist, state.cashflows, state.snapshots, state.audit] = await Promise.all([
      query(TABLES.positions, state.accountId, { column: 'security_name', ascending: true }),
      query(TABLES.closed, state.accountId, { column: 'closed_on', ascending: false }),
      query(TABLES.watchlist, state.accountId, { column: 'review_on', ascending: true }),
      query(TABLES.cashflows, state.accountId, { column: 'occurred_on', ascending: false }),
      query(TABLES.snapshots, state.accountId, { column: 'as_of_at', ascending: false }),
      query(TABLES.audit, state.accountId, { column: 'created_at', ascending: false })
    ]);
    renderAll();
    const latest = state.snapshots[0];
    setStatus(`数据更新时间：${latest ? dateLabel(latest.as_of_at, true) : '尚未记录资产快照'} · 价格与账户数据均为手工维护`);
  } catch (error) {
    setStatus(`加载失败：${error.message || '请检查 Supabase 表结构、RLS 与密码验证。'}`);
  }
}

function activeAccount() { return state.accounts.find((account) => account.id === state.accountId); }
function latestSnapshot() { return state.snapshots[0] || null; }
function portfolioMetrics() {
  const account = activeAccount();
  const latest = latestSnapshot();
  const marketValue = state.positions.reduce((total, row) => total + asNumber(row.quantity) * asNumber(row.current_price), 0);
  const floatingPnl = state.positions.reduce((total, row) => total + (asNumber(row.current_price) - asNumber(row.average_cost)) * asNumber(row.quantity), 0);
  const partialPnl = state.positions.reduce((total, row) => total + asNumber(row.accumulated_realized_pnl), 0);
  const closedPnl = state.closed.reduce((total, row) => total + asNumber(row.realized_pnl), 0);
  const totalAssets = latest ? asNumber(latest.total_assets) : asNumber(account?.initial_net_assets);
  const netCashflow = state.cashflows.reduce((total, row) => total + (row.flow_type === 'deposit' ? asNumber(row.amount) : -asNumber(row.amount)), 0);
  const adjustedPnl = totalAssets - asNumber(account?.initial_net_assets) - netCashflow;
  const plannedLoss = state.positions.reduce((total, row) => total + Math.max(asNumber(row.average_cost) - asNumber(row.stop_loss_price), 0) * asNumber(row.quantity), 0);
  const maxPosition = state.positions.reduce((max, row) => Math.max(max, asNumber(row.quantity) * asNumber(row.current_price)), 0);
  const wins = state.closed.filter((row) => asNumber(row.realized_pnl) > 0).length;
  return { account, latest, marketValue, floatingPnl, partialPnl, closedPnl, realizedPnl: partialPnl + closedPnl, totalAssets, netCashflow, adjustedPnl, plannedLoss, maxPosition, positionPct: totalAssets ? marketValue / totalAssets : 0, maxPositionPct: totalAssets ? maxPosition / totalAssets : 0, winRate: state.closed.length ? wins / state.closed.length : null };
}

function metricCard(label, value, note, tone = '') {
  return node('article', { className: 'metric-card' }, [node('p', { className: 'metric-label', text: label }), node('p', { className: `metric-value ${tone}`, text: value }), node('p', { className: 'metric-note', text: note })]);
}

function renderAll() {
  renderAccounts();
  renderMetrics();
  renderRisk();
  renderPositions();
  renderClosed();
  renderCashflows();
  renderSnapshots();
  renderWatchlist();
  renderAudit();
}

function renderAccounts() {
  const select = byId('accountSelect');
  select.replaceChildren();
  state.accounts.forEach((account) => select.append(node('option', { value: account.id, text: `${account.name}${account.is_active ? '' : '（已停用）'}` })));
  select.value = state.accountId;
}

function renderMetrics() {
  const grid = byId('metricGrid');
  grid.replaceChildren();
  const metric = portfolioMetrics();
  if (!metric.account) { grid.append(metricCard('账户状态', '尚未建立账户', '请新增账户或运行私有种子工具。')); return; }
  const cash = metric.latest ? asNumber(metric.latest.available_cash) : null;
  grid.append(
    metricCard('总资产', amount(metric.totalAssets), `跟踪起点：${metric.account.tracking_started_on}`),
    metricCard('证券市值 / 总仓位', amount(metric.marketValue), percent(metric.positionPct)),
    metricCard('可用资金', cash === null ? '未记录' : amount(cash), metric.latest?.withdrawable_cash === null || metric.latest?.withdrawable_cash === undefined ? '可取资金：未记录' : `可取：${amount(metric.latest.withdrawable_cash)}`),
    metricCard('跟踪期调整收益', amount(metric.adjustedPnl), `净入出金：${amount(metric.netCashflow)}`, classForPnl(metric.adjustedPnl)),
    metricCard('当前浮盈亏', amount(metric.floatingPnl), `含 ${state.positions.length} 只当前持仓`, classForPnl(metric.floatingPnl)),
    metricCard('已实现盈亏', amount(metric.realizedPnl), `清仓 ${state.closed.length} 笔`, classForPnl(metric.realizedPnl)),
    metricCard('清仓胜率', percent(metric.winRate), metric.winRate === null ? '尚无清仓记录' : `清仓总盈亏：${amount(metric.closedPnl)}`, metric.winRate !== null && metric.winRate >= 0.5 ? 'positive' : metric.winRate !== null ? 'negative' : ''),
    metricCard('计划止损损失', amount(metric.plannedLoss), '按已填写止损价与当前数量估算', metric.plannedLoss > 0 ? 'negative' : '')
  );
}

function renderRisk() {
  const metric = portfolioMetrics();
  const strip = byId('riskStrip');
  strip.replaceChildren();
  const concentrationWarning = metric.maxPositionPct > 0.25;
  const plannedLossWarning = metric.totalAssets && metric.plannedLoss / metric.totalAssets > 0.025;
  strip.append(
    node('div', { className: `risk-item ${concentrationWarning ? 'warning' : ''}` }, [node('strong', { text: `最大单股仓位：${percent(metric.maxPositionPct)}` }), node('span', { text: concentrationWarning ? '高于 AGENTS.md 默认单股上限 25%，请检查。' : '默认上限参考 AGENTS.md；具体目标仓位由每只持仓保存。' })]),
    node('div', { className: `risk-item ${plannedLossWarning ? 'warning' : ''}` }, [node('strong', { text: `计划损失：${amount(metric.plannedLoss)}` }), node('span', { text: plannedLossWarning ? '超过总资产 2.5% 的默认计划风险参考值。' : '仅按已填写止损价计算，不代表实际可执行损失。' })]),
    node('div', { className: 'risk-item' }, [node('strong', { text: `手工数据状态：${metric.latest ? '已有快照' : '缺少快照'}` }), node('span', { text: metric.latest ? `最近快照 ${dateLabel(metric.latest.as_of_at, true)}；请按需更新价格和现金。` : '请记录资产快照，账户收益才能反映实际情况。' })])
  );
}

function emptyRow(body, colspan, text) { body.append(node('tr', {}, [node('td', { className: 'empty-cell', colspan, text })])); }
function tableCell(text, className = '') { return node('td', { className, text: String(text ?? '—') }); }
function actionButton(label, handler, danger = false) { return node('button', { type: 'button', className: `action-link${danger ? ' danger' : ''}`, text: label, onClick: handler }); }

function renderPositions() {
  const body = $('#positionsTable tbody'); body.replaceChildren();
  const metric = portfolioMetrics();
  byId('positionSummary').textContent = `${state.positions.length} 只 · 市值 ${amount(metric.marketValue)}`;
  if (!state.positions.length) { emptyRow(body, 8, '暂无当前持仓。'); return; }
  state.positions.forEach((row) => {
    const marketValue = asNumber(row.quantity) * asNumber(row.current_price);
    const pnl = (asNumber(row.current_price) - asNumber(row.average_cost)) * asNumber(row.quantity);
    const pnlPct = asNumber(row.average_cost) ? (asNumber(row.current_price) - asNumber(row.average_cost)) / asNumber(row.average_cost) : null;
    const positionPct = metric.totalAssets ? marketValue / metric.totalAssets : null;
    const report = reportUrl(row.symbol);
    const security = node('td', {}, [node('span', { className: 'table-title', text: row.security_name }), node('span', { className: 'table-subtitle', text: row.symbol }), report ? node('a', { href: report, text: '打开研究报告', target: '_blank', rel: 'noopener', className: 'table-subtitle' }) : null]);
    const targetStop = node('td', {}, [node('span', { text: row.target_position_pct === null ? '目标：—' : `目标：${percent(row.target_position_pct)}` }), node('span', { className: 'table-subtitle', text: row.stop_loss_price === null ? '止损：—' : `止损：${numeric(row.stop_loss_price, 3)}` })]);
    const actions = node('div', { className: 'action-list' }, [actionButton('编辑', () => editPosition(row)), actionButton('卖出/清仓', () => sellPosition(row)), actionButton('删除', () => deletePosition(row), true)]);
    body.append(node('tr', {}, [security, tableCell(`${numeric(row.quantity, 0)} / ${numeric(row.available_quantity, 0)}`, 'numeric'), tableCell(`${numeric(row.average_cost, 3)} / ${numeric(row.current_price, 3)}`, 'numeric'), tableCell(amount(marketValue), 'numeric'), tableCell(`${amount(pnl)}\n${percent(pnlPct)}`, `numeric ${classForPnl(pnl)}`), tableCell(percent(positionPct), 'numeric'), targetStop, node('td', {}, [actions])]));
  });
}

function renderClosed() {
  const body = $('#closedTable tbody'); body.replaceChildren();
  const total = state.closed.reduce((sum, row) => sum + asNumber(row.realized_pnl), 0);
  const wins = state.closed.filter((row) => asNumber(row.realized_pnl) > 0).length;
  byId('closedSummary').textContent = state.closed.length ? `${state.closed.length} 笔 · 胜率 ${percent(wins / state.closed.length)} · ${amount(total)}` : '尚无清仓记录';
  if (!state.closed.length) { emptyRow(body, 8, '暂无清仓记录。完全清仓后会自动生成汇总分析。'); return; }
  state.closed.forEach((row) => {
    const security = node('td', {}, [node('span', { className: 'table-title', text: row.security_name }), node('span', { className: 'table-subtitle', text: row.symbol })]);
    const actions = node('div', { className: 'action-list' }, [actionButton('更正', () => correctClosed(row)), actionButton('恢复为持仓', () => reopenClosed(row), true)]);
    body.append(node('tr', {}, [security, tableCell(dateLabel(row.closed_on)), tableCell(numeric(row.closed_quantity, 0), 'numeric'), tableCell(`${numeric(row.average_cost, 3)} / ${numeric(row.final_sale_price, 3)}`, 'numeric'), tableCell(amount(row.total_sale_proceeds), 'numeric'), tableCell(amount(row.realized_pnl), `numeric ${classForPnl(row.realized_pnl)}`), tableCell(percent(row.return_pct), `numeric ${classForPnl(row.return_pct)}`), node('td', {}, [actions])]));
  });
}

function renderCashflows() {
  const body = $('#cashflowTable tbody'); body.replaceChildren();
  if (!state.cashflows.length) { emptyRow(body, 4, '暂无资金事件。'); return; }
  state.cashflows.forEach((row) => body.append(node('tr', {}, [tableCell(dateLabel(row.occurred_on)), tableCell(row.flow_type === 'deposit' ? '入金' : '出金'), tableCell(amount(row.amount), `numeric ${row.flow_type === 'deposit' ? 'positive' : 'negative'}`), tableCell(row.note || '—')] )));
}

function renderSnapshots() {
  const body = $('#snapshotTable tbody'); body.replaceChildren();
  if (!state.snapshots.length) { emptyRow(body, 5, '暂无资产快照。'); return; }
  state.snapshots.forEach((row) => body.append(node('tr', {}, [tableCell(dateLabel(row.as_of_at, true)), tableCell(amount(row.total_assets), 'numeric'), tableCell(amount(row.securities_value), 'numeric'), tableCell(`${amount(row.available_cash)} / ${amount(row.withdrawable_cash)}`, 'numeric'), tableCell(row.source || 'manual')] )));
}

function statusTag(status) {
  const labels = { watching: '观察', planned: '计划建仓', abandoned: '已放弃' };
  return node('span', { className: `status-tag ${status === 'planned' ? 'planned' : status === 'abandoned' ? 'abandoned' : ''}`, text: labels[status] || status });
}

function renderWatchlist() {
  const body = $('#watchlistTable tbody'); body.replaceChildren();
  if (!state.watchlist.length) { emptyRow(body, 7, '暂无观察股。'); return; }
  state.watchlist.forEach((row) => {
    const report = row.report_url || reportUrl(row.symbol);
    const security = node('td', {}, [node('span', { className: 'table-title', text: row.security_name }), node('span', { className: 'table-subtitle', text: row.symbol })]);
    const actions = node('div', { className: 'action-list' }, [actionButton('编辑', () => editWatchlist(row)), actionButton('转为持仓', () => convertWatchlist(row)), actionButton('删除', () => deleteWatchlist(row), true)]);
    body.append(node('tr', {}, [security, node('td', {}, [statusTag(row.status)]), tableCell(row.buy_low === null && row.buy_high === null ? '—' : `${numeric(row.buy_low, 3)} – ${numeric(row.buy_high, 3)}`), tableCell(row.invalidation_condition || '—'), tableCell(dateLabel(row.review_on)), node('td', {}, [report ? node('a', { href: report, target: '_blank', rel: 'noopener', text: '打开报告' }) : document.createTextNode('—')]), node('td', {}, [actions])]));
  });
}

function renderAudit() {
  const body = $('#auditTable tbody'); body.replaceChildren();
  if (!state.audit.length) { emptyRow(body, 4, '暂无操作日志。'); return; }
  state.audit.slice(0, 100).forEach((row) => body.append(node('tr', {}, [tableCell(dateLabel(row.created_at, true)), tableCell(row.action), tableCell(row.entity_type), tableCell(row.reason || '—')] )));
}

function switchTab(tab) {
  state.activeTab = tab;
  document.querySelectorAll('.tab-button').forEach((button) => { const active = button.dataset.tab === tab; button.classList.toggle('is-active', active); button.setAttribute('aria-selected', String(active)); });
  document.querySelectorAll('.tab-panel').forEach((panel) => { panel.hidden = panel.dataset.panel !== tab; });
}

function fieldDefinition({ key, label, type = 'text', required = false, value = '', hint = '', options = [], full = false, min, max, step, placeholder, readOnly = false }) {
  return { key, label, type, required, value, hint, options, full, min, max, step, placeholder, readOnly };
}

function appendFields(container, fields) {
  container.replaceChildren();
  fields.forEach((field) => {
    const id = `field-${field.key}`;
    const wrapper = node('div', { className: `field${field.full ? ' full-width' : ''}` });
    wrapper.append(node('label', { htmlFor: id, text: field.label }));
    let control;
    if (field.type === 'textarea') control = node('textarea', { id, name: field.key, placeholder: field.placeholder || '', required: field.required, readOnly: field.readOnly });
    else if (field.type === 'select') {
      control = node('select', { id, name: field.key, required: field.required });
      field.options.forEach((option) => control.append(node('option', { value: option.value, text: option.label })));
    } else control = node('input', { id, name: field.key, type: field.type, placeholder: field.placeholder || '', required: field.required, readOnly: field.readOnly, min: field.min, max: field.max, step: field.step });
    if (field.type === 'checkbox') control.checked = Boolean(field.value);
    else control.value = field.value ?? '';
    wrapper.append(control);
    if (field.hint) wrapper.append(node('span', { className: 'field-hint', text: field.hint }));
    container.append(wrapper);
  });
}

function valuesFrom(container) {
  const values = {};
  container.querySelectorAll('[name]').forEach((input) => { values[input.name] = input.type === 'checkbox' ? input.checked : input.value.trim(); });
  return values;
}

function openEditor({ title, description = '', fields, saveLabel = '保存', onSave }) {
  byId('editorTitle').textContent = title;
  byId('editorDescription').textContent = description;
  byId('saveEditorButton').textContent = saveLabel;
  setError(editorError, '');
  appendFields(editorFields, fields);
  editorForm.onsubmit = async (event) => {
    event.preventDefault();
    const saveButton = byId('saveEditorButton');
    saveButton.disabled = true;
    setError(editorError, '');
    try {
      await onSave(valuesFrom(editorFields));
      editorDialog.close();
      await refreshData();
    } catch (error) {
      setError(editorError, error.message || '保存失败。');
    } finally { saveButton.disabled = false; }
  };
  editorDialog.showModal();
}

function openConfirm({ title, description, fields = [], confirmLabel = '确认', dangerous = true, onConfirm }) {
  byId('confirmTitle').textContent = title;
  byId('confirmDescription').textContent = description;
  byId('confirmActionButton').textContent = confirmLabel;
  byId('confirmActionButton').className = dangerous ? 'danger-button' : 'primary-button';
  setError(confirmError, '');
  appendFields(confirmFields, fields);
  byId('confirmActionButton').onclick = async () => {
    const button = byId('confirmActionButton'); button.disabled = true; setError(confirmError, '');
    try { await onConfirm(valuesFrom(confirmFields)); confirmDialog.close(); await refreshData(); }
    catch (error) { setError(confirmError, error.message || '操作失败。'); }
    finally { button.disabled = false; }
  };
  confirmDialog.showModal();
}

function requiredAccount() { if (!state.accountId) throw new Error('请先新增或选择账户。'); return state.accountId; }
async function insert(table, payload) { const { error } = await state.client.from(table).insert(payload); if (error) throw error; }
async function update(table, id, payload) { const { error } = await state.client.from(table).update(payload).eq('id', id); if (error) throw error; }
async function remove(table, id) { const { error } = await state.client.from(table).delete().eq('id', id); if (error) throw error; }

function editAccount(account = null) {
  openEditor({
    title: account ? '编辑账户' : '新增账户',
    description: '首版按单账户使用，但数据模型支持多个实盘或模拟账户。',
    fields: [
      fieldDefinition({ key: 'name', label: '账户名称', required: true, value: account?.name || '默认实盘账户' }),
      fieldDefinition({ key: 'account_type', label: '账户类型', type: 'select', value: account?.account_type || 'live', options: [{ value: 'live', label: '实盘' }, { value: 'simulated', label: '模拟盘' }] }),
      fieldDefinition({ key: 'initial_net_assets', label: '初始净资产', type: 'number', min: 0, step: '0.01', required: true, value: account?.initial_net_assets ?? 0 }),
      fieldDefinition({ key: 'tracking_started_on', label: '跟踪起始日', type: 'date', required: true, value: account?.tracking_started_on || today() })
    ],
    onSave: async (values) => {
      const payload = { name: values.name, account_type: values.account_type, initial_net_assets: asNumber(values.initial_net_assets), tracking_started_on: values.tracking_started_on };
      if (account) await update(TABLES.accounts, account.id, payload);
      else await insert(TABLES.accounts, payload);
    }
  });
}

function positionFields(position = {}, watch = null) {
  return [
    fieldDefinition({ key: 'symbol', label: '证券代码', required: true, value: position.symbol || watch?.symbol || '', placeholder: '例如 300497.SZ', readOnly: Boolean(position.id) }),
    fieldDefinition({ key: 'security_name', label: '证券名称', required: true, value: position.security_name || watch?.security_name || '' }),
    fieldDefinition({ key: 'quantity', label: '当前持仓数量', type: 'number', min: 0.0001, step: '0.0001', required: true, value: position.quantity || '' }),
    fieldDefinition({ key: 'available_quantity', label: '可用数量', type: 'number', min: 0, step: '0.0001', required: true, value: position.available_quantity ?? position.quantity ?? '' }),
    fieldDefinition({ key: 'average_cost', label: '实际成本价', type: 'number', min: 0, step: '0.000001', required: true, value: position.average_cost || '' }),
    fieldDefinition({ key: 'current_price', label: '最新价', type: 'number', min: 0, step: '0.000001', required: true, value: position.current_price || '' }),
    fieldDefinition({ key: 'target_position_pct', label: '目标仓位（%）', type: 'number', min: 0, max: 100, step: '0.01', value: position.target_position_pct === null || position.target_position_pct === undefined ? '' : asNumber(position.target_position_pct) * 100, hint: '全局默认风控以 AGENTS.md 为准；此处仅保存该持仓的实际计划。' }),
    fieldDefinition({ key: 'stop_loss_price', label: '止损价', type: 'number', min: 0, step: '0.000001', value: position.stop_loss_price ?? '' }),
    fieldDefinition({ key: 'opened_on', label: '建仓日期', type: 'date', required: true, value: position.opened_on || today() }),
    fieldDefinition({ key: 'investment_thesis', label: '持仓逻辑', type: 'textarea', full: true, value: position.investment_thesis || watch?.focus_note || '' }),
    fieldDefinition({ key: 'plan_note', label: '交易计划 / 备注', type: 'textarea', full: true, value: position.plan_note || '' })
  ];
}

function editPosition(position = null, watch = null) {
  openEditor({
    title: position ? `编辑持仓：${position.security_name}` : '新增持仓',
    description: '直接编辑用于修正手工台账；部分卖出和清仓请使用持仓表中的卖出操作。',
    fields: positionFields(position || {}, watch),
    onSave: async (values) => {
      const quantity = asNumber(values.quantity); const available = asNumber(values.available_quantity);
      if (!quantity || available > quantity) throw new Error('持仓数量必须大于零，且可用数量不能大于持仓数量。');
      const payload = {
        symbol: values.symbol.toUpperCase(), security_name: values.security_name, quantity, available_quantity: available,
        average_cost: asNumber(values.average_cost), current_price: asNumber(values.current_price),
        target_position_pct: values.target_position_pct === '' ? null : asNumber(values.target_position_pct) / 100,
        stop_loss_price: values.stop_loss_price === '' ? null : asNumber(values.stop_loss_price), opened_on: values.opened_on,
        investment_thesis: values.investment_thesis, plan_note: values.plan_note
      };
      if (position) await update(TABLES.positions, position.id, payload);
      else {
        await insert(TABLES.positions, { ...payload, account_id: requiredAccount(), market: 'CN' });
        if (watch) await remove(TABLES.watchlist, watch.id);
      }
    }
  });
}

function editPrices() {
  if (!state.positions.length) throw new Error('暂无持仓可更新现价。');
  openEditor({
    title: '批量更新现价',
    description: '价格为手工维护。保存后会立即重新计算浮盈亏、仓位和风险提示。',
    fields: state.positions.map((row) => fieldDefinition({ key: `price_${row.id}`, label: `${row.security_name}（${row.symbol}）`, type: 'number', required: true, min: 0, step: '0.000001', value: row.current_price })),
    saveLabel: '更新价格',
    onSave: async (values) => Promise.all(state.positions.map((row) => update(TABLES.positions, row.id, { current_price: asNumber(values[`price_${row.id}`]) })))
  });
}

function sellPosition(position) {
  openEditor({
    title: `卖出 / 清仓：${position.security_name}`,
    description: `卖出全部 ${numeric(position.quantity, 0)} 股将生成一条清仓记录；部分卖出仅累计已实现盈亏。`,
    fields: [
      fieldDefinition({ key: 'quantity', label: '卖出数量', type: 'number', required: true, min: 0.0001, max: position.quantity, step: '0.0001', value: position.quantity }),
      fieldDefinition({ key: 'sell_price', label: '成交价', type: 'number', required: true, min: 0, step: '0.000001', value: position.current_price }),
      fieldDefinition({ key: 'fee', label: '费用', type: 'number', required: true, min: 0, step: '0.01', value: 0 }),
      fieldDefinition({ key: 'sold_on', label: '卖出日期', type: 'date', required: true, value: today() }),
      fieldDefinition({ key: 'note', label: '卖出备注', type: 'textarea', full: true, value: '' })
    ],
    saveLabel: '确认卖出',
    onSave: async (values) => {
      if (asNumber(values.quantity) > asNumber(position.quantity)) throw new Error('卖出数量不能大于当前持仓。');
      const { error } = await state.client.rpc('portfolio_sell_position', { p_position_id: position.id, p_quantity: asNumber(values.quantity), p_sell_price: asNumber(values.sell_price), p_fee: asNumber(values.fee), p_sold_on: values.sold_on, p_note: values.note });
      if (error) throw error;
    }
  });
}

function deletePosition(position) {
  openConfirm({ title: `删除持仓：${position.security_name}`, description: '这会删除当前持仓记录，不会生成清仓盈利分析。仅用于错误录入或导入前清理。', fields: [fieldDefinition({ key: 'reason', label: '删除原因', type: 'textarea', required: true, full: true })], confirmLabel: '确认删除', onConfirm: async (values) => { if (!values.reason) throw new Error('请填写删除原因。'); await remove(TABLES.positions, position.id); } });
}

function editSnapshot() {
  const latest = latestSnapshot(); const metric = portfolioMetrics();
  openEditor({
    title: '记录账户快照', description: '总资产为券商快照值；证券市值、可用资金与可取资金可据券商页面手工填写。',
    fields: [
      fieldDefinition({ key: 'as_of_at', label: '快照时间', type: 'datetime-local', required: true, value: new Date().toISOString().slice(0, 16) }),
      fieldDefinition({ key: 'total_assets', label: '账户总资产', type: 'number', required: true, min: 0, step: '0.01', value: latest?.total_assets ?? metric.totalAssets }),
      fieldDefinition({ key: 'securities_value', label: '证券市值', type: 'number', required: true, min: 0, step: '0.01', value: metric.marketValue }),
      fieldDefinition({ key: 'available_cash', label: '可用资金', type: 'number', required: true, min: 0, step: '0.01', value: latest?.available_cash ?? '' }),
      fieldDefinition({ key: 'withdrawable_cash', label: '可取资金', type: 'number', min: 0, step: '0.01', value: latest?.withdrawable_cash ?? '' }),
      fieldDefinition({ key: 'source', label: '数据来源', type: 'select', value: 'manual', options: [{ value: 'manual', label: '手工录入' }, { value: 'brokerage-screenshot', label: '券商截图' }] }),
      fieldDefinition({ key: 'note', label: '备注', type: 'textarea', full: true, value: '' })
    ],
    onSave: async (values) => insert(TABLES.snapshots, { account_id: requiredAccount(), as_of_at: new Date(values.as_of_at).toISOString(), total_assets: asNumber(values.total_assets), securities_value: asNumber(values.securities_value), available_cash: asNumber(values.available_cash), withdrawable_cash: values.withdrawable_cash === '' ? null : asNumber(values.withdrawable_cash), source: values.source, note: values.note })
  });
}

function editCashflow() {
  openEditor({ title: '记录资金变动', description: '只记录系统启用后的入金和出金，用于从账户收益中剔除外部资金影响。', fields: [fieldDefinition({ key: 'flow_type', label: '类型', type: 'select', value: 'deposit', options: [{ value: 'deposit', label: '入金' }, { value: 'withdrawal', label: '出金' }] }), fieldDefinition({ key: 'amount', label: '金额', type: 'number', required: true, min: 0.01, step: '0.01' }), fieldDefinition({ key: 'occurred_on', label: '日期', type: 'date', required: true, value: today() }), fieldDefinition({ key: 'note', label: '备注', type: 'textarea', full: true })], onSave: async (values) => insert(TABLES.cashflows, { account_id: requiredAccount(), flow_type: values.flow_type, amount: asNumber(values.amount), occurred_on: values.occurred_on, note: values.note }) });
}

function editWatchlist(item = null) {
  openEditor({
    title: item ? `编辑观察股：${item.security_name}` : '新增观察股',
    description: '观察股不使用实时行情；填写计划区间、失效条件和复盘日即可。',
    fields: [
      fieldDefinition({ key: 'symbol', label: '证券代码', required: true, value: item?.symbol || '', placeholder: '例如 300497.SZ', readOnly: Boolean(item) }),
      fieldDefinition({ key: 'security_name', label: '证券名称', required: true, value: item?.security_name || '' }),
      fieldDefinition({ key: 'status', label: '状态', type: 'select', value: item?.status || 'watching', options: [{ value: 'watching', label: '观察' }, { value: 'planned', label: '计划建仓' }, { value: 'abandoned', label: '已放弃' }] }),
      fieldDefinition({ key: 'review_on', label: '下次复盘日', type: 'date', value: item?.review_on || '' }),
      fieldDefinition({ key: 'buy_low', label: '计划买入下限', type: 'number', min: 0, step: '0.000001', value: item?.buy_low ?? '' }),
      fieldDefinition({ key: 'buy_high', label: '计划买入上限', type: 'number', min: 0, step: '0.000001', value: item?.buy_high ?? '' }),
      fieldDefinition({ key: 'report_url', label: '报告链接（可选）', type: 'url', full: true, value: item?.report_url || reportUrl(item?.symbol) || '' }),
      fieldDefinition({ key: 'invalidation_condition', label: '失效条件', type: 'textarea', full: true, value: item?.invalidation_condition || '' }),
      fieldDefinition({ key: 'focus_note', label: '关注理由 / 计划', type: 'textarea', full: true, value: item?.focus_note || '' })
    ],
    onSave: async (values) => {
      const low = values.buy_low === '' ? null : asNumber(values.buy_low); const high = values.buy_high === '' ? null : asNumber(values.buy_high);
      if (low !== null && high !== null && low > high) throw new Error('计划买入下限不能高于上限。');
      const payload = { symbol: values.symbol.toUpperCase(), security_name: values.security_name, status: values.status, review_on: values.review_on || null, buy_low: low, buy_high: high, report_url: values.report_url, invalidation_condition: values.invalidation_condition, focus_note: values.focus_note };
      if (item) await update(TABLES.watchlist, item.id, payload); else await insert(TABLES.watchlist, { ...payload, account_id: requiredAccount(), market: 'CN' });
    }
  });
}

function convertWatchlist(item) { editPosition(null, item); }
function deleteWatchlist(item) { openConfirm({ title: `删除观察股：${item.security_name}`, description: '删除后不会影响报告文件。', confirmLabel: '确认删除', onConfirm: async () => remove(TABLES.watchlist, item.id) }); }

function correctClosed(row) {
  openEditor({
    title: `更正清仓记录：${row.security_name}`,
    description: '更正会立即重算总盈亏和收益率，必须记录原因。',
    fields: [
      fieldDefinition({ key: 'final_sale_price', label: '最终成交价', type: 'number', required: true, min: 0, step: '0.000001', value: row.final_sale_price }),
      fieldDefinition({ key: 'total_sale_proceeds', label: '累计卖出金额', type: 'number', required: true, step: '0.01', value: row.total_sale_proceeds }),
      fieldDefinition({ key: 'total_fees', label: '累计费用', type: 'number', required: true, min: 0, step: '0.01', value: row.total_fees }),
      fieldDefinition({ key: 'closed_on', label: '清仓日期', type: 'date', required: true, value: row.closed_on }),
      fieldDefinition({ key: 'note', label: '备注', type: 'textarea', full: true, value: row.note || '' }),
      fieldDefinition({ key: 'reason', label: '更正原因', type: 'textarea', required: true, full: true })
    ],
    saveLabel: '确认更正',
    onSave: async (values) => {
      const { error } = await state.client.rpc('portfolio_correct_closed_position', { p_closed_id: row.id, p_final_sale_price: asNumber(values.final_sale_price), p_total_sale_proceeds: asNumber(values.total_sale_proceeds), p_total_fees: asNumber(values.total_fees), p_closed_on: values.closed_on, p_note: values.note, p_reason: values.reason });
      if (error) throw error;
    }
  });
}

function reopenClosed(row) {
  openConfirm({ title: `恢复为持仓：${row.security_name}`, description: '该清仓记录将从清仓分析撤回，并生成一条可编辑的当前持仓。', fields: [fieldDefinition({ key: 'reason', label: '恢复原因', type: 'textarea', required: true, full: true })], confirmLabel: '确认恢复', onConfirm: async (values) => { if (!values.reason) throw new Error('请填写恢复原因。'); const { error } = await state.client.rpc('portfolio_reopen_closed_position', { p_closed_id: row.id, p_reason: values.reason }); if (error) throw error; } });
}

async function exportBackup() {
  const button = byId('exportBackupButton'); button.disabled = true;
  try {
    const [accounts, positions, closedPositions, watchlist, cashflows, snapshots, auditLogs] = await Promise.all([
      query(TABLES.accounts, null), query(TABLES.positions, null), query(TABLES.closed, null), query(TABLES.watchlist, null), query(TABLES.cashflows, null), query(TABLES.snapshots, null), query(TABLES.audit, null)
    ]);
    const backup = { schemaVersion: 1, exportedAt: new Date().toISOString(), accounts, positions, closedPositions, watchlist, cashflows, snapshots, auditLogs };
    const blob = new Blob([JSON.stringify(backup, null, 2)], { type: 'application/json' });
    const href = URL.createObjectURL(blob); const anchor = node('a', { href, download: `portfolio-backup-${new Date().toISOString().slice(0, 10)}.json` });
    document.body.append(anchor); anchor.click(); anchor.remove(); URL.revokeObjectURL(href);
    setStatus('完整 JSON 备份已导出。请保存到本地私有目录，勿提交至公开仓库。');
  } catch (error) { setStatus(`导出失败：${error.message || '未知错误。'}`); }
  finally { button.disabled = false; }
}

async function importBackup(event) {
  const file = event.target.files?.[0]; event.target.value = '';
  if (!file) return;
  try {
    const backup = JSON.parse(await file.text());
    if (backup.schemaVersion !== 1 || !Array.isArray(backup.accounts)) throw new Error('不是本工具导出的版本 1 备份。');
    openConfirm({ title: '从备份恢复全部持仓数据', description: '恢复将先替换当前用户的所有账户、持仓、清仓记录、观察清单、资金事件和快照。恢复前请确认你已另行保存当前备份。', fields: [fieldDefinition({ key: 'confirm', label: '输入“恢复”以继续', required: true, full: true })], confirmLabel: '恢复数据', onConfirm: async (values) => { if (values.confirm !== '恢复') throw new Error('请输入“恢复”确认。'); const { error } = await state.client.rpc('portfolio_restore_backup', { p_backup: backup }); if (error) throw error; } });
  } catch (error) { setStatus(`导入失败：${error.message || '文件无法读取。'}`); }
}

boot();
