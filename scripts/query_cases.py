# -*- coding: utf-8 -*-
"""查询文章需要的具体案例数字"""
import os
import json
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')


def load(fname):
    df = pd.read_csv(os.path.join(DATA_DIR, fname))
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)


def ret_between(df, d1, d2):
    """d1 收盘买入，d2 收盘卖出（含两端交易日）"""
    a = df[df['date'] >= pd.Timestamp(d1)].iloc[0]['close']
    b = df[df['date'] <= pd.Timestamp(d2)].iloc[-1]['close']
    days = len(df[(df['date'] >= a if False else df['date'] >= pd.Timestamp(d1)) & (df['date'] <= pd.Timestamp(d2))])
    return a, b, days, b / a - 1


df300 = load('h00300.csv')  # 沪深300 全收益（含分红再投资）
dfmaotai = load('sh600519.csv')
dfpingan = load('sh601318.csv')

print('== 沪深300 关键点位 ==')
print('2007-10-16 最高点收盘:', df300.loc[df300['date'] == '2007-10-16', 'close'].values)
print('2015-06-12 高点收盘:', df300.loc[df300['date'] == '2015-06-12', 'close'].values)
print('2021-02-18 高点收盘:', df300.loc[df300['date'] == '2021-02-18', 'close'].values)
print('2008-11-04 低点收盘:', df300.loc[df300['date'] == '2008-11-04', 'close'].values)
print('2024-02-05 低点收盘:', df300.loc[df300['date'] == '2024-02-05', 'close'].values)

cases = [
    ('2007-10-16 买, 2008-11-04 卖(1年熊市)', '2007-10-16', '2008-11-04'),
    ('2007-10-16 买, 2012-10-16 卖(5年)', '2007-10-16', '2012-10-16'),
    ('2007-10-16 买, 2017-10-16 卖(10年)', '2007-10-16', '2017-10-16'),
    ('2007-10-16 买, 2026-07-31 卖(持有至今)', '2007-10-16', '2026-07-31'),
    ('2008-11-04 买, 2013-11-04 卖(5年)', '2008-11-04', '2013-11-04'),
    ('2015-06-12 买, 2020-06-12 卖(5年)', '2015-06-12', '2020-06-12'),
    ('2015-06-12 买, 2026-07-31 卖(持有至今)', '2015-06-12', '2026-07-31'),
    ('2018-01-24 买, 2023-01-24 卖(5年)', '2018-01-24', '2023-01-24'),
    ('2021-02-18 买, 2026-07-31 卖(持有至今)', '2021-02-18', '2026-07-31'),
    ('2005-01-04 买, 2008-01-04 卖(3年)', '2005-01-04', '2008-01-04'),
    ('2005-01-04 买, 2010-01-04 卖(5年)', '2005-01-04', '2010-01-04'),
    ('2005-01-04 买, 2015-01-04 卖(10年)', '2005-01-04', '2015-01-04'),
]
print('\n== 沪深300 案例 ==')
for label, d1, d2 in cases:
    a, b, days, r = ret_between(df300, d1, d2)
    annual = (1 + r) ** (252 / days) - 1 if r > -1 else float('-inf')
    print(f'{label}: 买入{a:.0f} → 卖出{b:.0f} 收益{r*100:+.1f}% (年化{annual*100:+.1f}%) 持有{days}个交易日')

print('\n== 茅台 案例 ==')
for label, d1, d2 in [('2021-02-18 高点买, 2026-07-31', '2021-02-18', '2026-07-31'),
                      ('2021-02-18 买, 2023-02-18 卖(2年)', '2021-02-18', '2023-02-18'),
                      ('2005-01-04 买, 2015-01-04 卖(10年)', '2005-01-04', '2015-01-04'),
                      ('2013-01-01 买, 2018-01-01 卖(5年)', '2013-01-01', '2018-01-01')]:
    a, b, days, r = ret_between(dfmaotai, d1, d2)
    annual = (1 + r) ** (252 / days) - 1 if r > -1 else float('-inf')
    print(f'{label}: 买入{a:.0f} → 卖出{b:.0f} 收益{r*100:+.1f}% (年化{annual*100:+.1f}%)')

print('\n== 平安 案例 ==')
for label, d1, d2 in [('2017-11-22 高点买, 2026-07-31', '2017-11-22', '2026-07-31'),
                      ('2008-01 买, 2013-01 卖(5年)', '2008-01-01', '2013-01-01')]:
    a, b, days, r = ret_between(dfpingan, d1, d2)
    annual = (1 + r) ** (252 / days) - 1 if r > -1 else float('-inf')
    print(f'{label}: 买入{a:.0f} → 卖出{b:.0f} 收益{r*100:+.1f}% (年化{annual*100:+.1f}%)')

# 沪深300 持有1/3/5/10年年化收益分位数（从 JSON）
with open(os.path.join(DATA_DIR, 'stats_summary.json'), encoding='utf-8') as f:
    s = json.load(f)
rec = s['main']['h00300']['periods']
print('\n== 沪深300 任意时点买入持有 N 年年化收益分位数 ==')
for label in ['1年', '3年', '5年', '10年']:
    p = rec[label]
    print(f'{label}: P25={p["年化收益P25"]*100:+.1f}% P50={p["年化收益P50"]*100:+.1f}% '
          f'P75={p["年化收益P75"]*100:+.1f}% 正收益概率={p["正收益概率"]*100:.0f}%')
