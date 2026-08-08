#!/usr/bin/env python3
"""Local-only portfolio administration, backup, and Skill snapshot utility.

The script deliberately uses Supabase's service-role key from an ignored local env
file. Never place that key in hub/ or any public static asset.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENV = REPO_ROOT / '.env.portfolio'
TABLES = {
    'accounts': 'portfolio_accounts',
    'positions': 'portfolio_positions',
    'closedPositions': 'portfolio_closed_positions',
    'watchlist': 'portfolio_watchlist',
    'cashflows': 'portfolio_cashflows',
    'snapshots': 'portfolio_asset_snapshots',
    'auditLogs': 'portfolio_audit_logs',
}


def load_env(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


def settings(env_path: Path) -> tuple[str, str, str]:
    load_env(env_path)
    url = os.getenv('PORTFOLIO_SUPABASE_URL', '').rstrip('/')
    key = os.getenv('PORTFOLIO_SUPABASE_SERVICE_ROLE_KEY', '')
    email = os.getenv('PORTFOLIO_OWNER_EMAIL', '').strip().lower()
    missing = [name for name, value in {
        'PORTFOLIO_SUPABASE_URL': url,
        'PORTFOLIO_SUPABASE_SERVICE_ROLE_KEY': key,
        'PORTFOLIO_OWNER_EMAIL': email,
    }.items() if not value]
    if missing:
        raise RuntimeError(f"缺少本地配置：{', '.join(missing)}。请复制 .env.portfolio.example 为 .env.portfolio 后填写。")
    return url, key, email


def request_json(url: str, service_key: str, method: str, path: str, *, query: dict[str, str] | None = None, body: Any = None, prefer: str | None = None) -> Any:
    target = f'{url}{path}'
    if query:
        target += '?' + urlencode(query)
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}',
        'Content-Type': 'application/json',
    }
    if prefer:
        headers['Prefer'] = prefer
    payload = None if body is None else json.dumps(body, ensure_ascii=False, default=str).encode('utf-8')
    req = Request(target, data=payload, headers=headers, method=method)
    try:
        with urlopen(req, timeout=30) as response:
            raw = response.read().decode('utf-8')
            return json.loads(raw) if raw else None
    except HTTPError as error:
        detail = error.read().decode('utf-8', errors='replace')
        raise RuntimeError(f'Supabase 请求失败（{error.code}）：{detail}') from error


def owner_id(url: str, key: str, email: str) -> str:
    payload = request_json(url, key, 'GET', '/auth/v1/admin/users', query={'page': '1', 'per_page': '1000'})
    users = payload.get('users', payload) if isinstance(payload, dict) else payload
    for user in users:
        if str(user.get('email', '')).lower() == email:
            return str(user['id'])
    raise RuntimeError(f'未找到 Supabase 用户：{email}。请先在持仓页面完成一次邮箱密码登录。')


def select_rows(url: str, key: str, table: str, owner: str, *, account_id: str | None = None, order: str | None = None) -> list[dict[str, Any]]:
    query = {'select': '*', 'owner_id': f'eq.{owner}'}
    if account_id:
        query['account_id'] = f'eq.{account_id}'
    if order:
        query['order'] = order
    return request_json(url, key, 'GET', f'/rest/v1/{table}', query=query) or []


def decimal(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def number(value: Decimal, digits: str = '0.01') -> float:
    return float(value.quantize(Decimal(digits)))


def save_json(destination: str | None, payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + '\n'
    if destination:
        target = Path(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        print(f'已写入：{target}')
    else:
        print(text, end='')


def command_seed(args: argparse.Namespace) -> None:
    url, key, email = settings(Path(args.env))
    owner = owner_id(url, key, email)
    seed = json.loads(Path(args.file).read_text(encoding='utf-8'))
    account_seed = seed.get('account')
    if not isinstance(account_seed, dict) or not account_seed.get('name'):
        raise RuntimeError('种子文件缺少 account.name。')
    accounts = select_rows(url, key, TABLES['accounts'], owner)
    if any(account['name'] == account_seed['name'] for account in accounts):
        raise RuntimeError(f"账户“{account_seed['name']}”已存在；为避免重复初始化，操作已取消。")

    account_payload = {**account_seed, 'owner_id': owner}
    created = request_json(url, key, 'POST', f"/rest/v1/{TABLES['accounts']}", body=account_payload, prefer='return=representation')
    account = created[0]
    account_id = account['id']
    for position in seed.get('positions', []):
        request_json(url, key, 'POST', f"/rest/v1/{TABLES['positions']}", body={**position, 'account_id': account_id, 'owner_id': owner}, prefer='return=minimal')
    for snapshot in seed.get('snapshots', []):
        request_json(url, key, 'POST', f"/rest/v1/{TABLES['snapshots']}", body={**snapshot, 'account_id': account_id, 'owner_id': owner}, prefer='return=minimal')
    print(f"初始化完成：账户 {account['name']}（{account_id}），持仓 {len(seed.get('positions', []))} 条，快照 {len(seed.get('snapshots', []))} 条。")


def load_data(url: str, key: str, owner: str, account_id: str | None = None) -> dict[str, list[dict[str, Any]]]:
    return {
        'accounts': select_rows(url, key, TABLES['accounts'], owner, order='created_at.asc'),
        'positions': select_rows(url, key, TABLES['positions'], owner, account_id=account_id, order='security_name.asc'),
        'closedPositions': select_rows(url, key, TABLES['closedPositions'], owner, account_id=account_id, order='closed_on.desc'),
        'watchlist': select_rows(url, key, TABLES['watchlist'], owner, account_id=account_id, order='review_on.asc.nullslast'),
        'cashflows': select_rows(url, key, TABLES['cashflows'], owner, account_id=account_id, order='occurred_on.desc'),
        'snapshots': select_rows(url, key, TABLES['snapshots'], owner, account_id=account_id, order='as_of_at.desc'),
        'auditLogs': select_rows(url, key, TABLES['auditLogs'], owner, account_id=account_id, order='created_at.desc'),
    }


def choose_account(data: dict[str, list[dict[str, Any]]], requested_id: str | None) -> dict[str, Any]:
    accounts = data['accounts']
    if requested_id:
        for account in accounts:
            if account['id'] == requested_id:
                return account
        raise RuntimeError(f'未找到指定账户：{requested_id}')
    active = next((account for account in accounts if account.get('is_active')), None)
    if active:
        return active
    if accounts:
        return accounts[0]
    raise RuntimeError('当前用户还没有账户。请先运行 seed 或在页面新增账户。')


def compact_snapshot(data: dict[str, list[dict[str, Any]]], account: dict[str, Any], details: bool) -> dict[str, Any]:
    positions = data['positions']
    snapshots = data['snapshots']
    cashflows = data['cashflows']
    closed = data['closedPositions']
    market_value = sum((decimal(row['quantity']) * decimal(row['current_price']) for row in positions), Decimal('0'))
    floating_pnl = sum(((decimal(row['current_price']) - decimal(row['average_cost'])) * decimal(row['quantity']) for row in positions), Decimal('0'))
    realized_pnl = sum((decimal(row['realized_pnl']) for row in closed), Decimal('0'))
    latest = snapshots[0] if snapshots else None
    total_assets = decimal(latest['total_assets']) if latest else decimal(account['initial_net_assets'])
    net_cashflow = sum((decimal(row['amount']) if row['flow_type'] == 'deposit' else -decimal(row['amount']) for row in cashflows), Decimal('0'))
    summary = {
        'accountName': account['name'],
        'accountId': account['id'],
        'trackingStartedOn': account['tracking_started_on'],
        'asOf': latest.get('as_of_at') if latest else account['tracking_started_on'],
        'totalAssets': number(total_assets),
        'securitiesValue': number(market_value),
        'availableCash': number(decimal(latest['available_cash'])) if latest else None,
        'withdrawableCash': number(decimal(latest['withdrawable_cash'])) if latest and latest.get('withdrawable_cash') is not None else None,
        'positionPct': number(market_value / total_assets) if total_assets else 0,
        'floatingPnl': number(floating_pnl),
        'realizedPnl': number(realized_pnl),
        'netCashflow': number(net_cashflow),
        'adjustedPnlSinceTracking': number(total_assets - decimal(account['initial_net_assets']) - net_cashflow),
        'closedCount': len(closed),
        'closedWinRate': number(Decimal(sum(1 for row in closed if decimal(row['realized_pnl']) > 0)) / Decimal(len(closed)), '0.0001') if closed else None,
    }
    result: dict[str, Any] = {
        'schemaVersion': 1,
        'generatedAt': datetime.now(timezone.utc).isoformat(),
        'dataStatus': 'manual-prices-and-snapshots',
        'account': summary,
        'currentPositions': [
            {
                'symbol': row['symbol'], 'name': row['security_name'], 'quantity': float(decimal(row['quantity'])),
                'availableQuantity': float(decimal(row['available_quantity'])), 'averageCost': float(decimal(row['average_cost'])),
                'currentPrice': float(decimal(row['current_price'])), 'marketValue': number(decimal(row['quantity']) * decimal(row['current_price'])),
                'floatingPnl': number((decimal(row['current_price']) - decimal(row['average_cost'])) * decimal(row['quantity'])),
                'floatingPnlPct': number((decimal(row['current_price']) - decimal(row['average_cost'])) / decimal(row['average_cost']), '0.0001') if decimal(row['average_cost']) else None,
                'targetPositionPct': float(decimal(row['target_position_pct'])) if row.get('target_position_pct') is not None else None,
                'stopLossPrice': float(decimal(row['stop_loss_price'])) if row.get('stop_loss_price') is not None else None,
                'distanceToStopPct': number((decimal(row['current_price']) - decimal(row['stop_loss_price'])) / decimal(row['current_price']), '0.0001') if row.get('stop_loss_price') and decimal(row['current_price']) else None,
                'plannedLossAtStop': number((decimal(row['average_cost']) - decimal(row['stop_loss_price'])) * decimal(row['quantity'])) if row.get('stop_loss_price') is not None else None,
                'plan': row.get('plan_note', ''),
            } for row in positions
        ],
        'watchlist': [
            {'symbol': row['symbol'], 'name': row['security_name'], 'status': row['status'], 'buyLow': row.get('buy_low'), 'buyHigh': row.get('buy_high'), 'invalidationCondition': row.get('invalidation_condition', ''), 'reviewOn': row.get('review_on')} for row in data['watchlist']
        ],
        'closedSummary': {
            'totalRealizedPnl': number(realized_pnl),
            'count': len(closed),
            'winRate': summary['closedWinRate'],
            'maxWin': number(max((decimal(row['realized_pnl']) for row in closed), default=Decimal('0'))),
            'maxLoss': number(min((decimal(row['realized_pnl']) for row in closed), default=Decimal('0'))),
        },
    }
    if details:
        result['details'] = data
    return result


def command_snapshot(args: argparse.Namespace) -> None:
    url, key, email = settings(Path(args.env))
    owner = owner_id(url, key, email)
    data = load_data(url, key, owner, args.account_id)
    account = choose_account(data, args.account_id)
    if args.account_id is None:
        data = load_data(url, key, owner, account['id'])
    save_json(args.output, compact_snapshot(data, account, args.details))


def command_backup(args: argparse.Namespace) -> None:
    url, key, email = settings(Path(args.env))
    owner = owner_id(url, key, email)
    data = load_data(url, key, owner)
    payload = {'schemaVersion': 1, 'exportedAt': datetime.now(timezone.utc).isoformat(), 'ownerEmail': email, **data}
    destination = args.output or str(REPO_ROOT / 'portfolio-backups' / f"portfolio-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
    save_json(destination, payload)


def main() -> int:
    parser = argparse.ArgumentParser(description='本地持仓工具：初始化、备份和供 Skill 读取的精简快照。')
    parser.add_argument('--env', default=str(DEFAULT_ENV), help='本地 Supabase 凭据文件，默认 .env.portfolio')
    subparsers = parser.add_subparsers(dest='command', required=True)
    seed = subparsers.add_parser('seed', help='将私有种子文件写入刚创建的 Supabase 用户账户')
    seed.add_argument('--file', default=str(REPO_ROOT / 'config' / 'portfolio-seed.local.json'))
    seed.set_defaults(handler=command_seed)
    snapshot = subparsers.add_parser('snapshot', help='输出供金融 Skill 读取的默认精简快照')
    snapshot.add_argument('--account-id')
    snapshot.add_argument('--details', action='store_true', help='额外包含完整明细和审计日志')
    snapshot.add_argument('--output', help='未指定时输出到标准输出')
    snapshot.set_defaults(handler=command_snapshot)
    backup = subparsers.add_parser('backup', help='导出完整私有 JSON 备份')
    backup.add_argument('--output', help='默认写入忽略的 portfolio-backups/ 目录')
    backup.set_defaults(handler=command_backup)
    args = parser.parse_args()
    try:
        args.handler(args)
        return 0
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f'操作失败：{error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
