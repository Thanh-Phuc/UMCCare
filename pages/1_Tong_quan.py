# pages/1_Tong_Quan.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- Configuration ---
GA_COLOR_SEQUENCE = px.colors.qualitative.Plotly
TEMPLATE = "plotly_white"
EXPECTED_CHANNELS = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care'] # Consistent list

st.set_page_config(page_title="Tổng quan", layout="wide")
st.title("📊 Tổng quan dữ liệu đăng ký")

# --- Analysis Function (Revised for Date Range and Pivoted Data) ---
def overview_analysis(data, start_date, end_date):
    """Perform overview analysis for the selected date range using pivoted data."""

    # Filter data based on the selected date range (using Month index level)
    mask = (data.index.get_level_values('Month') >= start_date) & \
           (data.index.get_level_values('Month') <= end_date)
    data_filtered = data[mask].copy()

    if data_filtered.empty:
        st.warning(f"Không có dữ liệu trong khoảng thời gian đã chọn ({start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}).")
        return

    date_range_str = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    st.header(f"Tổng quan dữ liệu đăng ký ({date_range_str})")

    # --- Calculate Metrics ---
    col1, col2, col3, col4 = st.columns(4)

    # Aggregate totals for the filtered period
    total_registrations_selected = data_filtered['Grand Total'].sum()
    channel_totals_selected = {ch: data_filtered[ch].sum() for ch in EXPECTED_CHANNELS if ch in data_filtered.columns}

    # Aggregate monthly totals
    monthly_totals_series = data_filtered.groupby(level='Month')['Grand Total'].sum()

    # Metric 1: Total Registrations
    with col1:
        st.metric(f"Tổng lượt đăng ký", f"{total_registrations_selected:,.0f}")

    # Metric 2: Change last month vs first month in range
    with col2:
        all_months_in_range = sorted(data_filtered.index.get_level_values('Month').unique())
        if len(all_months_in_range) > 1:
            last_month_total = monthly_totals_series.iloc[-1] if not monthly_totals_series.empty else 0
            first_month_total = monthly_totals_series.iloc[0] if not monthly_totals_series.empty else 0
            delta_last_first = last_month_total - first_month_total
            if first_month_total > 0:
                 perc_last_first = (delta_last_first / first_month_total) * 100
                 st.metric(f"{all_months_in_range[-1].strftime('%b %y')} vs {all_months_in_range[0].strftime('%b %y')}", f"{perc_last_first:.1f}%", delta=f"{delta_last_first:,.0f}")
            elif delta_last_first != 0:
                 st.metric(f"{all_months_in_range[-1].strftime('%b %y')} vs {all_months_in_range[0].strftime('%b %y')}", "Thay đổi", delta=f"{delta_last_first:,.0f}")
            else:
                 st.metric(f"{all_months_in_range[-1].strftime('%b %y')} vs {all_months_in_range[0].strftime('%b %y')}", "Không đổi", delta="0")
        elif len(all_months_in_range) == 1:
             st.metric("Thay đổi so với kỳ trước", "Chỉ có 1 tháng")
        else:
             st.metric("Thay đổi so với kỳ trước", "N/A")

    # Metric 3: Top Channel
    with col3:
        total_channel_regs_selected = sum(channel_totals_selected.values())
        if total_channel_regs_selected > 0:
            top_channel = max(channel_totals_selected, key=channel_totals_selected.get)
            top_channel_pct = (channel_totals_selected[top_channel] / total_channel_regs_selected) * 100
            st.metric(f"Kênh hàng đầu", top_channel, f"{top_channel_pct:.1f}%")
        else:
            st.metric(f"Kênh hàng đầu", "N/A", "0.0%")

    # Metric 4: Top Specialty
    with col4:
        # Sum 'Grand Total' per specialty *within the filtered date range*
        specialty_totals_selected = data_filtered.groupby(level='Chuyên khoa')['Grand Total'].sum()
        if not specialty_totals_selected.empty and total_registrations_selected > 0:
            top_specialty = specialty_totals_selected.idxmax()
            top_specialty_total_selected = specialty_totals_selected.max()
            top_specialty_pct_selected = (top_specialty_total_selected / total_registrations_selected) * 100
            st.metric(f"Chuyên khoa hàng đầu", top_specialty, f"{top_specialty_pct_selected:.1f}%")
        else:
            st.metric(f"Chuyên khoa hàng đầu", "N/A", "0.0%")

    # --- Monthly Trend Chart ---
    st.subheader("Xu hướng đăng ký theo tháng")

    # Aggregate data by month for plotting
    monthly_agg = data_filtered.groupby(level='Month').sum()

    # Ensure all months in the selected range are present
    full_month_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    monthly_agg = monthly_agg.reindex(full_month_range, fill_value=0)

    # Plot
    fig_trend = go.Figure()

    channels_in_data = [ch for ch in EXPECTED_CHANNELS if ch in monthly_agg.columns]
    for i, channel in enumerate(channels_in_data):
        fig_trend.add_trace(go.Bar(
            x=monthly_agg.index,
            y=monthly_agg[channel],
            name=channel,
            marker_color=GA_COLOR_SEQUENCE[i % len(GA_COLOR_SEQUENCE)]
        ))

    if 'Grand Total' in monthly_agg.columns:
        fig_trend.add_trace(go.Scatter(
            x=monthly_agg.index,
            y=monthly_agg['Grand Total'],
            mode='lines+markers',
            name='Tổng lượt đăng ký',
            line=dict(width=3, color='dimgray'),
            marker=dict(size=8, color='black')
        ))

    fig_trend.update_layout(
        title=f'Xu hướng đăng ký theo tháng ({date_range_str})',
        xaxis_title='Tháng',
        yaxis_title='Lượt đăng ký',
        barmode='stack',
        height=500,
        template=TEMPLATE,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        yaxis=dict(showgrid=True, gridwidth=1, gridcolor='whitesmoke'),
        xaxis=dict(
            tickformat="%b %Y",
            showgrid=False,
            dtick="M1",
            tickangle=-45
            ),
        plot_bgcolor='white'
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- Top 10 Specialties Chart ---
    st.subheader(f"Top 10 chuyên khoa ({date_range_str})")

    if not specialty_totals_selected.empty:
        top10_specialties = specialty_totals_selected.nlargest(10)

        fig_top10 = px.bar(
            x=top10_specialties.values,
            y=top10_specialties.index,
            orientation='h',
            labels={'x': 'Tổng lượt đăng ký', 'y': 'Chuyên khoa'},
            text=top10_specialties.values
        )
        fig_top10.update_traces(
             marker_color=GA_COLOR_SEQUENCE[0],
             texttemplate='%{text:,.0f}',
             textposition='outside'
        )
        fig_top10.update_layout(
            title=f'Top 10 chuyên khoa theo lượt đăng ký ({date_range_str})',
            height=500,
            yaxis=dict(autorange="reversed", showgrid=False, ticksuffix='  '),
            xaxis=dict(showgrid=True, gridwidth=1, gridcolor='whitesmoke'),
            xaxis_title='Tổng lượt đăng ký',
            yaxis_title=None,
            template=TEMPLATE,
            bargap=0.3,
            plot_bgcolor='white',
            margin=dict(l=10, r=10, t=50, b=50, pad=5)
        )
        st.plotly_chart(fig_top10, use_container_width=True)
    else:
        st.info("Không có dữ liệu đăng ký chuyên khoa trong khoảng thời gian đã chọn.")


# --- Load data and run analysis ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    start_date = st.session_state.get('start_date')
    end_date = st.session_state.get('end_date')

    if start_date and end_date:
         overview_analysis(data_loaded, start_date, end_date)
    else:
         st.warning("Vui lòng chọn khoảng thời gian phân tích ở thanh bên trái.")
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem phân tích.")