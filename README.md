# 写文章：A 股投资的概率统计

用 2005 年至今（20 余年）的真实行情数据，从概率统计视角写一篇面向个人投资者的 A 股投资文章。

## 交付物

| 文件 | 说明 |
| --- | --- |
| `A股投资概率账.md` | 主交付物：文章（含全部数据表格、案例、结论） |
| `data/stats_summary.json` | 全部统计结果（各持有期正收益概率、年化收益、波动率、分位数） |
| `data/annual_returns.csv` | 2005-2025 年各标的自然年收益表 |
| `data/h00300.csv` 等 | 指数全收益日线（中证官网 H00300/H00905/H00852，含分红再投资） |
| `data/sh000001_tr.csv` 等 | 上证/深证近似全收益日线（价格收益 + 股息率日摊） |
| `data/sh600519.csv` 等 | 个股前复权日线（baostock） |
| `scripts/fetch_baostock.py` | 个股数据拉取（baostock 免费行情库，前复权） |
| `scripts/fetch_total_return.py` | 指数全收益数据拉取（中证官网 + 近似法） |
| `scripts/calc_stats.py` | 统计计算脚本（滚动持有期收益 + 自然年收益） |
| `scripts/query_cases.py` | 文章具体案例查询脚本（牛市顶点/熊市底部买入等） |

## 统计口径

- **指数：全收益（总回报）口径**。沪深300/中证500/中证1000 直接采用中证指数官网发布的全收益指数日线（H00300/H00905/H00852，真实含分红再投资）；上证指数/深证成指无官方全收益历史数据，用"价格收益 + 历史平均股息率日摊"近似（上证 2%/年、深证成指 1.5%/年），方法详见文章附录 D。
- **个股：前复权口径**（baostock 前复权，含分红再投资近似）。
- 主区间：2005-01-04 至 2026-07-31（沪深300 基日至今）；上证指数另附 1990 年开市至今全历史。
- 方法：滚动持有期收益（任意交易日买入持有 N 日，Siegel《股市长线法宝》做法）；自然年收益作对照。

## 复现方法

```bash
pip3 install baostock pandas numpy requests
python3 scripts/fetch_baostock.py        # 拉取个股 → data/sh*.csv
python3 scripts/fetch_total_return.py    # 拉取全收益指数 → data/h00300.csv 等
python3 scripts/calc_stats.py            # 统计计算 → data/stats_summary.json、annual_returns.csv
python3 scripts/query_cases.py           # 案例查询
```

> 免责声明：本文仅为历史数据的概率统计展示，不构成投资建议。
