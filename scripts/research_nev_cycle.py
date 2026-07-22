#!/usr/bin/env python3
"""Build the price/valuation and quarterly-financial evidence tables for the 2021-23 A-share new-energy cycle."""

from __future__ import annotations

import csv
import datetime as dt
import json
import math
import pathlib
import time
import urllib.parse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "行业复盘" / "新能源2021-2023复盘" / "data"
OUT.mkdir(parents=True, exist_ok=True)

COMPANIES = {
    "002594": ("比亚迪", "电动车/动力电池"),
    "300750": ("宁德时代", "动力电池"),
    "002709": ("天赐材料", "电解液/六氟磷酸锂"),
    "002176": ("江特电机", "锂资源"),
    "002466": ("天齐锂业", "锂资源"),
    "300274": ("阳光电源", "光伏逆变器/储能"),
    "600438": ("通威股份", "硅料/电池片"),
    "601012": ("隆基绿能", "硅片/组件"),
    "300014": ("亿纬锂能", "动力/储能电池"),
    "300438": ("鹏辉能源", "储能电池"),
    "002518": ("科士达", "储能PCS/UPS"),
    "603606": ("东方电缆", "海缆"),
    "002487": ("大金重工", "风电塔筒/海工"),
    "300450": ("先导智能", "锂电设备"),
    "300693": ("盛弘股份", "充电桩/储能PCS"),
    "300713": ("英可瑞", "充电模块"),
    "002506": ("协鑫集成", "光伏组件"),
}

CORE = ["002594", "300750", "002709", "002176", "300274", "600438", "601012", "603606"]


def get_json(url: str, retries: int = 3):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"},
    )
    last = None
    for n in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as exc:  # pragma: no cover - network retry
            last = exc
            time.sleep(0.6 * (n + 1))
    raise last


def secid(code: str) -> str:
    return ("1." if code.startswith("6") else "0.") + code


def kline_url(code: str, fqt: int = 1) -> str:
    params = {
        "secid": secid(code),
        "klt": 101,
        "fqt": fqt,
        "beg": "20190101",
        "end": "20260722",
        "lmt": 5000,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61",
    }
    return "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urllib.parse.urlencode(params)


def fetch_prices(code: str, fqt: int = 1):
    url = kline_url(code, fqt)
    data = get_json(url)["data"]
    rows = []
    for line in data["klines"]:
        x = line.split(",")
        rows.append(
            {
                "date": dt.date.fromisoformat(x[0]),
                "open": float(x[1]),
                "close": float(x[2]),
                "high": float(x[3]),
                "low": float(x[4]),
                "volume": float(x[5]),
                "amount": float(x[6]),
            }
        )
    return rows, url


def max_drawup(rows, start=dt.date(2020, 1, 2), end=dt.date(2023, 12, 29)):
    xs = [r for r in rows if start <= r["date"] <= end]
    low = xs[0]
    best = (0.0, low, low)
    for r in xs:
        if r["close"] < low["close"]:
            low = r
        gain = r["close"] / low["close"] - 1
        if gain > best[0]:
            best = (gain, low, r)
    return best


def max_rolling_12m(rows, start=dt.date(2021, 1, 4), end=dt.date(2023, 12, 29)):
    xs = [r for r in rows if dt.date(2020, 1, 1) <= r["date"] <= end]
    best = (-math.inf, None, None)
    for i, r in enumerate(xs):
        if r["date"] < start:
            continue
        cutoff = r["date"] - dt.timedelta(days=365)
        eligible = [z for z in xs[: i + 1] if cutoff <= z["date"] <= r["date"]]
        lo = min(eligible, key=lambda z: z["close"])
        gain = r["close"] / lo["close"] - 1
        if gain > best[0]:
            best = (gain, lo, r)
    return best


