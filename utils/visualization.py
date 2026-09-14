import plotly.graph_objects as go
import plotly.subplots as sp
import pyomo.environ as pyo


def generate_comprehensive_visualization(model, price_forecast, battery_params):
    """
    生成一个精美、高级且信息丰富的综合可视化图表。

    Args:
        model (pyo.ConcreteModel): 已求解的Pyomo模型。
        price_forecast (list or np.array): 电价预测数据。
        battery_params (dict): 电池参数字典。

    Returns:
        go.Figure: 一个Plotly图表对象。
    """
    T = len(price_forecast)

    # --- 1. 数据提取 ---
    charge_power = [pyo.value(model.P_charge[t]) for t in range(T)]
    discharge_power = [pyo.value(model.P_discharge[t]) for t in range(T)]
    soc_percent = [pyo.value(model.E[t]) / battery_params['E_rated'] * 100 for t in range(T)]

    # 使用pandas创建时间索引，Plotly能更好地处理datetime对象
    # 假设时间步长为15分钟，如果不是，需要从外部传入
    # time_step_minutes = 15
    # time_index = pd.to_datetime(pd.date_range(start='2023-01-01', periods=T, freq=f'{time_step_minutes}T'))
    # 为了简化，我们继续使用原来的时间标签，但datetime是更优的选择
    time_labels = [f"{(h * 15) // 60:02d}:{(h * 15) % 60:02d}" for h in range(T)]

    # --- 2. 创建带有双Y轴的子图 ---
    fig = sp.make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.15,  # 增加子图间距
        subplot_titles=('<b>市场价格与储能功率调度</b>', '<b>电池荷电状态 (SOC)</b>'),
        specs=[[{"secondary_y": True}],  # 第一行图表拥有次Y轴
               [{"secondary_y": False}]]  # 第二行图表没有
    )

    # --- 3. 与正式页面一致的低噪声浅色方案 ---
    colors = {
        'price': '#2858D6',
        'charge': 'rgba(79, 141, 109, 0.46)',
        'discharge': 'rgba(184, 117, 60, 0.42)',
        'soc': '#5B6370',
        'soc_area': 'rgba(91, 99, 112, 0.12)',
        'soc_bounds': '#989CA2'
    }

    # --- 4. 绘制第一个子图：功率 & 电价 ---
    # 功率曲线 (次Y轴) - 使用面积图更显平滑
    fig.add_trace(go.Scatter(
        x=time_labels,
        y=[-c for c in charge_power],
        name='充电功率',
        fill='tozeroy',
        mode='lines',
        line=dict(width=0),  # 隐藏轮廓线，纯面积图
        fillcolor=colors['charge'],
        hovertemplate='充电功率: %{y:.2f} MW<extra></extra>'
    ), secondary_y=True, row=1, col=1)

    fig.add_trace(go.Scatter(
        x=time_labels,
        y=discharge_power,
        name='放电功率',
        fill='tozeroy',
        mode='lines',
        line=dict(width=0),
        fillcolor=colors['discharge'],
        hovertemplate='放电功率: %{y:.2f} MW<extra></extra>'
    ), secondary_y=True, row=1, col=1)

    # 电价曲线 (主Y轴)
    fig.add_trace(go.Scatter(
        x=time_labels,
        y=price_forecast,
        name='电价',
        mode='lines+markers',
        line=dict(color=colors['price'], width=3),
        marker=dict(size=4),
        hovertemplate='时间: %{x}<br>电价: %{y:.2f} 元/MWh<extra></extra>'
    ), secondary_y=False, row=1, col=1)

    # --- 5. 绘制第二个子图：SOC ---
    # SOC曲线
    fig.add_trace(go.Scatter(
        x=time_labels,
        y=soc_percent,
        name='SOC',
        mode='lines',
        line=dict(color=colors['soc'], width=2.5),
        fill='tozeroy',
        fillcolor=colors['soc_area'],
        hovertemplate='SOC: %{y:.1f}%<extra></extra>'
    ), row=2, col=1)

    # 添加SOC上下限参考线
    soc_min_percent = battery_params['SOC_min'] * 100
    soc_max_percent = battery_params['SOC_max'] * 100
    fig.add_hline(y=soc_max_percent, line_dash="dot", row=2, col=1,
                  annotation_text=f"SOC Max: {soc_max_percent:.0f}%",
                  annotation_position="bottom right",
                  line_color=colors['soc_bounds'])
    fig.add_hline(y=soc_min_percent, line_dash="dot", row=2, col=1,
                  annotation_text=f"SOC Min: {soc_min_percent:.0f}%",
                  annotation_position="bottom right",
                  line_color=colors['soc_bounds'])

    # --- 6. 更新整体布局和样式 ---
    fig.update_layout(
        height=650,
        title_text="<b>储能电站日前市场联合优化策略</b>",
        title_x=0.0,
        template='plotly_white',  # 使用简洁的白色主题
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        hovermode='x unified',  # 统一x轴的悬停信息
        margin=dict(l=56, r=42, t=82, b=58),
        paper_bgcolor='#FFFFFF',
        plot_bgcolor='#FFFFFF',
        font=dict(family='Arial, Microsoft YaHei, sans-serif', color='#18202A')
    )

    # --- 7. 更新坐标轴样式 ---
    # 主Y轴 (电价)
    fig.update_yaxes(
        title_text="<b>电价 (元/MWh)</b>",
        title_font=dict(color=colors['price']),
        tickfont=dict(color=colors['price']),
        row=1, col=1, secondary_y=False
    )
    # 次Y轴 (功率)
    fig.update_yaxes(
        title_text="<b>功率 (MW)</b>",
        title_font=dict(color='#444'),
        tickfont=dict(color='#444'),
        showgrid=False,  # 隐藏次轴网格线，避免杂乱
        range=[-battery_params['P_rated'] * 1.1, battery_params['P_rated'] * 1.1],  # 对称范围
        row=1, col=1, secondary_y=True
    )
    # SOC Y轴
    fig.update_yaxes(
        title_text="<b>荷电状态 (SOC)</b>",
        range=[0, 100],
        ticksuffix="%",
        row=2, col=1
    )
    # X轴
    fig.update_xaxes(
        title_text="<b>时间 (小时:分钟)</b>",
        tickangle=0,  # 让刻度标签水平显示
        nticks=12,  # 减少刻度数量，避免拥挤
        showspikes=True,  # 开启悬停时的十字准星线
        spikemode='toaxis+across',
        spikesnap='cursor',
        spikethickness=1,
        row=2, col=1
    )
    fig.update_xaxes(showticklabels=False, row=1, col=1)  # 隐藏顶部图的x轴标签
    fig.update_xaxes(gridcolor='#ECECEA', zerolinecolor='#D9DADD')
    fig.update_yaxes(gridcolor='#ECECEA', zerolinecolor='#D9DADD')

    return fig
