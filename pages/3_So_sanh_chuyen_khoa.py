# pages/3_So_Sanh_Chuyen_Khoa.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# --- Configuration ---
GA_COLOR_SEQUENCE = px.colors.qualitative.Plotly
TEMPLATE = "plotly_white"
EXPECTED_CHANNELS = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care']

st.set_page_config(page_title="So sánh chuyên khoa", layout="wide")
st.title("🔬 So sánh chuyên khoa")

# --- Analysis Function ---
def specialty_comparison(data, start_date, end_date):
    """Compare specialties for the selected date range using pivoted data."""

    # Filter data based on the selected date range
    mask = (data.index.get_level_values('Month') >= start_date) & \
           (data.index.get_level_values('Month') <= end_date)
    data_filtered = data[mask].copy()

    date_range_str = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    st.header(f"So sánh chuyên khoa ({date_range_str})")

    if data_filtered.empty:
        st.warning(f"Không có dữ liệu trong khoảng thời gian đã chọn ({date_range_str}).")
        return

    # Calculate total for selected period for default sorting
    specialty_totals_selected = data_filtered.groupby(level='Chuyên khoa')['Grand Total'].sum()

    # Get default specialties based on calculated total
    default_specialties = specialty_totals_selected.nlargest(5).index.tolist() if not specialty_totals_selected.empty else []

    # Select specialties to compare
    specialty_options = sorted(data_filtered.index.get_level_values('Chuyên khoa').unique().tolist())
    selected_specialties = st.multiselect(
        f'Chọn chuyên khoa để so sánh (Kỳ: {date_range_str}):',
        options=specialty_options,
        default=default_specialties,
        key='specialty_select_compare_page3'
    )

    if not selected_specialties:
        st.info("Vui lòng chọn ít nhất một chuyên khoa để so sánh.")
        return

    # Filter data further for selected specialties
    filtered_spec_data = data_filtered[data_filtered.index.get_level_values('Chuyên khoa').isin(selected_specialties)]

    # --- Comparison chart by Month ---
    st.subheader("So sánh lượt đăng ký theo chuyên khoa và tháng")

    # Aggregate by month for the selected specialties
    # Unstack 'Chuyên khoa' level to make it columns for plotting
    monthly_spec_agg = filtered_spec_data.groupby(level=['Month', 'Chuyên khoa'])['Grand Total'].sum().unstack(level='Chuyên khoa', fill_value=0)

    # Ensure all months in the range are present
    full_month_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    monthly_spec_agg = monthly_spec_agg.reindex(full_month_range, fill_value=0)

    if monthly_spec_agg.empty:
        st.warning("Không tìm thấy dữ liệu 'Grand Total' theo tháng cho các chuyên khoa đã chọn.")
    else:
        fig_month_compare = go.Figure()
        for i, spec in enumerate(selected_specialties):
            if spec in monthly_spec_agg.columns:
                 fig_month_compare.add_trace(go.Bar(
                     x=monthly_spec_agg.index,
                     y=monthly_spec_agg[spec],
                     name=spec,
                     marker_color=GA_COLOR_SEQUENCE[i % len(GA_COLOR_SEQUENCE)]
                 ))

        fig_month_compare.update_layout(
            # title=f'So sánh tổng lượt đăng ký theo chuyên khoa và tháng ({date_range_str})', # In subheader
            xaxis_title='Tháng',
            yaxis_title='Lượt đăng ký',
            barmode='group',
            height=500,
            template=TEMPLATE,
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='whitesmoke'),
            xaxis=dict(tickformat="%b %Y", showgrid=False, dtick="M1", tickangle=-45),
            legend_title_text='Chuyên khoa',
            plot_bgcolor='white',
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_month_compare, use_container_width=True)

    # --- Channel distribution for selected specialties (Overall for selected period) ---
    st.subheader(f"Phân bố kênh đăng ký tổng hợp ({date_range_str})")

    channels_in_data = [ch for ch in EXPECTED_CHANNELS if ch in filtered_spec_data.columns]
    if not channels_in_data:
        st.warning("Không tìm thấy dữ liệu theo kênh trong khoảng thời gian/chuyên khoa đã chọn.")
    else:
        # Calculate total per channel for each selected specialty over the selected period
        channel_dist_data = filtered_spec_data.groupby(level='Chuyên khoa')[channels_in_data].sum()
        # Ensure only selected specialties are included and in the right order
        channel_dist_data = channel_dist_data.reindex(selected_specialties, fill_value=0)

        fig_channel_dist = go.Figure()
        for i, channel in enumerate(channels_in_data):
            fig_channel_dist.add_trace(go.Bar(
                x=channel_dist_data.index,
                y=channel_dist_data[channel],
                name=channel,
                marker_color=GA_COLOR_SEQUENCE[i % len(GA_COLOR_SEQUENCE)]
            ))

        fig_channel_dist.update_layout(
            # title=f'Phân bố kênh đăng ký tổng hợp theo chuyên khoa ({date_range_str})', # In subheader
            xaxis_title='Chuyên khoa',
            yaxis_title='Tổng lượt đăng ký',
            barmode='stack',
            height=500,
            template=TEMPLATE,
            yaxis=dict(showgrid=True, gridwidth=1, gridcolor='whitesmoke'),
            xaxis=dict(showgrid=False, categoryorder='array', categoryarray=selected_specialties),
            legend_title_text='Kênh',
            plot_bgcolor='white',
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        st.plotly_chart(fig_channel_dist, use_container_width=True)


# --- Load data and run analysis ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    start_date = st.session_state.get('start_date')
    end_date = st.session_state.get('end_date')

    if start_date and end_date:
         # Pass the original loaded data (DataFrame) to the function
         specialty_comparison(data_loaded, start_date, end_date)
    else:
         st.warning("Vui lòng chọn khoảng thời gian phân tích ở thanh bên trái.")
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem phân tích.")