-- Portfolio module schema for Supabase PostgreSQL.
-- Apply this file in Supabase SQL Editor before using the public portfolio entry.
-- The schema contains no personal account data. Seed data stays in ignored local files.

create extension if not exists pgcrypto;

create table if not exists public.portfolio_accounts (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  name text not null check (char_length(trim(name)) between 1 and 80),
  account_type text not null default 'live' check (account_type in ('live', 'simulated')),
  currency char(3) not null default 'CNY',
  initial_net_assets numeric(18, 2) not null default 0 check (initial_net_assets >= 0),
  tracking_started_on date not null default current_date,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_id, name)
);

create table if not exists public.portfolio_positions (
  id uuid primary key default gen_random_uuid(),
  account_id uuid not null references public.portfolio_accounts(id) on delete cascade,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  symbol text not null check (symbol ~ '^[0-9A-Z._-]{1,24}$'),
  security_name text not null check (char_length(trim(security_name)) between 1 and 80),
  market text not null default 'CN',
  quantity numeric(20, 4) not null check (quantity > 0),
  available_quantity numeric(20, 4) not null check (available_quantity >= 0 and available_quantity <= quantity),
  average_cost numeric(20, 6) not null check (average_cost >= 0),
  current_price numeric(20, 6) not null check (current_price >= 0),
  target_position_pct numeric(8, 6) check (target_position_pct is null or target_position_pct between 0 and 1),
  stop_loss_price numeric(20, 6) check (stop_loss_price is null or stop_loss_price >= 0),
  opened_on date not null default current_date,
  investment_thesis text not null default '',
  plan_note text not null default '',
  accumulated_realized_pnl numeric(20, 2) not null default 0,
  accumulated_sale_proceeds numeric(20, 2) not null default 0,
  accumulated_fees numeric(20, 2) not null default 0,
  lifecycle_sold_quantity numeric(20, 4) not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (account_id, symbol)
);