def max_drawdown_after(rows, peak_date, end=dt.date(2023, 12, 29)):
    xs = [r for r in rows if peak_date <= r["date"] <= end]
    peak = xs[0]
    worst = (0.0, peak, peak)
    for r in xs:
        if r["close"] > peak["close"]:
            peak = r
        dd = r["close"] / peak["close"] - 1
        if dd < worst[0]:
            worst = (dd, peak, r)
    return worst


def nearest(rows, date):
    xs = [r for r in rows if r["date"] <= date]
    return xs[-1] if xs else None


def valuation_url(code: str, date: dt.date) -> str:
    flt = f'(SECURITY_CODE="{code}")(TRADE_DATE=\'{date.isoformat()}\')'
    params = {
        "reportName": "RPT_VALUEANALYSIS_DET",
        "columns": "ALL",
        "filter": flt,
        "pageNumber": 1,
        "pageSize": 5,
    }
    return "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(params)


def fetch_valuation(code: str, date: dt.date):
    url = valuation_url(code, date)
    obj = get_json(url)
    rows = (obj.get("result") or {}).get("data") or []
    return (rows[0] if rows else {}), url


def report_url(report: str, code: str, page_size: int = 500) -> str:
    params = {
        "reportName": report,
        "columns": "ALL",
        "filter": f'(SECURITY_CODE="{code}")',
        "pageNumber": 1,
        "pageSize": page_size,
    }
    return "https://datacenter-web.eastmoney.com/api/data/v1/get?" + urllib.parse.urlencode(params)


def fetch_report(report: str, code: str):
    url = report_url(report, code)
    obj = get_json(url)
    return (obj.get("result") or {}).get("data") or [], url


def dedupe_period(rows):
    """Prefer consolidated/current report data and the latest notice for each report date."""
    out = {}
    for r in rows:
        date = (r.get("REPORT_DATE") or r.get("REPORTDATE") or "")[:10]
        if not date:
            continue
        prev = out.get(date)
        score = (r.get("REPORT_TYPE_CODE") == "001", r.get("DATA_STATE") == "2", r.get("NOTICE_DATE") or "")
        pscore = (-1, -1, "") if prev is None else (
            prev.get("REPORT_TYPE_CODE") == "001",
            prev.get("DATA_STATE") == "2",
            prev.get("NOTICE_DATE") or "",
        )
        if prev is None or score > pscore:
            out[date] = r
    return out


def ttm_from_cumulative(fin_by_date, field, report_date):
    d = dt.date.fromisoformat(report_date)
    cur = fin_by_date.get(report_date, {}).get(field)
    if cur is None:
        return None
    if d.month == 12:
        return cur
    prev_year = f"{d.year-1}-12-31"
    prev_same = f"{d.year-1}-{d.month:02d}-{d.day:02d}"
    a = fin_by_date.get(prev_year, {}).get(field)
    b = fin_by_date.get(prev_same, {}).get(field)
    if a is None or b is None:
        return None
    return cur + a - b


def prior_trading_rows(rows, date, n):
    xs = [r for r in rows if r["date"] < date]
    return xs[-n:]


def forward_return(rows, announce_date, days):
    # A-share periodic reports are normally released after the close; the event
    # day is therefore the first trading day strictly after NOTICE_DATE.
    xs = [r for r in rows if r["date"] > announce_date]
    if not xs:
        return None, None
    base = nearest(rows, announce_date)
    if base is None:
        return None, None
    target = xs[min(days - 1, len(xs) - 1)] if days > 0 else base
    return target["close"] / base["close"] - 1, target["date"]


