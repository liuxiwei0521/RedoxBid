# streamlit run app/决策主页面.py

import os
import sys

import streamlit as st


# Apply page metadata and the product shell before importing data/solver stacks.
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ui import inject_theme


st.set_page_config(
    page_title="RedoxBid",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

import copy
import pandas as pd
import numpy as np
import pyomo.environ as pyo
import plotly.graph_objects as go

# --- 关键路径处理 ---
# 这个代码块是解决 app 和 utils 是同级目录问题的核心。
# 它将项目的根目录添加到Python的搜索路径中。
try:
    # 现在可以安全地从同级目录导入模块了
    from models.optimization_model import DEFAULT_SOLVER, FlowBatteryDayAheadMarketModel, \
        get_available_solver_names, mode_selection_rarr, generate_bid_table, \
        generate_segmented_bid_table, calculate_kpis
    from models.parameter_config import get_default_battery_params, validate_battery_params
    from models.regulation_forecast import forecast_regulation_prices
    from models.sequential_market_model import SequentialRegulationModel
    from models.joint_market_model import JointEnergyRegulationModel
    from utils.market_comparison import (
        build_baseline_schedule,
        build_market_comparison,
        build_regulation_market_frame,
    )
    from utils.regulation_data import normalize_regulation_history
    from utils.visualization import generate_comprehensive_visualization
    from utils.database import init_db, save_decision_record, load_station_profile

except (ImportError, NameError) as e:
    st.error(f"模块导入失败: {e}")
    st.error(f"请确保您的项目结构正确，且依赖已安装。期望的结构是 'app' 和 'utils'/'models' 文件夹位于同一项目根目录下。")


    # 提供一个备用方案，以便UI可以渲染，避免应用完全崩溃
    def get_default_battery_params():
        return {}


    def validate_battery_params(p):
        return p


    class FlowBatteryDayAheadMarketModel:
        def __init__(self, *args, **kwargs): pass

        def solve_model(self): return None, None


    DEFAULT_SOLVER = "CBC"


    def get_available_solver_names():
        return (DEFAULT_SOLVER,)


    def mode_selection_rarr(*args, **kwargs):
        return 1


    def generate_segmented_bid_table(*args, **kwargs):
        return pd.DataFrame(columns=['时段', '类型', '分段', '申报电量(MWh)', '申报电价(元/MWh)'])


    def generate_bid_table(*args, **kwargs):
        return pd.DataFrame()


    def calculate_kpis(*args, **kwargs):
        return {k: 0 for k in ['总净利润', '总放电收益', '等效循环次数', '总能量吞吐', '平均度电利润']}


    def generate_comprehensive_visualization(*args, **kwargs):
        return go.Figure()


    def init_db():
        pass


    def save_decision_record(*args, **kwargs):
        pass


    def load_station_profile():
        return {'e_rated': 100, 'p_rated': 25}


from ui import (
    apply_plotly_theme,
    get_language,
    localize_bid_table,
    render_metric_strip,
    render_sidebar,
    render_stepper,
    render_topbar,
    t,
)


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SAMPLE_REGULATION_PATH = os.path.join(
    PROJECT_ROOT, "data", "synthetic_regulation_history.csv"
)


def bi(language, chinese, english):
    """Return compact page-local bilingual copy."""
    return chinese if language == "zh" else english


def validate_day_ahead_prices(frame):
    """Validate the stable 96-interval day-ahead input contract."""
    if "price" not in frame:
        raise ValueError("日前电价文件必须包含 price 列 / Missing price column")
    prices = pd.to_numeric(frame["price"], errors="coerce").to_numpy(dtype=float)
    if prices.shape != (96,) or not np.isfinite(prices).all():
        raise ValueError("price 列必须包含 96 个有限数值 / Exactly 96 prices required")
    return prices


def load_default_regulation_history():
    """Load the bundled synthetic regulation sample and disclose its provenance."""
    history = normalize_regulation_history(pd.read_csv(SAMPLE_REGULATION_PATH))
    return history, "synthetic seven-day sample"


def build_regulation_config(values):
    """Keep the regulation-model parameter contract explicit."""
    return {
        "reserve_duration_hours": values["reserve_duration_hours"],
        "max_market_share": values["max_market_share"],
        "regulation_degradation_cost_cny_per_mwh": values[
            "regulation_degradation_cost_cny_per_mwh"
        ],
        "regulation_om_cost_cny_per_mw_h": values[
            "regulation_om_cost_cny_per_mw_h"
        ],
        "efficiency_loss_fraction": values["efficiency_loss_fraction"],
        "regulation_ramp_mw_per_interval": values[
            "regulation_ramp_mw_per_interval"
        ],
    }


@st.cache_data
def convert_df_to_csv(df):
    """将DataFrame转换为CSV格式的字符串，以便下载。"""
    if not isinstance(df, pd.DataFrame):
        df = pd.DataFrame(df)
    return df.to_csv(index=False).encode('utf-8-sig')


def build_download_artifacts(results_df, bid_table, optimal_mode):
    """Build downloadable CSV artifacts for schedules and bid strategies."""
    bid_file_name = (
        'segmented_bidding_strategy.csv'
        if optimal_mode == 1
        else 'simple_bidding_strategy.csv'
    )
    return {
        'schedule': {
            'data': convert_df_to_csv(results_df),
            'file_name': 'optimal_schedule_details.csv',
        },
        'bid': {
            'data': convert_df_to_csv(bid_table),
            'file_name': bid_file_name,
        },
    }


def create_results_dataframe(model, price_forecast, battery_params, time_step_minutes):
    """从Pyomo模型中提取数据并创建详细结果的DataFrame。"""
    if model is None:
        return pd.DataFrame()

    T = len(price_forecast)
    charge_power = [pyo.value(model.P_charge[t]) for t in range(T)]
    discharge_power = [pyo.value(model.P_discharge[t]) for t in range(T)]
    net_power = [dp - cp for dp, cp in zip(discharge_power, charge_power)]
    energy = [pyo.value(model.E[t]) for t in range(T)]
    soc = [e / battery_params['E_rated'] * 100 for e in energy]

    time_index = pd.to_datetime(pd.date_range(start='2023-01-01', periods=T, freq=f'{time_step_minutes}min'))

    results_df = pd.DataFrame({
        'Time': time_index.strftime('%H:%M'),
        'Price (元/MWh)': price_forecast,
        'Charge_Power (MW)': charge_power,
        'Discharge_Power (MW)': discharge_power,
        'Net_Power (MW)': net_power,
        'Energy_State (MWh)': energy,
        'SOC (%)': soc
    })
    return results_df


def render_multi_market_results(view, language):
    """Render the three approved scenario views without changing core outputs."""
    extension = view["market_extension"]
    forecast = extension["forecast"]
    sequential = extension["sequential"]
    joint = extension["joint"]
    comparison = extension["comparison"]
    day_tab, regulation_tab, comparison_tab = st.tabs(
        [
            bi(language, "日前市场", "Day-ahead"),
            bi(language, "调频市场", "Regulation"),
            bi(language, "联合对比", "Joint comparison"),
        ]
    )

    with day_tab:
        kpis = view["kpis"]
        currency = "元" if language == "zh" else "CNY"
        render_metric_strip(
            [
                (t("result.net_profit"), f"{kpis['总净利润']:,.2f} {currency}", None),
                (t("result.discharge_revenue"), f"{kpis['总放电收益']:,.2f} {currency}", None),
                (t("result.cycles"), f"{kpis['等效循环次数']:.3f}", None),
                (t("result.throughput"), f"{kpis['总能量吞吐']:.2f} MWh", None),
            ]
        )
        st.plotly_chart(
            apply_plotly_theme(copy.deepcopy(view["figure"]), language),
            use_container_width=True,
        )
        results_df = view["results_df"]
        bid_table = view["bid_table"]
        st.dataframe(results_df, use_container_width=True)
        da_col, bid_col = st.columns(2)
        da_col.download_button(
            bi(language, "下载日前调度", "Download day-ahead schedule"),
            convert_df_to_csv(results_df),
            "day_ahead_schedule.csv",
            "text/csv",
            key="multi_download_da",
        )
        bid_col.download_button(
            t("action.download_bid"),
            convert_df_to_csv(bid_table),
            "day_ahead_bid_strategy.csv",
            "text/csv",
            key="multi_download_bid",
        )

    with regulation_tab:
        metrics = forecast.metrics
        r2_text = "N/A" if metrics["r2"] is None else f"{metrics['r2']:.3f}"
        render_metric_strip(
            [
                (bi(language, "预测模型", "Forecast model"), forecast.model_name, None),
                ("MAE", f"{metrics['mae']:.2f}", None),
                ("RMSE", f"{metrics['rmse']:.2f}", None),
                ("R²", r2_text, None),
                (
                    bi(language, "顺序方案总利润", "Sequential total profit"),
                    f"{sequential.kpis['total_profit_cny']:,.2f}",
                    None,
                ),
            ]
        )
        st.info(
            bi(
                language,
                f"数据来源：{forecast.data_source}；需求来源：{forecast.demand_source}。当前样例为合成数据，仅用于方法演示。",
                f"Data source: {forecast.data_source}; demand source: {forecast.demand_source}. The current sample is synthetic and intended for demonstration only.",
            )
        )
        forecast_figure = go.Figure()
        forecast_figure.add_trace(
            go.Scatter(
                x=forecast.hourly_forecast["timestamp"],
                y=forecast.hourly_forecast["mileage_price_cny_per_mw"],
                name=bi(language, "里程价格", "Mileage price"),
                mode="lines+markers",
            )
        )
        forecast_figure.add_trace(
            go.Scatter(
                x=forecast.hourly_forecast["timestamp"],
                y=forecast.hourly_forecast["regulation_demand_mw"],
                name=bi(language, "调频需求", "Regulation demand"),
                mode="lines",
                yaxis="y2",
            )
        )
        forecast_figure.update_layout(
            title=bi(language, "调频需求与里程价格预测", "Regulation demand and mileage-price forecast"),
            yaxis_title=bi(language, "价格（元/MW）", "Price (CNY/MW)"),
            yaxis2=dict(
                title=bi(language, "需求（MW）", "Demand (MW)"),
                overlaying="y",
                side="right",
            ),
        )
        st.plotly_chart(
            apply_plotly_theme(forecast_figure, language),
            use_container_width=True,
        )
        st.dataframe(sequential.schedule, use_container_width=True)
        st.download_button(
            bi(language, "下载顺序调频方案", "Download sequential regulation plan"),
            convert_df_to_csv(sequential.schedule),
            "sequential_regulation_schedule.csv",
            "text/csv",
            key="download_sequential",
        )

    with comparison_tab:
        scenario_labels = {
            "day_ahead_only": bi(language, "仅日前市场", "Day-ahead only"),
            "sequential": bi(language, "顺序调频优化", "Sequential regulation"),
            "joint": bi(language, "日前—调频联合优化", "Joint co-optimization"),
        }
        display_comparison = comparison.copy()
        display_comparison["scenario"] = display_comparison["scenario"].map(
            scenario_labels
        )
        render_metric_strip(
            [
                (
                    bi(language, "仅日前利润", "Day-ahead profit"),
                    f"{comparison.iloc[0]['total_profit_cny']:,.2f}",
                    None,
                ),
                (
                    bi(language, "顺序方案利润", "Sequential profit"),
                    f"{comparison.iloc[1]['total_profit_cny']:,.2f}",
                    f"{comparison.iloc[1]['increment_vs_day_ahead_cny']:,.2f}",
                ),
                (
                    bi(language, "联合方案利润", "Joint profit"),
                    f"{comparison.iloc[2]['total_profit_cny']:,.2f}",
                    f"{comparison.iloc[2]['increment_vs_day_ahead_cny']:,.2f}",
                ),
                (
                    bi(language, "联合调频峰值", "Joint peak reserve"),
                    f"{joint.kpis['peak_reserve_mw']:.2f} MW",
                    None,
                ),
            ]
        )
        profit_figure = go.Figure(
            go.Bar(
                x=display_comparison["scenario"],
                y=display_comparison["total_profit_cny"],
                marker_color=["#A9B0BA", "#7D94D8", "#2858D6"],
            )
        )
        profit_figure.update_layout(
            title=bi(language, "三种市场参与方案利润对比", "Profit comparison across three market strategies"),
            yaxis_title=bi(language, "总利润（元）", "Total profit (CNY)")
        )
        st.plotly_chart(
            apply_plotly_theme(profit_figure, language),
            use_container_width=True,
        )
        schedule_figure = go.Figure()
        schedule_figure.add_trace(
            go.Scatter(
                x=joint.schedule["time"],
                y=joint.schedule["net_power_mw"],
                name=bi(language, "日前净功率", "Day-ahead net power"),
            )
        )
        schedule_figure.add_trace(
            go.Scatter(
                x=joint.schedule["time"],
                y=joint.schedule["regulation_reserve_mw"],
                name=bi(language, "调频备用", "Regulation reserve"),
            )
        )
        schedule_figure.update_layout(
            title=bi(language, "联合优化功率分配", "Joint optimization power allocation"),
            yaxis_title=bi(language, "功率（MW）", "Power (MW)")
        )
        st.plotly_chart(
            apply_plotly_theme(schedule_figure, language),
            use_container_width=True,
        )
        st.dataframe(joint.schedule, use_container_width=True)
        joint_col, comparison_col = st.columns(2)
        joint_col.download_button(
            bi(language, "下载联合调度", "Download joint schedule"),
            convert_df_to_csv(joint.schedule),
            "joint_energy_regulation_schedule.csv",
            "text/csv",
            key="download_joint",
        )
        comparison_col.download_button(
            bi(language, "下载模型对比", "Download model comparison"),
            convert_df_to_csv(comparison),
            "market_model_comparison.csv",
            "text/csv",
            key="download_comparison",
        )


def main():
    station_profile = load_station_profile() or {}
    render_topbar(
        station_profile.get("station_name", t("station.unnamed")),
        t("status.system_normal"),
    )
    active_section = (
        st.session_state.get("sidebar_section", "results")
        if "decision_view" in st.session_state
        else "input"
    )
    render_sidebar("decision", active_section)

    language = get_language()
    st.markdown('<div class="pm-eyebrow">Decision Workspace</div>', unsafe_allow_html=True)
    st.title(t("app.title"))
    market_mode = st.segmented_control(
        bi(language, "决策范围", "Decision scope"),
        options=["day_ahead_only", "comparison"],
        format_func=lambda value: {
            "day_ahead_only": bi(language, "仅日前市场", "Day-ahead only"),
            "comparison": bi(language, "三方案对比", "Three-scenario comparison"),
        }[value],
        default="day_ahead_only",
        key="market_mode",
    ) or "day_ahead_only"
    st.caption(
        t("app.subtitle")
        if market_mode == "day_ahead_only"
        else bi(
            language,
            "日前基准、顺序调频与日前—调频联合优化的统一比较",
            "Unified comparison of day-ahead, sequential regulation and joint co-optimization",
        )
    )

    available_solvers = get_available_solver_names()
    selected_solver = st.session_state.get("solver_type", DEFAULT_SOLVER)
    if selected_solver not in available_solvers:
        selected_solver = DEFAULT_SOLVER
        st.session_state["solver_type"] = selected_solver

    comparison_mode = market_mode == "comparison"
    completed_steps = 6 if comparison_mode else 4
    current_step = completed_steps if "decision_view" in st.session_state else 1
    workflow_steps = [
        t("stage.input"),
        t("stage.baseline", solver=selected_solver),
        t("stage.rarr"),
    ]
    if comparison_mode:
        workflow_steps.extend(
            [
                bi(language, "调频价格预测", "Regulation forecast"),
                bi(language, "联合市场优化", "Joint optimization"),
            ]
        )
    workflow_steps.append(t("stage.output"))
    render_stepper(
        current_step,
        workflow_steps,
    )

    default_params = get_default_battery_params()
    if station_profile:
        default_params["E_rated"] = station_profile.get(
            "e_rated", default_params.get("E_rated", 100)
        )
        default_params["P_rated"] = station_profile.get(
            "p_rated", default_params.get("P_rated", 25)
        )
    battery_params = default_params.copy()
    regulation_values = {
        "capacity_price_cny_per_mw_h": 8.0,
        "performance_score": 0.95,
        "mileage_ratio": 0.25,
        "reserve_duration_hours": 0.25,
        "max_market_share": 0.20,
        "regulation_degradation_cost_cny_per_mwh": 2.0,
        "regulation_om_cost_cny_per_mw_h": 0.10,
        "efficiency_loss_fraction": 0.02,
        "regulation_ramp_mw_per_interval": 20.0,
        "price_upper_limit": 50.0,
        "price_min_unit": 0.1,
    }

    with st.container(border=True):
        header_col, parameter_col = st.columns([5, 1.35], vertical_alignment="center")
        with header_col:
            st.subheader(t("input.title"))
            st.caption(t("input.hint"))
        with parameter_col:
            parameter_popover = st.popover(
                t("action.parameters"),
                use_container_width=True,
            )

        with parameter_popover:
            system_tab, battery_tab, market_tab, regulation_tab = st.tabs(
                [
                    t("group.system"),
                    t("group.battery"),
                    t("group.market"),
                    bi(language, "调频参数", "Regulation"),
                ]
            )
            with system_tab:
                solver_type = st.selectbox(
                    t("field.solver"),
                    list(available_solvers),
                    key="solver_type",
                )
                time_horizon = st.number_input(
                    t("field.time_horizon"),
                    1,
                    48,
                    24,
                    key="time_horizon",
                    disabled=True,
                )
                time_step = st.number_input(
                    t("field.time_step"),
                    1,
                    60,
                    15,
                    key="time_step",
                    disabled=True,
                )
            with battery_tab:
                st.markdown(f"**{t('group.core')}**")
                battery_params["E_rated"] = st.number_input(
                    t("field.e_rated"),
                    10,
                    2000,
                    int(default_params.get("E_rated", 100)),
                    key="battery_E_rated",
                )
                battery_params["P_rated"] = st.number_input(
                    t("field.p_rated"),
                    1,
                    500,
                    int(default_params.get("P_rated", 25)),
                    key="battery_P_rated",
                )
                st.markdown(f"**{t('group.operation')}**")
                battery_params["initial_soc"] = st.slider(
                    t("field.initial_soc"),
                    0.2,
                    0.8,
                    float(default_params.get("initial_soc", 0.5)),
                    format="%.2f",
                    key="battery_initial_soc",
                )
                battery_params["E_0"] = st.number_input(
                    t("field.e_0"),
                    1,
                    int(battery_params["E_rated"]),
                    int(default_params.get("E_0", 50)),
                    key="battery_E_0",
                )
                battery_params["E_T_target"] = st.number_input(
                    t("field.e_t_target"),
                    1,
                    int(battery_params["E_rated"]),
                    int(default_params.get("E_T_target", 50)),
                    key="battery_E_T_target",
                )
                st.markdown(f"**{t('group.efficiency')}**")
                battery_params["η_charge"] = st.slider(
                    t("field.eta_charge"),
                    0.7,
                    1.0,
                    float(default_params.get("η_charge", 0.9)),
                    format="%.2f",
                    key="battery_eta_charge",
                )
                battery_params["η_discharge"] = st.slider(
                    t("field.eta_discharge"),
                    0.7,
                    1.0,
                    float(default_params.get("η_discharge", 0.9)),
                    format="%.2f",
                    key="battery_eta_discharge",
                )
                st.markdown(f"**{t('group.soc')}**")
                battery_params["SOC_min"] = st.slider(
                    t("field.soc_min"),
                    0.1,
                    0.3,
                    float(default_params.get("SOC_min", 0.2)),
                    format="%.2f",
                    key="battery_SOC_min",
                )
                battery_params["SOC_max"] = st.slider(
                    t("field.soc_max"),
                    0.7,
                    0.9,
                    float(default_params.get("SOC_max", 0.8)),
                    format="%.2f",
                    key="battery_SOC_max",
                )
            with market_tab:
                st.markdown(f"**{t('group.cost')}**")
                battery_params["k"] = st.number_input(
                    t("field.k"),
                    0.0,
                    0.5,
                    float(default_params.get("k", 0.01)),
                    format="%.4f",
                    key="battery_k",
                )
                battery_params["N_cycle_max"] = st.number_input(
                    t("field.n_cycle_max"),
                    1,
                    10,
                    int(default_params.get("N_cycle_max", 5)),
                    key="battery_N_cycle_max",
                )
                battery_params["C_OM"] = st.number_input(
                    t("field.c_om"),
                    0,
                    5000,
                    int(default_params.get("C_OM", 100)),
                    key="battery_C_OM",
                )
                st.markdown(f"**{t('group.constraints')}**")
                battery_params["R_ramp"] = st.number_input(
                    t("field.r_ramp"),
                    0.1,
                    50.0,
                    float(default_params.get("R_ramp", 2.0)),
                    key="battery_R_ramp",
                )
            with regulation_tab:
                st.caption(
                    bi(
                        language,
                        "以下为模型场景参数，不是吉木萨尔电站公开实测结算参数。",
                        "These are scenario inputs, not published Jimsar settlement measurements.",
                    )
                )
                regulation_values["capacity_price_cny_per_mw_h"] = st.number_input(
                    bi(language, "容量补偿价（元/MW·h）", "Capacity price (CNY/MW·h)"),
                    min_value=0.0,
                    value=8.0,
                    step=0.5,
                    key="reg_capacity_price",
                )
                regulation_values["performance_score"] = st.slider(
                    bi(language, "性能得分", "Performance score"),
                    0.0,
                    1.0,
                    0.95,
                    0.01,
                    key="reg_performance",
                )
                regulation_values["mileage_ratio"] = st.number_input(
                    bi(language, "里程系数", "Mileage ratio"),
                    min_value=0.0,
                    value=0.25,
                    step=0.05,
                    key="reg_mileage_ratio",
                )
                regulation_values["reserve_duration_hours"] = st.number_input(
                    bi(language, "持续响应时长（小时）", "Reserve duration (hours)"),
                    min_value=0.05,
                    max_value=1.0,
                    value=0.25,
                    step=0.05,
                    key="reg_duration",
                )
                regulation_values["max_market_share"] = st.slider(
                    bi(language, "最大市场需求占比", "Maximum demand share"),
                    0.01,
                    1.0,
                    0.20,
                    0.01,
                    key="reg_market_share",
                )
                regulation_values[
                    "regulation_degradation_cost_cny_per_mwh"
                ] = st.number_input(
                    bi(language, "调频退化成本（元/MWh）", "Regulation degradation (CNY/MWh)"),
                    min_value=0.0,
                    value=2.0,
                    step=0.1,
                    key="reg_degradation",
                )
                regulation_values["regulation_om_cost_cny_per_mw_h"] = st.number_input(
                    bi(language, "调频运维成本（元/MW·h）", "Regulation O&M (CNY/MW·h)"),
                    min_value=0.0,
                    value=0.10,
                    step=0.05,
                    key="reg_om",
                )
                regulation_values["efficiency_loss_fraction"] = st.slider(
                    bi(language, "响应能量损耗比例", "Response energy loss fraction"),
                    0.0,
                    0.20,
                    0.02,
                    0.01,
                    key="reg_efficiency_loss",
                )
                regulation_values[
                    "regulation_ramp_mw_per_interval"
                ] = st.number_input(
                    bi(language, "调频爬坡上限（MW/15min）", "Regulation ramp (MW/15min)"),
                    min_value=0.1,
                    value=20.0,
                    step=1.0,
                    key="reg_ramp",
                )

        uploaded_regulation_file = None
        input_col, regulation_col, summary_col = st.columns(
            [1.25, 1.25 if comparison_mode else 0.01, 0.9]
        )
        with input_col:
            uploaded_file = st.file_uploader(
                t("field.price_csv"),
                type=["csv"],
                key="price_forecast_file",
            )
        with regulation_col:
            if comparison_mode:
                uploaded_regulation_file = st.file_uploader(
                    bi(
                        language,
                        "调频历史数据（可选 CSV）",
                        "Regulation history (optional CSV)",
                    ),
                    type=["csv"],
                    key="regulation_history_file",
                )
                st.caption(
                    bi(
                        language,
                        "未上传时使用7日合成调频样例；仅用于方法演示和系统测试，不代表任何真实电站或市场的实测数据。",
                        "Uses a seven-day synthetic regulation sample when omitted; for demonstration and system testing only, not measured data from any real station or market.",
                    )
                )
        with summary_col:
            st.markdown(
                f'<div class="pm-section-label">{t("parameter.summary")}</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                f"{t('parameter.capacity')}: {battery_params['E_rated']} MWh  ·  "
                f"{t('parameter.power')}: {battery_params['P_rated']} MW"
            )
            st.caption(
                f"{t('parameter.soc_range')}: "
                f"{battery_params['SOC_min']:.0%}–{battery_params['SOC_max']:.0%}  ·  "
                f"{t('field.time_step')}: {time_step} min"
            )

        solve_button = st.button(
            t("action.solve"),
            type="primary",
            use_container_width=True,
            key="solve_decision",
        )

    if solve_button and uploaded_file is None:
        st.warning(t("input.file_missing"))

    if solve_button and uploaded_file is not None:
        try:
            price_forecast = validate_day_ahead_prices(pd.read_csv(uploaded_file))
            battery_params = validate_battery_params(battery_params)

            st.subheader(t("progress.title"))
            with st.container(border=True):
                progress_bar = st.progress(0)
                with st.expander(t("action.show_logs"), expanded=True):
                    log_container = st.container()

            log_container.info(t("progress.started"))
            progress_bar.progress(10, text=t("progress.baseline_running"))
            log_container.write(t("progress.baseline_running"))

            market_model = FlowBatteryDayAheadMarketModel(
                price_forecast,
                battery_params,
                solver_type=solver_type,
            )
            optimal_model, solve_results = market_model.solve_model()

            if optimal_model is None:
                st.error(t("error.solve"))
                log_container.error(t("error.solve"))
                st.stop()

            progress_bar.progress(40, text=t("progress.baseline_done"))
            log_container.success(t("progress.baseline_done"))

            progress_bar.progress(50, text=t("progress.rarr_running"))
            log_container.write(t("progress.rarr_running"))
            with st.spinner(t("progress.rarr_spinner")):
                optimal_mode = mode_selection_rarr(
                    optimal_model,
                    price_forecast,
                    battery_params,
                )
            mode_text = "报量不报价" if optimal_mode == 0 else "报量报价"
            mode_display = (
                t("mode.quantity_only")
                if optimal_mode == 0
                else t("mode.quantity_price")
            )

            progress_bar.progress(
                80,
                text=t("progress.rarr_done", mode=mode_display),
            )
            log_container.success(t("progress.rarr_done", mode=mode_display))

            progress_bar.progress(90, text=t("progress.output_running"))
            log_container.write(t("progress.output_running"))
            kpis = calculate_kpis(
                optimal_model,
                price_forecast,
                battery_params,
            )
            results_df = create_results_dataframe(
                optimal_model,
                price_forecast,
                battery_params,
                time_step,
            )
            figure = generate_comprehensive_visualization(
                optimal_model,
                price_forecast,
                battery_params,
            )

            if optimal_mode == 1:
                bid_table = generate_segmented_bid_table(
                    optimal_model,
                    price_forecast,
                    battery_params,
                )
            else:
                bid_table = generate_bid_table(
                    optimal_model,
                    price_forecast,
                    battery_params,
                )
            if not isinstance(bid_table, pd.DataFrame):
                bid_table = pd.DataFrame(bid_table)

            market_extension = None
            if comparison_mode:
                progress_bar.progress(
                    82,
                    text=bi(language, "正在预测调频里程价格。", "Forecasting regulation mileage prices."),
                )
                if uploaded_regulation_file is None:
                    regulation_history, regulation_source = (
                        load_default_regulation_history()
                    )
                else:
                    regulation_history = pd.read_csv(uploaded_regulation_file)
                    regulation_source = "uploaded"
                    regulation_history = normalize_regulation_history(
                        regulation_history
                    )
                forecast_result = forecast_regulation_prices(
                    regulation_history,
                    random_state=42,
                    data_source=regulation_source,
                    price_upper_limit=regulation_values["price_upper_limit"],
                    price_min_unit=regulation_values["price_min_unit"],
                )
                regulation_market = build_regulation_market_frame(
                    forecast_result.hourly_forecast,
                    capacity_price_cny_per_mw_h=regulation_values[
                        "capacity_price_cny_per_mw_h"
                    ],
                    performance_score=regulation_values["performance_score"],
                    mileage_ratio=regulation_values["mileage_ratio"],
                )
                regulation_config = build_regulation_config(regulation_values)
                baseline_schedule = build_baseline_schedule(
                    optimal_model, price_forecast
                )
                sequential_result = SequentialRegulationModel(
                    baseline_schedule,
                    battery_params,
                    regulation_market,
                    regulation_config,
                    solver_type=solver_type,
                ).solve()
                if sequential_result.status != "optimal":
                    raise RuntimeError(
                        f"Sequential regulation solve: {sequential_result.status}; "
                        f"{'; '.join(sequential_result.diagnostics)}"
                    )

                progress_bar.progress(
                    90,
                    text=bi(language, "正在执行日前—调频联合优化。", "Running joint energy-regulation optimization."),
                )
                joint_result = JointEnergyRegulationModel(
                    price_forecast,
                    battery_params,
                    regulation_market,
                    regulation_config,
                    solver_type=solver_type,
                ).solve()
                if joint_result.status != "optimal":
                    raise RuntimeError(
                        f"Joint market solve: {joint_result.status}; "
                        f"{'; '.join(joint_result.diagnostics)}"
                    )
                comparison = build_market_comparison(
                    kpis["总净利润"],
                    sequential_result.kpis["total_profit_cny"],
                    joint_result.kpis["total_profit_cny"],
                )
                if (
                    joint_result.kpis["total_profit_cny"] + 0.01
                    < sequential_result.kpis["total_profit_cny"]
                ):
                    raise RuntimeError(
                        "联合模型结果低于顺序可行解，请检查模型约束一致性。"
                    )
                market_extension = {
                    "forecast": forecast_result,
                    "regulation_market": regulation_market,
                    "sequential": sequential_result,
                    "joint": joint_result,
                    "comparison": comparison,
                    "data_source": regulation_source,
                }

            save_decision_record(
                kpis,
                mode_text,
                {
                    "market_mode": market_mode,
                    "da_profit": kpis["总净利润"],
                    "sequential_profit": (
                        market_extension["sequential"].kpis["total_profit_cny"]
                        if market_extension
                        else None
                    ),
                    "joint_profit": (
                        market_extension["joint"].kpis["total_profit_cny"]
                        if market_extension
                        else None
                    ),
                    "solver_name": solver_type,
                    "solver_status": "optimal",
                    "data_source": (
                        market_extension["data_source"]
                        if market_extension
                        else "day-ahead upload"
                    ),
                },
            )
            log_container.info(t("progress.saved"))

            st.session_state["decision_view"] = {
                "kpis": kpis,
                "results_df": results_df,
                "figure": figure,
                "optimal_mode": optimal_mode,
                "mode_text": mode_text,
                "bid_table": bid_table,
                "market_mode": market_mode,
                "market_extension": market_extension,
            }
            progress_bar.progress(100, text=t("progress.output_done"))
            log_container.success(t("progress.output_done"))
            st.session_state["sidebar_section"] = "results"
            st.rerun()

        except Exception as error:
            st.error(t("error.workflow", error=error))
            st.exception(error)

    if "decision_view" in st.session_state:
        view = st.session_state["decision_view"]
        if view.get("market_mode") == "comparison" and view.get(
            "market_extension"
        ):
            st.divider()
            st.subheader(
                bi(language, "多市场决策结果", "Multi-market decision results")
            )
            render_multi_market_results(view, language)
            return
        kpis = view["kpis"]
        optimal_mode = view["optimal_mode"]
        mode_display = (
            t("mode.quantity_only")
            if optimal_mode == 0
            else t("mode.quantity_price")
        )

        st.divider()
        st.subheader(t("result.title"))
        st.caption(mode_display)
        currency = "元" if language == "zh" else "CNY"
        cycle_unit = "次" if language == "zh" else ""
        render_metric_strip(
            [
                (
                    t("result.net_profit"),
                    f"{kpis['总净利润']:,.2f} {currency}",
                    f"{kpis['总放电收益']:,.2f} {currency}",
                ),
                (
                    t("result.discharge_revenue"),
                    f"{kpis['总放电收益']:,.2f} {currency}",
                    None,
                ),
                (
                    t("result.cycles"),
                    f"{kpis['等效循环次数']:.3f} {cycle_unit}".strip(),
                    None,
                ),
                (
                    t("result.throughput"),
                    f"{kpis['总能量吞吐']:.2f} MWh",
                    None,
                ),
                (
                    t("result.avg_profit"),
                    f"{kpis['平均度电利润']:.2f} {currency}/MWh",
                    None,
                ),
            ]
        )

        st.markdown(
            f'<div class="pm-section-label">{t("result.schedule")}</div>',
            unsafe_allow_html=True,
        )
        themed_figure = apply_plotly_theme(
            copy.deepcopy(view["figure"]),
            language,
        )
        st.plotly_chart(themed_figure, use_container_width=True)

        details_col, bid_col = st.columns([1.25, 1])
        results_df = view["results_df"]
        bid_table = view["bid_table"]
        downloads = build_download_artifacts(
            results_df,
            bid_table,
            optimal_mode,
        )

        with details_col:
            st.markdown(
                f'<div class="pm-section-label">{t("result.details")}</div>',
                unsafe_allow_html=True,
            )
            st.caption(t("result.details_hint"))
            display_results = results_df
            if language == "en":
                display_results = results_df.rename(
                    columns={
                        "Time": "Time",
                        "Price (元/MWh)": "Price (CNY/MWh)",
                        "Charge_Power (MW)": "Charging Power (MW)",
                        "Discharge_Power (MW)": "Discharging Power (MW)",
                        "Net_Power (MW)": "Net Power (MW)",
                        "Energy_State (MWh)": "Energy (MWh)",
                        "SOC (%)": "SOC (%)",
                    }
                )
            st.dataframe(display_results, use_container_width=True)
            st.download_button(
                label=t("action.download_details"),
                data=downloads["schedule"]["data"],
                file_name=downloads["schedule"]["file_name"],
                mime="text/csv",
                key="download_schedule",
            )

        with bid_col:
            st.markdown(
                f'<div class="pm-section-label">{t("result.bid_strategy")}</div>',
                unsafe_allow_html=True,
            )
            st.caption(
                t(
                    "result.mode_reason_qp"
                    if optimal_mode == 1
                    else "result.mode_reason_qnp"
                )
            )
            display_bids = localize_bid_table(bid_table, language)
            st.dataframe(display_bids, use_container_width=True)
            st.download_button(
                label=t("action.download_bid"),
                data=downloads["bid"]["data"],
                file_name=downloads["bid"]["file_name"],
                mime="text/csv",
                key="download_bid",
            )


if __name__ == "__main__":
    main()