create table if not exists public.portfolio_closed_positions (
  id uuid primary key default gen_random_uuid(),
  account_id uuid not null references public.portfolio_accounts(id) on delete cascade,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  source_position_id uuid,
  symbol text not null check (symbol ~ '^[0-9A-Z._-]{1,24}$'),
  security_name text not null,
  market text not null default 'CN',
  closed_quantity numeric(20, 4) not null check (closed_quantity > 0),
  average_cost numeric(20, 6) not null check (average_cost >= 0),
  final_sale_price numeric(20, 6) not null check (final_sale_price >= 0),
  total_sale_proceeds numeric(20, 2) not null,
  total_fees numeric(20, 2) not null default 0 check (total_fees >= 0),
  realized_pnl numeric(20, 2) not null,
  return_pct numeric(12, 8),
  opened_on date,
  closed_on date not null default current_date,
  investment_thesis text not null default '',
  plan_note text not null default '',
  correction_reason text not null default '',
  note text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.portfolio_watchlist (
  id uuid primary key default gen_random_uuid(),
  account_id uuid not null references public.portfolio_accounts(id) on delete cascade,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  symbol text not null check (symbol ~ '^[0-9A-Z._-]{1,24}$'),
  security_name text not null,
  market text not null default 'CN',
  status text not null default 'watching' check (status in ('watching', 'planned', 'abandoned')),
  buy_low numeric(20, 6) check (buy_low is null or buy_low >= 0),
  buy_high numeric(20, 6) check (buy_high is null or buy_high >= 0),
  invalidation_condition text not null default '',
  focus_note text not null default '',
  review_on date,
  report_url text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (account_id, symbol),
  check (buy_low is null or buy_high is null or buy_low <= buy_high)
);

create table if not exists public.portfolio_cashflows (
  id uuid primary key default gen_random_uuid(),
  account_id uuid not null references public.portfolio_accounts(id) on delete cascade,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  flow_type text not null check (flow_type in ('deposit', 'withdrawal')),
  amount numeric(20, 2) not null check (amount > 0),
  occurred_on date not null default current_date,
  note text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.portfolio_asset_snapshots (
  id uuid primary key default gen_random_uuid(),
  account_id uuid not null references public.portfolio_accounts(id) on delete cascade,
  owner_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
  as_of_at timestamptz not null default now(),
  total_assets numeric(20, 2) not null check (total_assets >= 0),
  securities_value numeric(20, 2) not null check (securities_value >= 0),
  available_cash numeric(20, 2) not null check (available_cash >= 0),
  withdrawable_cash numeric(20, 2) check (withdrawable_cash is null or withdrawable_cash >= 0),
  source text not null default 'manual',
  note text not null default '',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.portfolio_audit_logs (
  id uuid primary key default gen_random_uuid(),
  account_id uuid references public.portfolio_accounts(id) on delete set null,
  owner_id uuid not null references auth.users(id) on delete cascade,
  entity_type text not null,
  entity_id uuid,
  action text not null check (action in ('INSERT', 'UPDATE', 'DELETE', 'SELL', 'CLOSE', 'CORRECT', 'RESTORE')),
  reason text not null default '',
  before_data jsonb,
  after_data jsonb,
  created_at timestamptz not null default now()
);

create index if not exists portfolio_positions_owner_account_idx on public.portfolio_positions(owner_id, account_id);
create index if not exists portfolio_closed_positions_owner_account_idx on public.portfolio_closed_positions(owner_id, account_id, closed_on desc);
create index if not exists portfolio_watchlist_owner_account_idx on public.portfolio_watchlist(owner_id, account_id, status);
create index if not exists portfolio_cashflows_owner_account_idx on public.portfolio_cashflows(owner_id, account_id, occurred_on desc);
create index if not exists portfolio_asset_snapshots_owner_account_idx on public.portfolio_asset_snapshots(owner_id, account_id, as_of_at desc);
create index if not exists portfolio_audit_logs_owner_created_idx on public.portfolio_audit_logs(owner_id, created_at desc);

create or replace function public.portfolio_set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.portfolio_capture_audit()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  before_payload jsonb := case when tg_op in ('UPDATE', 'DELETE') then to_jsonb(old) else null end;
  after_payload jsonb := case when tg_op in ('INSERT', 'UPDATE') then to_jsonb(new) else null end;
  target_owner uuid;
  target_account uuid;
  target_id uuid;
begin
  if current_setting('portfolio.skip_audit', true) = 'on' then
    return coalesce(new, old);
  end if;

  target_owner := coalesce((after_payload ->> 'owner_id')::uuid, (before_payload ->> 'owner_id')::uuid);
  target_account := coalesce((after_payload ->> 'account_id')::uuid, (before_payload ->> 'account_id')::uuid);
  target_id := coalesce((after_payload ->> 'id')::uuid, (before_payload ->> 'id')::uuid);
  if tg_table_name = 'portfolio_accounts' then
    target_account := target_id;
  end if;

  if target_owner is not null then
    insert into public.portfolio_audit_logs (account_id, owner_id, entity_type, entity_id, action, reason, before_data, after_data)
    values (
      target_account,
      target_owner,
      tg_table_name,
      target_id,
      tg_op,
      coalesce(current_setting('portfolio.change_reason', true), ''),
      before_payload,
      after_payload
    );
  end if;
  return coalesce(new, old);
end;
$$;

do $$
declare
  target_table text;
begin
  foreach target_table in array array[
    'portfolio_accounts',
    'portfolio_positions',
    'portfolio_closed_positions',
    'portfolio_watchlist',
    'portfolio_cashflows',
    'portfolio_asset_snapshots'
  ] loop
    execute format('drop trigger if exists %I on public.%I', target_table || '_updated_at', target_table);
    execute format('create trigger %I before update on public.%I for each row execute function public.portfolio_set_updated_at()', target_table || '_updated_at', target_table);
    execute format('drop trigger if exists %I on public.%I', target_table || '_audit', target_table);
    execute format('create trigger %I after insert or update or delete on public.%I for each row execute function public.portfolio_capture_audit()', target_table || '_audit', target_table);
  end loop;
end;
$$;

alter table public.portfolio_accounts enable row level security;
alter table public.portfolio_positions enable row level security;
alter table public.portfolio_closed_positions enable row level security;
alter table public.portfolio_watchlist enable row level security;
alter table public.portfolio_cashflows enable row level security;
alter table public.portfolio_asset_snapshots enable row level security;
alter table public.portfolio_audit_logs enable row level security;

drop policy if exists portfolio_accounts_owner_only on public.portfolio_accounts;
create policy portfolio_accounts_owner_only on public.portfolio_accounts for all to authenticated using (owner_id = auth.uid()) with check (owner_id = auth.uid());
drop policy if exists portfolio_positions_owner_only on public.portfolio_positions;
create policy portfolio_positions_owner_only on public.portfolio_positions for all to authenticated
using (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()))
with check (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()));
drop policy if exists portfolio_closed_positions_owner_only on public.portfolio_closed_positions;
create policy portfolio_closed_positions_owner_only on public.portfolio_closed_positions for all to authenticated
using (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()))
with check (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()));
drop policy if exists portfolio_watchlist_owner_only on public.portfolio_watchlist;
create policy portfolio_watchlist_owner_only on public.portfolio_watchlist for all to authenticated
using (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()))
with check (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()));
drop policy if exists portfolio_cashflows_owner_only on public.portfolio_cashflows;
create policy portfolio_cashflows_owner_only on public.portfolio_cashflows for all to authenticated
using (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()))
with check (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()));
drop policy if exists portfolio_asset_snapshots_owner_only on public.portfolio_asset_snapshots;
create policy portfolio_asset_snapshots_owner_only on public.portfolio_asset_snapshots for all to authenticated
using (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()))
with check (owner_id = auth.uid() and exists (select 1 from public.portfolio_accounts account where account.id = account_id and account.owner_id = auth.uid()));
drop policy if exists portfolio_audit_logs_owner_only on public.portfolio_audit_logs;
create policy portfolio_audit_logs_owner_only on public.portfolio_audit_logs for select to authenticated using (owner_id = auth.uid());

