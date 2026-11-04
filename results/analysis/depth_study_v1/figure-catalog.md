# D01–D03：深化研究图表目录

三图使用 Python，183 mm 宽，PDF／SVG／600 dpi PNG。它们是独立增补编号，不改变原 F 图协议。图中 SIMULATION 标识保留。源表、配置、脚本、对齐、PDF 字体、碰撞和视觉 QA 随包交付。

## D01：恢复增益取决于基准

- 源：run_metrics.csv、run_contrasts.csv；一致区间汇总 summary_metrics.csv。
- a：5 种方法的 10 次 MAE 原始点、平均与 95% run-bootstrap 区间。b：前两项预设配对差，负值有利于 joint。
- 为什么画：把“有量比没有量好”与“量价组合最好”分开。
- 应注意：joint 在每次都优于 return；volume 在原网格每次都优于 joint。物理矩方法不用训练标签。
- 改变的结论：组合不是普遍最优；后续必须保留 volume 和物理参照。
- 限制：模型固定 N、u，10 次有限重复，非真实市场；图中网格测试不是全部泛化结果。

## D02：尺度不变性是表示性质

- 源：run_metrics.csv 和一致 run-bootstrap 汇总。
- a 原网格；b 训练未见的中间 rho；5 种方法、全部三个冲击尺度。
- y 为 log MAE，区间端点均大于零；不同方法做小幅分类轴错位以避免重叠。n=10 完整独立研究，误差条均为同一口径。
- 为什么画：区分原学习器失效与观测信息不足。
- 应注意：raw-return／joint 随尺度改变退步；shape、volume、physics 保持不变。未见 rho 时 physics 接近 joint，volume RBF 有插值误差。
- 改变的结论：已知干扰可以通过表示设计处理；不能从一个拟合器失败推导不可识别。
- 限制：窗口共同正乘法；shape 无漂移时较差；此图不覆盖未知 N／u、非线性冲击或真实流动性。

## D03：相同边际不足以固定联合机制

- 源：mechanism_diagnostics.csv、mechanism_null_distribution.csv、mechanism_observations.csv。
- a 原配对耦合量和 4,999 次置换的中央 99% 范围；原配对误差条为 95% period-bootstrap CI。b 原始 Z 与一个边际保真替代的 Z，各 95% period-bootstrap 区间。
- 为什么画：给出完全相同边际但不同联合机制的受控替代。
- 应注意：两种边际经验分布精确不变；配对信息改变，联合约束区分它们。rho=1 原始 Z 有小的名义区间偏离，正文明确披露；追加独立均值复查不在图中替换旧序列。
- 改变的结论：仅复现收益／量的边际不构成机制验证；联合检验提供受控排除能力。
- 限制：独立配对只是一个替代；Z 不是充分条件，q=1/2 退化；它不能检测临界性或证明真实羊群。

所有图的误差条所代表的样本单位必须随图注带入 PPT，不能只复制图而删除 n 与范围说明。
