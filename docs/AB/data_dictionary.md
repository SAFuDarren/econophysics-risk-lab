# 真实市场数据字典

对象：Binance Vision，BTCUSDT spot，2025-01-01 至 2025-12-31 UTC，5 分钟。12 个月归档，加一个 2024-12-31 日归档供首根收益取前收盘。来源与 SHA256 在 data/manifests/binance_btcusdt_2025_5m_v1/download_manifest.json。官方 K 线定义见 [Binance spot market data](https://developers.binance.com/en/docs/catalog/core-trading-spot-trading/api/rest-api/market)。

| 原始列序号（从 1 起） | 处理字段 | 含义／单位 |
|---|---|---|
| 1 | open_time_us | K 线起始时间，标准化为 Unix 微秒 |
| 2 | open | 首笔价格，USDT/BTC |
| 3 | high | 区间最高价，USDT/BTC |
| 4 | low | 区间最低价，USDT/BTC |
| 5 | close | 末笔价格，USDT/BTC |
| 6 | volume | 基础资产成交量，BTC |
| 7 | close_time_us | 区间结束时间，标准化为 Unix 微秒 |
| 8 | quote_volume | 计价资产成交额，USDT |
| 9 | trades | 成交笔数，非负整数 |
| 10 | taker_buy_volume | 主动买入成交量，BTC |
| 11 | taker_buy_quote_volume | 主动买入成交额，USDT |
| 12 | 不作分析 | 官方保留／ignore 字段 |

| 衍生字段 | 定义 |
|---|---|
| timestamp_utc | UTC ISO 时间，从起始时间转换 |
| return_log | log(close_t / close_(t-1))；首根以前一年最后收盘 93576.0 衔接 |
| signed_taker_volume | 2*taker_buy_volume-volume，BTC；有符号主动成交量，不是净资金流入 |
| range_log | log(high/low)，区间对数振幅 |
| date_utc / month_utc / slot_utc | UTC 日期／月份／0–287 的 5 分钟时段编号 |
| split | calibration：上半年；holdout：2025-07-01 起 |

实际字段以 bars.csv 表头为准。2025 现货归档时间单位为微秒；2024 参考归档为毫秒，不能统一按毫秒读后再猜测修正。close_time 检查按来源精度处理。

105,120 根、365 个完整 UTC 日。连续网格、唯一性、次序、有限值、正价格、OHLC 包含关系、非负量、主动买入量不超过总量、量价加权均价范围均核验。缺失／重复／无效记录均为零；未删根、未填补。零收益 288 根保留、零量 0 根。完整质量报告在同一 manifest 目录。

所有聚合以 UTC 为界，收益求和、量求和；5 分钟以内逐笔路径和盘口不在数据中。价格使用原始现货价格，无股票复权或人为收益去极值。分析中中心矩自行去除均值，未改写原始收益字段。

完整 raw/processed 行情保留本地、不入 Git 或交接 ZIP；下载脚本复原。市场衍生成果署名 Binance Vision，CC BY-NC-SA 4.0，详见 [来源与使用范围](market_data_provenance.md)。