create or replace function public.portfolio_sell_position(
  p_position_id uuid,
  p_quantity numeric,
  p_sell_price numeric,
  p_fee numeric default 0,
  p_sold_on date default current_date,
  p_note text default ''
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  position_row public.portfolio_positions%rowtype;
  sale_proceeds numeric(20, 2);
  sale_pnl numeric(20, 2);
  remaining_quantity numeric(20, 4);
  closing_pnl numeric(20, 2);
  closing_proceeds numeric(20, 2);
  closing_fees numeric(20, 2);
  closing_quantity numeric(20, 4);
  closed_id uuid;
begin
  if auth.uid() is null then
    raise exception '需要已验证用户。';
  end if;
  if p_quantity is null or p_quantity <= 0 or p_sell_price is null or p_sell_price < 0 or coalesce(p_fee, 0) < 0 then
    raise exception '卖出数量、价格或费用不合法。';
  end if;

  select * into position_row
  from public.portfolio_positions
  where id = p_position_id and owner_id = auth.uid()
  for update;

  if not found then
    raise exception '未找到可卖出的持仓。';
  end if;
  if p_quantity > position_row.quantity then
    raise exception '卖出数量不能大于当前持仓数量。';
  end if;

  perform set_config('portfolio.change_reason', coalesce(p_note, ''), true);
  sale_proceeds := round(p_quantity * p_sell_price, 2);
  sale_pnl := round((p_sell_price - position_row.average_cost) * p_quantity - coalesce(p_fee, 0), 2);
  remaining_quantity := position_row.quantity - p_quantity;

  if remaining_quantity > 0 then
    update public.portfolio_positions
    set quantity = remaining_quantity,
        available_quantity = least(position_row.available_quantity, remaining_quantity),
        current_price = p_sell_price,
        accumulated_realized_pnl = position_row.accumulated_realized_pnl + sale_pnl,
        accumulated_sale_proceeds = position_row.accumulated_sale_proceeds + sale_proceeds,
        accumulated_fees = position_row.accumulated_fees + coalesce(p_fee, 0),
        lifecycle_sold_quantity = position_row.lifecycle_sold_quantity + p_quantity
    where id = position_row.id;

    insert into public.portfolio_audit_logs (account_id, owner_id, entity_type, entity_id, action, reason, after_data)
    values (position_row.account_id, auth.uid(), 'portfolio_positions', position_row.id, 'SELL', coalesce(p_note, ''), jsonb_build_object('quantity', p_quantity, 'price', p_sell_price, 'fee', coalesce(p_fee, 0), 'sold_on', p_sold_on));
    return jsonb_build_object('status', 'partial', 'realized_pnl', sale_pnl, 'remaining_quantity', remaining_quantity);
  end if;

  closing_pnl := position_row.accumulated_realized_pnl + sale_pnl;
  closing_proceeds := position_row.accumulated_sale_proceeds + sale_proceeds;
  closing_fees := position_row.accumulated_fees + coalesce(p_fee, 0);
  closing_quantity := position_row.lifecycle_sold_quantity + p_quantity;

  insert into public.portfolio_closed_positions (
    account_id, owner_id, source_position_id, symbol, security_name, market, closed_quantity, average_cost,
    final_sale_price, total_sale_proceeds, total_fees, realized_pnl, return_pct, opened_on, closed_on,
    investment_thesis, plan_note, note
  ) values (
    position_row.account_id, auth.uid(), position_row.id, position_row.symbol, position_row.security_name, position_row.market,
    closing_quantity, position_row.average_cost, p_sell_price, closing_proceeds, closing_fees, closing_pnl,
    case when position_row.average_cost * closing_quantity = 0 then null else round(closing_pnl / (position_row.average_cost * closing_quantity), 8) end,
    position_row.opened_on, coalesce(p_sold_on, current_date), position_row.investment_thesis, position_row.plan_note, coalesce(p_note, '')
  ) returning id into closed_id;

  delete from public.portfolio_positions where id = position_row.id;
  insert into public.portfolio_audit_logs (account_id, owner_id, entity_type, entity_id, action, reason, after_data)
  values (position_row.account_id, auth.uid(), 'portfolio_closed_positions', closed_id, 'CLOSE', coalesce(p_note, ''), jsonb_build_object('realized_pnl', closing_pnl, 'closed_quantity', closing_quantity));
  return jsonb_build_object('status', 'closed', 'closed_id', closed_id, 'realized_pnl', closing_pnl, 'return_pct', case when position_row.average_cost * closing_quantity = 0 then null else round(closing_pnl / (position_row.average_cost * closing_quantity), 8) end);
end;
$$;

create or replace function public.portfolio_correct_closed_position(
  p_closed_id uuid,
  p_final_sale_price numeric,
  p_total_sale_proceeds numeric,
  p_total_fees numeric,
  p_closed_on date,
  p_note text,
  p_reason text
)
returns public.portfolio_closed_positions
language plpgsql
security definer
set search_path = public
as $$
declare
  corrected public.portfolio_closed_positions%rowtype;
  corrected_pnl numeric(20, 2);
begin
  if auth.uid() is null or coalesce(trim(p_reason), '') = '' then
    raise exception '更正已清仓记录必须填写原因。';
  end if;
  select * into corrected from public.portfolio_closed_positions where id = p_closed_id and owner_id = auth.uid() for update;
  if not found then
    raise exception '未找到已清仓记录。';
  end if;
  if p_final_sale_price < 0 or p_total_fees < 0 then
    raise exception '更正后的价格或费用不合法。';
  end if;
  corrected_pnl := round(p_total_sale_proceeds - corrected.average_cost * corrected.closed_quantity - p_total_fees, 2);
  perform set_config('portfolio.change_reason', p_reason, true);
  update public.portfolio_closed_positions
  set final_sale_price = p_final_sale_price,
      total_sale_proceeds = p_total_sale_proceeds,
      total_fees = p_total_fees,
      realized_pnl = corrected_pnl,
      return_pct = case when corrected.average_cost * corrected.closed_quantity = 0 then null else round(corrected_pnl / (corrected.average_cost * corrected.closed_quantity), 8) end,
      closed_on = p_closed_on,
      note = coalesce(p_note, ''),
      correction_reason = p_reason
  where id = p_closed_id
  returning * into corrected;
  insert into public.portfolio_audit_logs (account_id, owner_id, entity_type, entity_id, action, reason, after_data)
  values (corrected.account_id, auth.uid(), 'portfolio_closed_positions', corrected.id, 'CORRECT', p_reason, to_jsonb(corrected));
  return corrected;
end;
$$;

create or replace function public.portfolio_reopen_closed_position(p_closed_id uuid, p_reason text)
returns public.portfolio_positions
language plpgsql
security definer
set search_path = public
as $$
declare
  closed_row public.portfolio_closed_positions%rowtype;
  restored public.portfolio_positions%rowtype;
begin
  if auth.uid() is null or coalesce(trim(p_reason), '') = '' then
    raise exception '恢复为持仓必须填写原因。';
  end if;
  select * into closed_row from public.portfolio_closed_positions where id = p_closed_id and owner_id = auth.uid() for update;
  if not found then
    raise exception '未找到已清仓记录。';
  end if;
  if exists (select 1 from public.portfolio_positions where account_id = closed_row.account_id and symbol = closed_row.symbol) then
    raise exception '同一账户已有该证券持仓，请先合并或移除现有持仓。';
  end if;
  perform set_config('portfolio.change_reason', p_reason, true);
  insert into public.portfolio_positions (
    account_id, owner_id, symbol, security_name, market, quantity, available_quantity, average_cost, current_price,
    opened_on, investment_thesis, plan_note
  ) values (
    closed_row.account_id, auth.uid(), closed_row.symbol, closed_row.security_name, closed_row.market,
    closed_row.closed_quantity, closed_row.closed_quantity, closed_row.average_cost, closed_row.final_sale_price,
    coalesce(closed_row.opened_on, closed_row.closed_on), closed_row.investment_thesis, closed_row.plan_note
  ) returning * into restored;
  delete from public.portfolio_closed_positions where id = closed_row.id;
  insert into public.portfolio_audit_logs (account_id, owner_id, entity_type, entity_id, action, reason, after_data)
  values (restored.account_id, auth.uid(), 'portfolio_positions', restored.id, 'RESTORE', p_reason, to_jsonb(restored));
  return restored;
end;
$$;

create or replace function public.portfolio_restore_backup(p_backup jsonb)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  item jsonb;
  restore_account_id uuid;
begin
  if auth.uid() is null then
    raise exception '需要已验证用户。';
  end if;
  if coalesce((p_backup ->> 'schemaVersion')::integer, 0) <> 1 then
    raise exception '不支持的备份版本。';
  end if;

  perform set_config('portfolio.skip_audit', 'on', true);
  delete from public.portfolio_audit_logs where owner_id = auth.uid();
  delete from public.portfolio_accounts where owner_id = auth.uid();

  for item in select value from jsonb_array_elements(coalesce(p_backup -> 'accounts', '[]'::jsonb)) loop
    insert into public.portfolio_accounts (id, owner_id, name, account_type, currency, initial_net_assets, tracking_started_on, is_active, created_at, updated_at)
    values (
      (item ->> 'id')::uuid, auth.uid(), item ->> 'name', coalesce(item ->> 'account_type', 'live'), coalesce(item ->> 'currency', 'CNY'),
      coalesce((item ->> 'initial_net_assets')::numeric, 0), coalesce((item ->> 'tracking_started_on')::date, current_date), coalesce((item ->> 'is_active')::boolean, true),
      coalesce((item ->> 'created_at')::timestamptz, now()), coalesce((item ->> 'updated_at')::timestamptz, now())
    );
  end loop;
  for item in select value from jsonb_array_elements(coalesce(p_backup -> 'positions', '[]'::jsonb)) loop
    insert into public.portfolio_positions (id, account_id, owner_id, symbol, security_name, market, quantity, available_quantity, average_cost, current_price, target_position_pct, stop_loss_price, opened_on, investment_thesis, plan_note, accumulated_realized_pnl, accumulated_sale_proceeds, accumulated_fees, lifecycle_sold_quantity, created_at, updated_at)
    values ((item ->> 'id')::uuid, (item ->> 'account_id')::uuid, auth.uid(), item ->> 'symbol', item ->> 'security_name', coalesce(item ->> 'market', 'CN'), (item ->> 'quantity')::numeric, (item ->> 'available_quantity')::numeric, (item ->> 'average_cost')::numeric, (item ->> 'current_price')::numeric, nullif(item ->> 'target_position_pct', '')::numeric, nullif(item ->> 'stop_loss_price', '')::numeric, coalesce((item ->> 'opened_on')::date, current_date), coalesce(item ->> 'investment_thesis', ''), coalesce(item ->> 'plan_note', ''), coalesce((item ->> 'accumulated_realized_pnl')::numeric, 0), coalesce((item ->> 'accumulated_sale_proceeds')::numeric, 0), coalesce((item ->> 'accumulated_fees')::numeric, 0), coalesce((item ->> 'lifecycle_sold_quantity')::numeric, 0), coalesce((item ->> 'created_at')::timestamptz, now()), coalesce((item ->> 'updated_at')::timestamptz, now()));
  end loop;
  for item in select value from jsonb_array_elements(coalesce(p_backup -> 'closedPositions', '[]'::jsonb)) loop
    insert into public.portfolio_closed_positions (id, account_id, owner_id, source_position_id, symbol, security_name, market, closed_quantity, average_cost, final_sale_price, total_sale_proceeds, total_fees, realized_pnl, return_pct, opened_on, closed_on, investment_thesis, plan_note, correction_reason, note, created_at, updated_at)
    values ((item ->> 'id')::uuid, (item ->> 'account_id')::uuid, auth.uid(), nullif(item ->> 'source_position_id', '')::uuid, item ->> 'symbol', item ->> 'security_name', coalesce(item ->> 'market', 'CN'), (item ->> 'closed_quantity')::numeric, (item ->> 'average_cost')::numeric, (item ->> 'final_sale_price')::numeric, (item ->> 'total_sale_proceeds')::numeric, coalesce((item ->> 'total_fees')::numeric, 0), (item ->> 'realized_pnl')::numeric, nullif(item ->> 'return_pct', '')::numeric, nullif(item ->> 'opened_on', '')::date, coalesce((item ->> 'closed_on')::date, current_date), coalesce(item ->> 'investment_thesis', ''), coalesce(item ->> 'plan_note', ''), coalesce(item ->> 'correction_reason', ''), coalesce(item ->> 'note', ''), coalesce((item ->> 'created_at')::timestamptz, now()), coalesce((item ->> 'updated_at')::timestamptz, now()));
  end loop;
  for item in select value from jsonb_array_elements(coalesce(p_backup -> 'watchlist', '[]'::jsonb)) loop
    insert into public.portfolio_watchlist (id, account_id, owner_id, symbol, security_name, market, status, buy_low, buy_high, invalidation_condition, focus_note, review_on, report_url, created_at, updated_at)
    values ((item ->> 'id')::uuid, (item ->> 'account_id')::uuid, auth.uid(), item ->> 'symbol', item ->> 'security_name', coalesce(item ->> 'market', 'CN'), coalesce(item ->> 'status', 'watching'), nullif(item ->> 'buy_low', '')::numeric, nullif(item ->> 'buy_high', '')::numeric, coalesce(item ->> 'invalidation_condition', ''), coalesce(item ->> 'focus_note', ''), nullif(item ->> 'review_on', '')::date, coalesce(item ->> 'report_url', ''), coalesce((item ->> 'created_at')::timestamptz, now()), coalesce((item ->> 'updated_at')::timestamptz, now()));
  end loop;
  for item in select value from jsonb_array_elements(coalesce(p_backup -> 'cashflows', '[]'::jsonb)) loop
    insert into public.portfolio_cashflows (id, account_id, owner_id, flow_type, amount, occurred_on, note, created_at, updated_at)
    values ((item ->> 'id')::uuid, (item ->> 'account_id')::uuid, auth.uid(), item ->> 'flow_type', (item ->> 'amount')::numeric, coalesce((item ->> 'occurred_on')::date, current_date), coalesce(item ->> 'note', ''), coalesce((item ->> 'created_at')::timestamptz, now()), coalesce((item ->> 'updated_at')::timestamptz, now()));
  end loop;
  for item in select value from jsonb_array_elements(coalesce(p_backup -> 'snapshots', '[]'::jsonb)) loop
    insert into public.portfolio_asset_snapshots (id, account_id, owner_id, as_of_at, total_assets, securities_value, available_cash, withdrawable_cash, source, note, created_at, updated_at)
    values ((item ->> 'id')::uuid, (item ->> 'account_id')::uuid, auth.uid(), coalesce((item ->> 'as_of_at')::timestamptz, now()), (item ->> 'total_assets')::numeric, (item ->> 'securities_value')::numeric, (item ->> 'available_cash')::numeric, nullif(item ->> 'withdrawable_cash', '')::numeric, coalesce(item ->> 'source', 'manual'), coalesce(item ->> 'note', ''), coalesce((item ->> 'created_at')::timestamptz, now()), coalesce((item ->> 'updated_at')::timestamptz, now()));
  end loop;
  perform set_config('portfolio.skip_audit', 'off', true);
  insert into public.portfolio_audit_logs (owner_id, entity_type, action, reason, after_data)
  values (auth.uid(), 'portfolio_backup', 'RESTORE', '从 JSON 备份恢复', jsonb_build_object('restored_at', now()));
  return jsonb_build_object('restored', true);
end;
$$;

grant usage on schema public to authenticated;
grant select, insert, update, delete on public.portfolio_accounts, public.portfolio_positions, public.portfolio_closed_positions, public.portfolio_watchlist, public.portfolio_cashflows, public.portfolio_asset_snapshots to authenticated;
grant select on public.portfolio_audit_logs to authenticated;
grant execute on function public.portfolio_sell_position(uuid, numeric, numeric, numeric, date, text) to authenticated;
grant execute on function public.portfolio_correct_closed_position(uuid, numeric, numeric, numeric, date, text, text) to authenticated;
grant execute on function public.portfolio_reopen_closed_position(uuid, text) to authenticated;
grant execute on function public.portfolio_restore_backup(jsonb) to authenticated;
