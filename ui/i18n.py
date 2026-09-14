"""UI-only internationalization for the formal Streamlit pages."""

from __future__ import annotations

import streamlit as st


LANGUAGES = ("zh", "en")
DEFAULT_LANGUAGE = "en"

STATION_NAME_TRANSLATIONS = {
    "三峡能源新疆吉木萨尔全钒液流储能电站": {
        "zh": "三峡能源新疆吉木萨尔全钒液流储能电站",
        "en": (
            "China Three Gorges Renewables Xinjiang Jimusaer All-Vanadium "
            "Redox Flow Battery Energy Storage Station"
        ),
    },
}

BID_TABLE_COLUMN_TRANSLATIONS = {
    "时间点": "Time Slot",
    "申报类型": "Bid Type",
    "申报功率 (MW)": "Bid Power (MW)",
    "预测电价 (元/MWh)": "Forecast Price (CNY/MWh)",
    "预期收益/成本 (元)": "Expected Revenue/Cost (CNY)",
    "功率段 (MW)": "Power Segment (MW)",
    "报价 (元/MWh)": "Bid Price (CNY/MWh)",
    "备注": "Notes",
    # Retain compatibility with the earlier segmented-table schema.
    "时段": "Interval",
    "类型": "Type",
    "分段": "Segment",
    "申报电量(MWh)": "Bid Quantity (MWh)",
    "申报电价(元/MWh)": "Bid Price (CNY/MWh)",
}

BID_TYPE_TRANSLATIONS = {
    "充电": "Charge",
    "放电": "Discharge",
    "静置": "Idle",
}

BID_NOTE_TRANSLATIONS = {
    "无充放电操作": "No charging or discharging action",
    "无任何申报": "No bid submitted",
    "模型求解失败，无充放电操作": (
        "Model solve failed; no charging or discharging action"
    ),
    "保守报价，确保基础成交": (
        "Conservative bid to improve base clearing probability"
    ),
    "核心报价，围绕预测边际价": (
        "Core bid around the forecast marginal price"
    ),
    "激进报价，仅在电价极低时成交": (
        "Aggressive bid that clears only at very low prices"
    ),
    "激进报价，捕捉尖峰价格": "Aggressive bid to capture price spikes",
}

