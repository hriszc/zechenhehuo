# -*- coding: utf-8 -*-
"""
拉取 A 股宽基指数与个股历史日线数据（baostock，免费开源，服务器国内可直连）
- 指数：沪深300(000300)、中证500(000905)、中证1000(000852)、上证指数(000001)、深证成指(399001)
- 个股：贵州茅台、招商银行、宁德时代、中国平安、长江电力（前复权 adjustflag=2）
- 数据落盘 data/*.csv（date,open,close,high,low,volume,amount,turn,pctChg）
用法：python3 scripts/fetch_baostock.py
"""
import os
import time
import socket

# 清空代理环境变量（本机 127.0.0.1:7892 代理无法访问行情源，必须直连）
for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
          'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy']:
    os.environ.pop(k, None)

# baostock 底层 socket 无超时，设置默认超时避免无限阻塞
socket.setdefaulttimeout(60)

import baostock as bs

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
os.makedirs(OUT_DIR, exist_ok=True)

FIELDS = 'date,open,close,high,low,volume,amount,turn,pctChg'

# (baostock代码, 文件名, 名称, 起始日期, 复权: 3=不复权 2=前复权 1=后复权)
TARGETS = [
    ('sh.000300', 'sh000300', '沪深300', '2004-01-01', '3'),
    ('sh.000905', 'sh000905', '中证500', '2004-01-01', '3'),
    ('sh.000852', 'sh000852', '中证1000', '2004-01-01', '3'),
    ('sh.000001', 'sh000001', '上证指数', '1990-12-19', '3'),
    ('sz.399001', 'sz399001', '深证成指', '1991-04-03', '3'),
    ('sh.600519', 'sh600519', '贵州茅台', '2001-08-27', '2'),
    ('sh.600036', 'sh600036', '招商银行', '2002-04-09', '2'),
    ('sz.300750', 'sz300750', '宁德时代', '2018-06-11', '2'),
    ('sh.601318', 'sh601318', '中国平安', '2007-03-01', '2'),
    ('sh.600900', 'sh600900', '长江电力', '2003-11-18', '2'),
]

lg = bs.login()
print('login:', lg.error_code, lg.error_msg)


def query_with_retry(code, fields, start, end, adj, tries=4):
    """查询并自动重连重试（baostock 偶发阻塞/断连）"""
    for i in range(tries):
        try:
            rs = bs.query_history_k_data_plus(
                code, fields, start_date=start, end_date=end,
                frequency='d', adjustflag=adj)
            rows = []
            while (rs.error_code == '0') and rs.next():
                rows.append(rs.get_row_data())
            if rs.error_code != '0':
                raise RuntimeError(f'{rs.error_code} {rs.error_msg}')
            return rows
        except Exception as e:
            print(f'  retry {i+1}/{tries} {code}: {e}')
            try:
                bs.logout()
            except Exception:
                pass
            time.sleep(3)
            bs.login()
    return []


for code, fname, name, start, adj in TARGETS:
    rows = query_with_retry(code, FIELDS, start, '2026-08-01', adj)
    if rows:
        path = os.path.join(OUT_DIR, f'{fname}.csv')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(FIELDS + '\n')
            for r in rows:
                f.write(','.join(r) + '\n')
        print(f'{name} {fname}: {len(rows)} 行  {rows[0][0]} ~ {rows[-1][0]}')
    else:
        print(f'{name} {fname}: 无数据')
    time.sleep(1.5)

bs.logout()
print('done')
