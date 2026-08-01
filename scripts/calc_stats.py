# -*- coding: utf-8 -*-
"""
A 股投资统计（v2）：各持有周期收益为正的概率、年化预期收益、波动率
- 主统计区间：2005-01-04 起（沪深300 基日），各标的统一可比
- 上证指数另附 1990-12-19 起（超长历史参考，注明早期制度差异）
- 方法：滚动持有期收益率（重叠样本，Siegel《股市长线法宝》做法）
  自然年收益（不重叠样本）对照
- 输出：data/stats_summary.json + data/annual_returns.csv + data/hold_annual.json
用法：python3 scripts/calc_stats.py
"""
import os
import json
import glob
import numpy as np
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
TRADING_DAYS = 252
MAIN_SINCE = '2005-01-04'

PERIODS = [
    (1, '1日'), (5, '1周'), (21, '1月'), (63, '1季'), (126, '半年'),
    (252, '1年'), (504, '2年'), (756, '3年'), (1260, '5年'), (2520, '10年'),
]

META = {
    # 指数：全收益（总回报）口径
    #   h00300/h00905/h00852 = 中证官网真实全收益（含分红再投资）
    #   sh000001_tr/sz399001_tr = 价格指数 + 历史平均股息率日摊的近似全收益
    'h00300': '沪深300',
    'h00905': '中证500',
    'h00852': '中证1000',
    'sh000001_tr': '上证指数',
    'sz399001_tr': '深证成指',
    # 个股：前复权（已含分红再投资近似）
    'sh600519': '贵州茅台',
    'sh600036': '招商银行',
    'sh601318': '中国平安',
    'sh600900': '长江电力',
    'sz300750': '宁德时代',
}

STOCK_IPO = {  # 上市日（晚于2005的个股从上市日起统计）
    'sh600519': '2001-08-27', 'sh600036': '2002-04-09', 'sh601318': '2007-03-01',
    'sh600900': '2003-11-18', 'sz300750': '2018-06-11',
}


def load_close(fname):
    df = pd.read_csv(os.path.join(DATA_DIR, fname))
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    return df['date'], df['close'].astype(float)


def rolling_stats(close):
    out = {}
    n = len(close)
    for days, label in PERIODS:
        if n <= days:
            out[label] = None
            continue
        r = close[days:].values / close[:-days].values - 1.0
        pos = (r > 0).mean()
        neg_big = (r < -0.2).mean()
        geo_annual = (np.exp(np.log1p(r).mean()) ** (TRADING_DAYS / days) - 1)
        arith_annual = (r.mean() + 1) ** (TRADING_DAYS / days) - 1
        vol_annual = r.std(ddof=1) * np.sqrt(TRADING_DAYS / days)
        out[label] = {
            '样本数': int(len(r)),
            '正收益概率': round(float(pos), 4),
            '亏损超20%概率': round(float(neg_big), 4),
            '平均单期收益': round(float(r.mean()), 4),
            '中位数单期收益': round(float(np.median(r)), 4),
            '年化收益_几何': round(float(geo_annual), 4),
            '年化收益_算术': round(float(arith_annual), 4),
            '年化波动率': round(float(vol_annual), 4),
            '最差单期收益': round(float(r.min()), 4),
            '最好单期收益': round(float(r.max()), 4),
            '年化收益P25': round(float(np.percentile((1 + r) ** (TRADING_DAYS / days) - 1, 25)), 4),
            '年化收益P50': round(float(np.percentile((1 + r) ** (TRADING_DAYS / days) - 1, 50)), 4),
            '年化收益P75': round(float(np.percentile((1 + r) ** (TRADING_DAYS / days) - 1, 75)), 4),
        }
    return out


def annual_returns(date, close, exclude_last_year=True):
    s = pd.Series(close.values, index=date)
    ye = s.groupby(s.index.year).last()
    rets = ye.pct_change().dropna()
    if exclude_last_year:
        rets = rets[rets.index < 2026]
    return [{'年': int(y), '收益': round(float(r), 4)} for y, r in rets.items()]


def build(code, since=None):
    name = META[code]
    date, close = load_close(f'{code}.csv')
    if since:
        mask = date >= pd.Timestamp(since)
        date, close = date[mask], close[mask]
        if len(close) == 0:
            return None
    stats = rolling_stats(close)
    ann = annual_returns(date, close)
    total_annual = (close.iloc[-1] / close.iloc[0]) ** (TRADING_DAYS / max(len(close) - 1, 1)) - 1
    return {
        'name': name, 'code': code,
        'start': str(date.iloc[0].date()), 'end': str(date.iloc[-1].date()),
        'rows': int(len(close)),
        'total_return': round(float(close.iloc[-1] / close.iloc[0] - 1), 4),
        'total_annual': round(float(total_annual), 4),
        'periods': stats, 'annual_returns': ann,
    }


def print_table(title, rec):
    print(f"\n=== {title} ===")
    print(f"{'持有期':<6}{'正收益概率':>10}{'年化收益(几何)':>14}{'年化波动率':>12}{'最差单期':>10}{'样本数':>8}")
    for days, label in PERIODS:
        s = rec['periods'].get(label)
        if s is None:
            continue
        print(f"{label:<6}{s['正收益概率']*100:>9.1f}%{s['年化收益_几何']*100:>13.1f}%"
              f"{s['年化波动率']*100:>11.1f}%{s['最差单期收益']*100:>9.1f}%{s['样本数']:>8}")
    ann = rec['annual_returns']
    if ann:
        npos = sum(1 for a in ann if a['收益'] > 0)
        print(f"自然年收益: {len(ann)}个完整年度 正收益{npos}年({npos/len(ann)*100:.0f}%) "
              f"最好{max(a['收益'] for a in ann)*100:.0f}% 最差{min(a['收益'] for a in ann)*100:.0f}%")


def main():
    summary = {'main': {}, 'appendix': {}}
    codes = list(META.keys())

    # 主表：统一 2005 起（个股按上市日）
    for code in codes:
        since = MAIN_SINCE
        rec = build(code, since)
        if rec and len(rec['annual_returns']) >= 1:
            summary['main'][code] = rec
            print_table(f"{rec['name']}（{rec['start']} 起）", rec)

    # 附录：上证指数近似全收益全历史（1990 起）
    rec = build('sh000001_tr')
    if rec:
        summary['appendix']['sh000001_1990'] = rec
        print_table(f"上证指数 全历史（{rec['start']} 起）", rec)

    out_path = os.path.join(DATA_DIR, 'stats_summary.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(f"\n已写入 {out_path}")

    # 年度收益 CSV（供文章附录）
    rows = []
    for code in codes:
        rec = summary['main'].get(code)
        if not rec:
            continue
        for a in rec['annual_returns']:
            rows.append({'标的': rec['name'], '年份': a['年'], '收益': a['收益']})
    if rows:
        df = pd.DataFrame(rows).pivot(index='年份', columns='标的', values='收益')
        df.to_csv(os.path.join(DATA_DIR, 'annual_returns.csv'), encoding='utf-8-sig')
        print('年度收益表已写入 data/annual_returns.csv')


if __name__ == '__main__':
    main()
