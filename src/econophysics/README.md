# 共用研究实现

已实现 `model.py` 的 ER 网络／群体、动作、全成交执行、OHLCVD、理论矩和独立窗口；`features.py` 统一收益与量价摘要。使用 Python 标准库，入口为 `scripts/research/run_foundation.py`。

`inference.py` 已实现经典参照和训练内预处理，`study_statistics.py` 实现窗口 bootstrap 与有限离散尾部诊断；这些分析模块需要 requirements-study.txt。核心 model／features 仍只用标准库。模拟研究已运行一次，成员复核和真实数据流程仍待完成。