TRANSLATIONS = {
    "zh": {
        "app.title": "日前市场决策",
        "app.subtitle": "96 个时段的价格预测、充放电优化与 RARR 模式判断",
        "nav.workspace": "决策工作区",
        "nav.station_group": "电站管理",
        "nav.decision": "日前决策",
        "nav.station": "电站档案",
        "nav.input": "数据输入",
        "nav.parameters": "模型参数",
        "nav.results": "结果分析",
        "nav.bid": "申报策略",
        "nav.history": "历史记录",
        "status.system_normal": "系统正常",
        "status.interval_count": "{count} 个时段",
        "status.ready": "等待运行",
        "status.running": "正在运行",
        "status.completed": "决策完成",
        "stage.input": "数据准备",
        "stage.baseline": "{solver} 基准求解",
        "stage.rarr": "RARR 模式判断",
        "stage.output": "策略输出",
        "action.parameters": "参数配置",
        "action.solve": "校验并开始求解",
        "action.download_details": "下载详细数据",
        "action.download_bid": "下载报价策略",
        "action.replace_file": "替换文件",
        "action.edit_profile": "编辑电站档案",
        "action.save_profile": "保存档案",
        "action.show_logs": "查看详细执行日志",
        "field.solver": "求解器选择",
        "field.time_horizon": "优化时间范围（小时）",
        "field.time_step": "时间步长（分钟）",
        "field.price_csv": "上传电价预测数据（CSV，包含 price 列）",
        "field.e_rated": "额定容量（MWh）",
        "field.p_rated": "额定功率（MW）",
        "field.initial_soc": "初始荷电状态（SOC）",
        "field.e_0": "初始能量（MWh）",
        "field.e_t_target": "目标结束能量（MWh）",
        "field.eta_charge": "充电效率",
        "field.eta_discharge": "放电效率",
        "field.soc_min": "最小荷电状态（SOC）",
        "field.soc_max": "最大荷电状态（SOC）",
        "field.k": "度电退化成本系数",
        "field.n_cycle_max": "最大等效循环次数",
        "field.c_om": "固定运维成本",
        "field.r_ramp": "功率爬坡速率（MW/15min）",
        "group.system": "系统配置",
        "group.battery": "电池参数",
        "group.market": "市场参数",
        "group.core": "核心规格",
        "group.operation": "运行状态",
        "group.efficiency": "效率参数",
        "group.soc": "SOC 范围",
        "group.cost": "成本与退化",
        "group.constraints": "物理约束",
        "input.title": "决策输入",
        "input.hint": "上传日前电价预测，并检查本次运行的关键参数。",
        "input.file_ready": "数据文件已就绪",
        "input.file_missing": "请先上传包含 price 列的 CSV 文件。",
        "parameter.summary": "参数摘要",
        "parameter.capacity": "容量",
        "parameter.power": "功率",
        "parameter.soc_range": "SOC 安全区间",
        "progress.title": "优化执行",
        "progress.started": "优化流程已启动，准备执行。",
        "progress.baseline_running": "第一阶段：正在求解最优充放电基准计划。",
        "progress.baseline_done": "第一阶段：基准计划求解完成。",
        "progress.rarr_running": "第二阶段：正在通过 RARR 进行模式判断。",
        "progress.rarr_spinner": "正在进行蒙特卡洛模拟以评估风险...",
        "progress.rarr_done": "第二阶段：推荐采用 {mode} 模式。",
        "progress.output_running": "第三阶段：正在生成结果与申报策略。",
        "progress.output_done": "第三阶段：结果与策略生成完成。",
        "progress.saved": "本次决策结果已存入电站档案。",
        "result.title": "决策结果",
        "result.net_profit": "总净利润",
        "result.discharge_revenue": "总放电收益",
        "result.cycles": "等效循环次数",
        "result.throughput": "总能量吞吐",
        "result.avg_profit": "平均度电利润",
        "result.schedule": "价格与调度曲线",
        "result.details": "详细调度计划",
        "result.details_hint": "下表展示每个时间步的详细调度结果。",
        "result.bid_strategy": "市场报价策略",
        "result.mode_reason_qp": "系统采用报量报价模式。下表为分段申报电量和对应价格。",
        "result.mode_reason_qnp": "系统采用报量不报价模式。正值表示放电，负值表示充电。",
        "mode.quantity_only": "报量不报价",
        "mode.quantity_price": "报量报价",
        "profile.title": "电站档案",
        "profile.subtitle": "电站基础信息与历史决策表现",
        "profile.basic": "电站基本信息",
        "profile.station_name": "电站名称",
        "profile.location": "地理位置",
        "profile.commission_date": "投运日期",
        "profile.e_rated": "额定容量（MWh）",
        "profile.p_rated": "额定功率（MW）",
        "profile.edit_title": "编辑电站档案",
        "profile.save_success": "电站档案已成功更新。",
        "profile.saved": "电站档案已更新。",
        "profile.missing": "未能加载电站档案，请刷新页面后重试。",
        "history.title": "历史决策",
        "history.empty": "尚无历史决策记录。请先在日前决策页面运行一次优化。",
        "history.overview": "历史表现",
        "history.total_profit": "历史总净利润",
        "history.total_cycles": "累计等效循环",
        "history.avg_profit": "平均单次运行利润",
        "history.profit_trend": "每次运行净利润趋势",
        "history.mode_distribution": "历史决策模式分布",
        "history.details": "查看详细历史数据",
        "history.run_time": "运行时间",
        "history.net_profit_axis": "净利润（元）",
        "history.no_date": "未设置",
        "error.import": "模块导入失败：{error}",
        "error.solve": "优化模型求解失败，请检查参数和输入数据。",
        "error.workflow": "优化求解或决策过程中出错：{error}",
        "station.unnamed": "未命名电站",
    },
    "en": {
        "app.title": "Day-ahead Market Decision",
        "app.subtitle": "Price forecast, battery dispatch and RARR mode selection across 96 intervals",
        "nav.workspace": "Decision Workspace",
        "nav.station_group": "Station",
        "nav.decision": "Day-ahead Decision",
        "nav.station": "Station Profile",
        "nav.input": "Input Data",
        "nav.parameters": "Model Parameters",
        "nav.results": "Results",
        "nav.bid": "Bid Strategy",
        "nav.history": "History",
        "status.system_normal": "System normal",
        "status.interval_count": "{count} intervals",
        "status.ready": "Ready",
        "status.running": "Running",
        "status.completed": "Completed",
        "stage.input": "Data Preparation",
        "stage.baseline": "{solver} Baseline Solve",
        "stage.rarr": "RARR Mode Selection",
        "stage.output": "Strategy Output",
        "action.parameters": "Parameters",
        "action.solve": "Validate and Run",
        "action.download_details": "Download Schedule",
        "action.download_bid": "Download Bid Strategy",
        "action.replace_file": "Replace File",
        "action.edit_profile": "Edit Station Profile",
        "action.save_profile": "Save Profile",
        "action.show_logs": "View Execution Log",
        "field.solver": "Solver",
        "field.time_horizon": "Optimization Horizon (hours)",
        "field.time_step": "Time Step (minutes)",
        "field.price_csv": "Upload price forecast CSV with a price column",
        "field.e_rated": "Rated Capacity (MWh)",
        "field.p_rated": "Rated Power (MW)",
        "field.initial_soc": "Initial State of Charge (SOC)",
        "field.e_0": "Initial Energy (MWh)",
        "field.e_t_target": "Target Final Energy (MWh)",
        "field.eta_charge": "Charging Efficiency",
        "field.eta_discharge": "Discharging Efficiency",
        "field.soc_min": "Minimum State of Charge (SOC)",
        "field.soc_max": "Maximum State of Charge (SOC)",
        "field.k": "Degradation Cost Coefficient",
        "field.n_cycle_max": "Maximum Equivalent Cycles",
        "field.c_om": "Fixed O&M Cost",
        "field.r_ramp": "Ramp Rate (MW/15min)",
        "group.system": "System",
        "group.battery": "Battery",
        "group.market": "Market",
        "group.core": "Core Rating",
        "group.operation": "Operating State",
        "group.efficiency": "Efficiency",
        "group.soc": "SOC Range",
        "group.cost": "Cost and Degradation",
        "group.constraints": "Physical Constraints",
        "input.title": "Decision Input",
        "input.hint": "Upload the day-ahead price forecast and review the key parameters for this run.",
        "input.file_ready": "Data file ready",
        "input.file_missing": "Upload a CSV file containing a price column.",
        "parameter.summary": "Parameter Summary",
        "parameter.capacity": "Capacity",
        "parameter.power": "Power",
        "parameter.soc_range": "Safe SOC Range",
        "progress.title": "Optimization Run",
        "progress.started": "Optimization started.",
        "progress.baseline_running": "Stage 1: solving the baseline charge and discharge plan.",
        "progress.baseline_done": "Stage 1: baseline plan completed.",
        "progress.rarr_running": "Stage 2: evaluating the RARR decision mode.",
        "progress.rarr_spinner": "Running Monte Carlo simulations to evaluate risk...",
        "progress.rarr_done": "Stage 2: recommended mode is {mode}.",
        "progress.output_running": "Stage 3: generating results and the bid strategy.",
        "progress.output_done": "Stage 3: results and strategy completed.",
        "progress.saved": "This decision has been saved to the station archive.",
        "result.title": "Decision Results",
        "result.net_profit": "Net Profit",
        "result.discharge_revenue": "Discharge Revenue",
        "result.cycles": "Equivalent Cycles",
        "result.throughput": "Energy Throughput",
        "result.avg_profit": "Average Profit per MWh",
        "result.schedule": "Price and Dispatch Profile",
        "result.details": "Detailed Dispatch Schedule",
        "result.details_hint": "The table shows the dispatch result for every interval.",
        "result.bid_strategy": "Market Bid Strategy",
        "result.mode_reason_qp": "Quantity-and-price bidding was selected. The table shows segmented quantities and prices.",
        "result.mode_reason_qnp": "Quantity-only bidding was selected. Positive values discharge; negative values charge.",
        "mode.quantity_only": "Quantity-only Bid",
        "mode.quantity_price": "Quantity-and-price Bid",
        "profile.title": "Station Profile",
        "profile.subtitle": "Station details and historical decision performance",
        "profile.basic": "Station Details",
        "profile.station_name": "Station Name",
        "profile.location": "Location",
        "profile.commission_date": "Commissioning Date",
        "profile.e_rated": "Rated Capacity (MWh)",
        "profile.p_rated": "Rated Power (MW)",
        "profile.edit_title": "Edit Station Profile",
        "profile.save_success": "Station profile updated successfully.",
        "profile.saved": "Station profile updated.",
        "profile.missing": "The station profile could not be loaded. Refresh and try again.",
        "history.title": "Decision History",
        "history.empty": "No historical decisions are available. Run an optimization first.",
        "history.overview": "Historical Performance",
        "history.total_profit": "Total Historical Net Profit",
        "history.total_cycles": "Cumulative Equivalent Cycles",
        "history.avg_profit": "Average Profit per Run",
        "history.profit_trend": "Net Profit by Run",
        "history.mode_distribution": "Decision Mode Distribution",
        "history.details": "View Detailed History",
        "history.run_time": "Run Time",
        "history.net_profit_axis": "Net Profit (CNY)",
        "history.no_date": "Not set",
        "error.import": "Module import failed: {error}",
        "error.solve": "The optimization model failed. Check the parameters and input data.",
        "error.workflow": "The decision workflow failed: {error}",
        "station.unnamed": "Unnamed Station",
    },
}


