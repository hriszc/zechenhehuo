# -*- coding: utf-8 -*-
"""
拉取指数全收益（总回报）口径日线数据
- 真实全收益：中证指数官网 index-perf 接口
    H00300 沪深300全收益 / H00905 中证500全收益 / H00852 中证1000全收益
- 近似全收益：上证指数、深证成指（无官方全收益历史数据），用"价格收益 + 历史平均股息率日摊"补齐
- 输出：data/h00300.csv h00905.csv h00852.csv sh000001_tr.csv sz399001_tr.csv
  （列：date,close；close 为全收益点位）
用法：python3 scripts/fetch_total_return.py
"""
import os
import time
import requests
import pandas as pd

# 清空代理环境变量（本机 127.0.0.1:7892 代理无法访问国内数据源，必须直连）
for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
          'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']:
    os.environ.pop(k, None)

UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0 Safari/537.36')
H = {'User-Agent': UA, 'Referer': 'https://www.csindex.com.cn/'}
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
TRADING_DAYS = 252

# 真实全收益指数（中证官网）
TR = {
    'H00300': 'h00300',   # 沪深300全收益
    'H00905': 'h00905',   # 中证500全收益
    'H00852': 'h00852',   # 中证1000全收益
}


def fetch_csindex(code):
    url = (f'https://www.csindex.com.cn/csindex-home/perf/index-perf'
           f'?indexCode={code}&startDate=20050104&endDate=20260731')
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=30, headers=H)
            j = r.json()
            if j.get('code') == '200' and j.get('data'):
                return [(d['tradeDate'], float(d['close'])) for d in j['data']]
            print(f'  {code} attempt{attempt}: code={j.get("code")} rows={len(j.get("data") or [])}')
        except Exception as e:
            print(f'  {code} attempt{attempt}: {type(e).__name__} {str(e)[:80]}')
        time.sleep(2)
    return []


def approx_total_return(price_csv, div_yield, out_name):
    """近似全收益 = 价格日收益 + 年化股息率/252（复利叠加）"""
    df = pd.read_csv(os.path.join(OUT_DIR, price_csv))
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    r = df['close'].pct_change().fillna(0)
    tr = (1 + r + div_yield / TRADING_DAYS).cumprod()
    out = pd.DataFrame({'date': df['date'].dt.strftime('%Y-%m-%d'),
                        'close': (df['close'].iloc[0] * tr).round(4)})
    path = os.path.join(OUT_DIR, out_name)
    out.to_csv(path, index=False)
    print(f'近似全收益 {out_name}: {len(out)} 行 {out.iloc[0]["date"]} ~ {out.iloc[-1]["date"]} '
          f'(股息率近似 {div_yield*100:.1f}%/年)')
    return len(out)


def main():
    for code, fname in TR.items():
        rows = fetch_csindex(code)
        if rows:
            path = os.path.join(OUT_DIR, f'{fname}.csv')
            with open(path, 'w', encoding='utf-8') as f:
                f.write('date,close\n')
                for d, c in rows:
                    f.write(f'{d[:4]}-{d[4:6]}-{d[6:8]},{c}\n')
            print(f'{code} {fname}: {len(rows)} 行 {rows[0][0]} ~ {rows[-1][0]}')
        else:
            print(f'{code}: 拉取失败')
        time.sleep(1)

    # 上证指数：历史平均股息率约 2%（大盘蓝筹，近似）
    approx_total_return('sh000001.csv', 0.02, 'sh000001_tr.csv')
    # 深证成指：历史平均股息率约 1.5%（偏成长，近似）
    approx_total_return('sz399001.csv', 0.015, 'sz399001_tr.csv')

    print('done')


if __name__ == '__main__':
    main()
