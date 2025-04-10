# pages/2_Phan_Tich_Kenh_Dang_Ky.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- Configuration ---
GA_COLOR_SEQUENCE = px.colors.qualitative.Plotly
TEMPLATE = "plotly_white"
EXPECTED_CHANNELS = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care']

st.set_page_config(page_title="Phân tích kênh", layout="wide")
st.title("📈 Phân tích kênh đăng ký")

# --- Analysis Function ---
def channel_analysis(data, start_date, end_date):
    """Analyze registration channels for the selected date range using pivoted data."""

    # Filter data based on the selected date range
    mask = (data.index.get_level_values('Month') >= start_date) & \
           (data.index.get_level_values('Month') <= end_date)
    data_filtered = data[mask].copy()

    date_range_str = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    st.header(f"Phân tích kênh đăng ký ({date_range_str})")

    if data_filtered.empty:
        st.warning(f"Không có dữ liệu trong khoảng thời gian đã chọn ({date_range_str}).")
        return

    # Identify available standard channels in the filtered data
    channels_in_data = [ch for ch in EXPECTED_CHANNELS if ch in data_filtered.columns and data_filtered[ch].sum() > 0]

    if not channels_in_data:
        st.warning(f"Không tìm thấy dữ liệu cho các kênh đăng ký tiêu chuẩn trong khoảng thời gian đã chọn.")
        return

    # --- Controls ---
    st.subheader("Tùy chọn hiển thị")
    col1, col2 = st.columns([1, 3]) # Give more space to the chart

    with col1:
        analysis_period = st.selectbox(
            'Phân bố theo:',
             [f'Tổng hợp ({date_range_str})', 'Từng tháng'],
            key='channel_period_select_page2' # Unique key
        )
        selected_channels_filter = st.multiselect(
            'Lọc kênh hiển thị:',
            channels_in_data,
            default=channels_in_data,
            key='channel_select_filter_page2'
        )

    if not selected_channels_filter:
        st.warning("Vui lòng chọn ít nhất một kênh để hiển thị.")
        return

    # --- Distribution Chart ---
    if analysis_period == f'Tổng hợp ({date_range_str})':
        st.subheader(f"Phân bố kênh tổng hợp ({date_range_str})")
        # Calculate totals for selected channels within the filtered data
        channel_data_dist = data_filtered[selected_channels_filter].sum().to_dict()

        channel_data_pie = {k: v for k, v in channel_data_dist.items() if v > 0}

        with col2:
            if channel_data_pie:
                fig_pie = go.Figure(data=[go.Pie(
                    labels=list(channel_data_pie.keys()),
                    values=list(channel_data_pie.values()),
                    hole=.4,
                    textinfo='percent+label',
                    marker=dict(colors=GA_COLOR_SEQUENCE),
                    pull=[0.05 if i==0 else 0 for i in range(len(channel_data_pie))]
                )])
                fig_pie.update_traces(textposition='outside', textfont_size=12)
                fig_pie.update_layout(
                    height=400,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend_title_text='Kênh',
                    uniformtext_minsize=10, uniformtext_mode='hide',
                    template=TEMPLATE,
                    showlegend=True
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info(f"Không có lượt đăng ký cho các kênh đã chọn trong khoảng thời gian này.")

    else: # analysis_period == 'Từng tháng':
        st.subheader("Lượt đăng ký theo kênh và tháng")
        # Aggregate filtered data by month for the selected channels
        monthly_agg = data_filtered.groupby(level='Month')[selected_channels_filter].sum()
        # Reindex to ensure all months in the selection are present
        full_month_range = pd.date_range(start=start_date, end=end_date, freq='MS')
        monthly_agg = monthly_agg.reindex(full_month_range, fill_value=0)

        fig_monthly_dist = px.bar(monthly_agg, x=monthly_agg.index, y=selected_channels_filter,
                                 # title="Lượt đăng ký theo kênh và tháng", # Title in subheader
                                 template=TEMPLATE,
                                 color_discrete_sequence=GA_COLOR_SEQUENCE)
        fig_monthly_dist.update_layout(
            barmode='stack',
            xaxis_title='Tháng',
            yaxis_title='Lượt đăng ký',
            height=450,
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='whitesmoke'),
            xaxis=dict(tickformat="%b %Y", showgrid=False, dtick="M1", tickangle=-45),
            legend_title_text='Kênh',
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            plot_bgcolor='white'
        )
        # Display below controls if showing monthly breakdown
        st.plotly_chart(fig_monthly_dist, use_container_width=True)


    # --- Channel Trend Chart ---
    st.subheader("Xu hướng kênh đăng ký theo thời gian")

    # Aggregate filtered data by month for the selected channels again for clarity
    monthly_agg_trend = data_filtered.groupby(level='Month')[selected_channels_filter].sum()
    # Reindex
    full_month_range_trend = pd.date_range(start=start_date, end=end_date, freq='MS')
    monthly_agg_trend = monthly_agg_trend.reindex(full_month_range_trend, fill_value=0)

    fig_trend = go.Figure()
    for i, channel in enumerate(selected_channels_filter):
        fig_trend.add_trace(go.Scatter(
            x=monthly_agg_trend.index,
            y=monthly_agg_trend[channel],
            mode='lines+markers',
            name=channel,
            line=dict(color=GA_COLOR_SEQUENCE[i % len(GA_COLOR_SEQUENCE)]),
            marker=dict(size=6)
        ))

    fig_trend.update_layout(
        # title='Xu hướng kênh đăng ký theo tháng', # Title in subheader
        xaxis_title='Tháng',
        yaxis_title='Lượt đăng ký',
        height=400,
        template=TEMPLATE,
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='whitesmoke'),
        xaxis=dict(tickformat="%b %Y", showgrid=False, dtick="M1", tickangle=-45),
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        hovermode='x unified',
        plot_bgcolor='white'
    )
    st.plotly_chart(fig_trend, use_container_width=True)

# --- Load data and run analysis ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    start_date = st.session_state.get('start_date')
    end_date = st.session_state.get('end_date')

    if start_date and end_date:
         channel_analysis(data_loaded, start_date, end_date)
    else:
         st.warning("Vui lòng chọn khoảng thời gian phân tích ở thanh bên trái.")
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem phân tích.")