def get_language() -> str:
    """Return the active UI language, defaulting to English."""
    widget_value = st.session_state.get("language_switcher")
    if widget_value in ("中文", "EN"):
        return "zh" if widget_value == "中文" else "en"
    language = st.session_state.get("language", DEFAULT_LANGUAGE)
    return language if language in LANGUAGES else DEFAULT_LANGUAGE


def set_language(language: str) -> None:
    """Set the active UI language."""
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")
    st.session_state["language"] = language


def t(key: str, language: str | None = None, **kwargs) -> str:
    """Translate a UI key with Chinese fallback."""
    selected = language or get_language()
    template = TRANSLATIONS.get(selected, {}).get(
        key, TRANSLATIONS["zh"].get(key, key)
    )
    return template.format(**kwargs)


def localize_station_name(station_name: str, language: str | None = None) -> str:
    """Localize a known station name without changing its stored profile value."""
    source_name = str(station_name)
    selected = language or get_language()
    translations = STATION_NAME_TRANSLATIONS.get(source_name)
    if translations is None:
        return source_name
    return translations.get(selected, source_name)


def localize_bid_table(table, language: str | None = None):
    """Return a localized display copy without changing the bid data contract."""
    selected = language or get_language()
    localized = table.copy()
    if selected != "en":
        return localized

    for type_column in ("申报类型", "类型"):
        if type_column in localized.columns:
            localized[type_column] = localized[type_column].map(
                lambda value: BID_TYPE_TRANSLATIONS.get(value, value)
            )

    if "备注" in localized.columns:
        def translate_note(value):
            if not isinstance(value, str):
                return value
            if value.startswith("充电效率:"):
                return f"Charging efficiency:{value.removeprefix('充电效率:')}"
            if value.startswith("放电效率:"):
                return f"Discharging efficiency:{value.removeprefix('放电效率:')}"
            return BID_NOTE_TRANSLATIONS.get(value, value)

        localized["备注"] = localized["备注"].map(translate_note)

    return localized.rename(columns=BID_TABLE_COLUMN_TRANSLATIONS)


def render_language_switcher(key: str = "language_switcher") -> str:
    """Render the compact top-right language control."""
    current = get_language()
    selected = st.segmented_control(
        "Language",
        options=["中文", "EN"],
        default="中文" if current == "zh" else "EN",
        key=key,
        label_visibility="collapsed",
    )
    language = "zh" if selected == "中文" else "en"
    set_language(language)
    return language
