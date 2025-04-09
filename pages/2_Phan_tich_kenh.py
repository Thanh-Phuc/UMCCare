# pages/2_Phan_Tich_Kenh_Dang_Ky.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Phân tích kênh", layout="wide")

st.title("📈 Phân tích kênh đăng ký")

# --- Function from original script ---
def channel_analysis(data):
    """Analyze registration channels"""
    st.header("Phân tích kênh đăng ký")

    # Create columns for selection
    col1, col2 = st.columns([1, 3]) # Adjust column widths if needed

    channels_available = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care']
    # Filter out channels that don't exist in the data for any quarter
    channels_in_data = [ch for ch in channels_available if any(f'Q{q}_{ch}' in data.columns for q in range(1, 5))]

    if not channels_in_data:
        st.warning("Không tìm thấy dữ liệu cho các kênh đăng ký tiêu chuẩn (Bàn Khám, PKH, Tổng đài, UMC Care).")
        return

    with col1:
        # Quarter selection
        quarter = st.selectbox(
            'Chọn quý:',
            ['Tất cả', 'Q1', 'Q2', 'Q3', 'Q4'],
            key='channel_quarter_select'
        )

        # Channel selection
        selected_channels = st.multiselect(
            'Chọn kênh đăng ký:',
            channels_in_data,
            default=channels_in_data,
            key='channel_select'
        )

    if not selected_channels:
        st.warning("Vui lòng chọn ít nhất một kênh đăng ký.")
        return

    # Calculate channel distribution
    channel_data_dist = {}
    if quarter == 'Tất cả':
        # Sum across all quarters
        for channel in selected_channels:
            channel_sum = 0
            for q in range(1, 5):
                col_name = f'Q{q}_{channel}'
                if col_name in data.columns:
                    channel_sum += data[col_name].sum()
            channel_data_dist[channel] = channel_sum
    else:
        # Get data for selected quarter
        q_num = int(quarter[1])
        for channel in selected_channels:
             col_name = f'Q{q_num}_{channel}'
             channel_data_dist[channel] = data[col_name].sum() if col_name in data.columns else 0

    # Filter out channels with zero registrations for the pie chart
    channel_data_pie = {k: v for k, v in channel_data_dist.items() if v > 0}

    with col2:
        if channel_data_pie:
            # Create pie chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(channel_data_pie.keys()),
                values=list(channel_data_pie.values()),
                hole=.4,
                textinfo='label+percent',
                insidetextorientation='radial',
                marker=dict(colors=px.colors.qualitative.Pastel) # Use different color scheme
            )])

            fig_pie.update_layout(
                title=f'Phân bố lượt đăng ký theo kênh ({quarter})',
                height=400,
                margin=dict(l=20, r=20, t=50, b=20), # Adjust margins
                legend_title_text='Kênh'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info(f"Không có lượt đăng ký nào cho các kênh đã chọn trong {quarter}.")


    # Channel trend over quarters
    st.subheader("Xu hướng kênh đăng ký theo thời gian")

    # Create a line chart showing trends for selected channels
    fig_trend = go.Figure()
    quarters_list = ['Q1', 'Q2', 'Q3', 'Q4']

    for channel in selected_channels:
        channel_trend_values = []
        for q in range(1, 5):
            col_name = f'Q{q}_{channel}'
            channel_trend_values.append(data[col_name].sum() if col_name in data.columns else 0)

        fig_trend.add_trace(go.Scatter(
            x=quarters_list,
            y=channel_trend_values,
            mode='lines+markers',
            name=channel
        ))

    fig_trend.update_layout(
        title='Xu hướng kênh đăng ký theo quý',
        xaxis_title='Quý',
        yaxis_title='Lượt đăng ký',
        height=400,
        template='plotly_white',
        hovermode='x unified'
    )

    st.plotly_chart(fig_trend, use_container_width=True)

# --- Load data and run analysis ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    channel_analysis(data_loaded)
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem phân tích.")