def main():
    summary = []
    quarterly = []
    source_index = []
    all_prices = {}
    bench_prices, bench_url = fetch_prices("399808", 0)

    for code, (name, sector) in COMPANIES.items():
        prices, purl = fetch_prices(code, 1)
        raw_prices, rawurl = fetch_prices(code, 0)
        all_prices[code] = prices
        gain, low, peak = max_drawup(prices)
        rgain, rlow, rpeak = max_rolling_12m(prices)
        dd, ddpeak, trough = max_drawdown_after(prices, peak["date"])
        dd_current, ddpeak_current, trough_current = max_drawdown_after(
            prices, peak["date"], end=dt.date(2026, 7, 22)
        )
        current = nearest(prices, dt.date(2026, 7, 22))
        cycle_end = nearest(prices, dt.date(2023, 12, 29))
        baseline = nearest(prices, dt.date(2021, 1, 4))
        avg_amt = sum(r["amount"] for r in prior_trading_rows(prices, low["date"], 60)) / max(
            1, len(prior_trading_rows(prices, low["date"], 60))
        )
        baseline_prior = prior_trading_rows(prices, baseline["date"] + dt.timedelta(days=1), 60)
        baseline_avg_amt = sum(r["amount"] for r in baseline_prior) / max(1, len(baseline_prior))
        val_low, vlow_url = fetch_valuation(code, low["date"])
        val_base, vbase_url = fetch_valuation(code, baseline["date"])
        val_peak, vpeak_url = fetch_valuation(code, peak["date"])
        val_current, vcur_url = fetch_valuation(code, current["date"])
        summary.append(
            {
                "code": code,
                "name": name,
                "sector": sector,
                "start_date": low["date"].isoformat(),
                "start_adj_close": low["close"],
                "peak_date": peak["date"].isoformat(),
                "peak_adj_close": peak["close"],
                "max_gain_pct": gain * 100,
                "days_to_peak": (peak["date"] - low["date"]).days,
                "rolling12_start": rlow["date"].isoformat(),
                "rolling12_peak": rpeak["date"].isoformat(),
                "rolling12_gain_pct": rgain * 100,
                "post_peak_dd_to_2023_pct": dd * 100,
                "post_peak_trough_date": trough["date"].isoformat(),
                "post_peak_dd_to_current_pct": dd_current * 100,
                "post_peak_trough_current_date": trough_current["date"].isoformat(),
                "cycle_end_close": cycle_end["close"],
                "current_date": current["date"].isoformat(),
                "current_close": current["close"],
                "current_vs_peak_pct": (current["close"] / peak["close"] - 1) * 100,
                "avg_amount_60d_before_start_cny": avg_amt,
                "baseline_date": baseline["date"].isoformat(),
                "market_cap_baseline_cny": val_base.get("TOTAL_MARKET_CAP"),
                "avg_amount_60d_to_baseline_cny": baseline_avg_amt,
                "market_cap_start_cny": val_low.get("TOTAL_MARKET_CAP"),
                "pe_ttm_start": val_low.get("PE_TTM"),
                "pe_ttm_peak": val_peak.get("PE_TTM"),
                "pe_ttm_current": val_current.get("PE_TTM"),
                "price_source": purl,
                "raw_price_source": rawurl,
                "valuation_start_source": vlow_url,
                "valuation_baseline_source": vbase_url,
                "valuation_peak_source": vpeak_url,
                "valuation_current_source": vcur_url,
            }
        )
        source_index.extend(
            [
                {"code": code, "kind": "price_adjusted", "url": purl},
                {"code": code, "kind": "price_raw", "url": rawurl},
                {"code": code, "kind": "valuation_start", "url": vlow_url},
                {"code": code, "kind": "valuation_baseline", "url": vbase_url},
                {"code": code, "kind": "valuation_peak", "url": vpeak_url},
                {"code": code, "kind": "valuation_current", "url": vcur_url},
            ]
        )

        if code not in CORE:
            continue
        main_fin, main_url = fetch_report("RPT_LICO_FN_CPD", code)
        income, income_url = fetch_report("RPT_DMSK_FN_INCOME", code)
        cash, cash_url = fetch_report("RPT_DMSK_FN_CASHFLOW", code)
        balance, balance_url = fetch_report("RPT_DMSK_FN_BALANCE", code)
        m = dedupe_period(main_fin)
        inc = dedupe_period(income)
        cf = dedupe_period(cash)
        bal = dedupe_period(balance)
        source_index.extend(
            [
                {"code": code, "kind": "main_fin", "url": main_url},
                {"code": code, "kind": "income", "url": income_url},
                {"code": code, "kind": "cashflow", "url": cash_url},
                {"code": code, "kind": "balance", "url": balance_url},
            ]
        )
        # Covers the quarter before the broad launch through two quarters after the main decline signal.
        for report_date in sorted(d for d in set(m) | set(inc) | set(cf) | set(bal) if "2020-09-30" <= d <= "2023-12-31"):
            mr = m.get(report_date, {})
            ir = inc.get(report_date, {})
            cr = cf.get(report_date, {})
            br = bal.get(report_date, {})
            notice = (mr.get("NOTICE_DATE") or ir.get("NOTICE_DATE") or cr.get("NOTICE_DATE") or br.get("NOTICE_DATE") or "")[:10]
            if not notice:
                continue
            ad = dt.date.fromisoformat(notice)
            prev = nearest(raw_prices, ad)
            r1, d1 = forward_return(raw_prices, ad, 1)
            r5, d5 = forward_return(raw_prices, ad, 5)
            r20, d20 = forward_return(raw_prices, ad, 20)
            b1, _ = forward_return(bench_prices, ad, 1)
            b5, _ = forward_return(bench_prices, ad, 5)
            b20, _ = forward_return(bench_prices, ad, 20)
            revenue = mr.get("TOTAL_OPERATE_INCOME") or ir.get("TOTAL_OPERATE_INCOME")
            net_profit = mr.get("PARENT_NETPROFIT") or ir.get("PARENT_NETPROFIT")
            gross_margin = mr.get("XSMLL")
            ocf = cr.get("NETCASH_OPERATE")
            capex = cr.get("CONSTRUCT_LONG_ASSET")
            quarterly.append(
                {
                    "code": code,
                    "name": name,
                    "sector": sector,
                    "report_date": report_date,
                    "notice_date": notice,
                    "revenue_cny": revenue,
                    "revenue_yoy_pct": mr.get("YSTZ"),
                    "net_profit_cny": net_profit,
                    "net_profit_yoy_pct": mr.get("SJLTZ"),
                    "gross_margin_pct": gross_margin,
                    "ocf_cny": ocf,
                    "inventory_cny": br.get("INVENTORY"),
                    "accounts_receivable_cny": br.get("ACCOUNTS_RECE"),
                    "capex_cny": capex,
                    "pre_close_raw": prev["close"] if prev else None,
                    "ret_1d_pct": None if r1 is None else r1 * 100,
                    "ret_5d_pct": None if r5 is None else r5 * 100,
                    "ret_20d_pct": None if r20 is None else r20 * 100,
                    "excess_1d_pct": None if r1 is None or b1 is None else (r1 - b1) * 100,
                    "excess_5d_pct": None if r5 is None or b5 is None else (r5 - b5) * 100,
                    "excess_20d_pct": None if r20 is None or b20 is None else (r20 - b20) * 100,
                    "date_1d": d1.isoformat() if d1 else None,
                    "date_5d": d5.isoformat() if d5 else None,
                    "date_20d": d20.isoformat() if d20 else None,
                    "ttm_revenue_cny": ttm_from_cumulative(m, "TOTAL_OPERATE_INCOME", report_date),
                    "ttm_net_profit_cny": ttm_from_cumulative(m, "PARENT_NETPROFIT", report_date),
                    "financial_source": main_url,
                    "cashflow_source": cash_url,
                    "balance_source": balance_url,
                    "price_source": rawurl,
                    "benchmark_source": bench_url,
                }
            )
        time.sleep(0.1)

    def write_csv(name, rows):
        path = OUT / name
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    write_csv("price_valuation_summary.csv", summary)
    write_csv("quarterly_event_study.csv", quarterly)
    write_csv("source_index.csv", source_index)
    print(json.dumps({"summary_rows": len(summary), "quarterly_rows": len(quarterly), "out": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
