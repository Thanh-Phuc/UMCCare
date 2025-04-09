# pages/3_So_Sanh_Chuyen_Khoa.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="So sánh chuyên khoa", layout="wide")

st.title("🔬 So sánh chuyên khoa")

# --- Function from original script ---
def specialty_comparison(data):
    """Compare specialties"""
    st.header("So sánh chuyên khoa")

    # Use pre-calculated 'Total_Registrations' if available for default sorting
    default_specialties = []
    if 'Total_Registrations' in data.columns and not data.empty:
         default_specialties = data.sort_values('Total_Registrations', ascending=False).head(5)['Chuyên khoa'].tolist()

    # Select specialties to compare
    selected_specialties = st.multiselect(
        'Chọn chuyên khoa để so sánh:',
        options=data['Chuyên khoa'].unique().tolist(), # Use unique list
        default=default_specialties,
        key='specialty_select_compare'
    )

    if not selected_specialties:
        st.info("Vui lòng chọn ít nhất một chuyên khoa để so sánh.")
        return

    # Filter data for selected specialties
    filtered_data = data[data['Chuyên khoa'].isin(selected_specialties)].copy() # Use copy to avoid SettingWithCopyWarning

    # Comparison chart by Quarter
    st.subheader("So sánh lượt đăng ký theo chuyên khoa và quý")

    fig_quarter_compare = go.Figure()
    quarters_present = [q for q in range(1, 5) if f'Q{q}_Grand Total' in filtered_data.columns]

    if not quarters_present:
        st.warning("Không tìm thấy dữ liệu 'Grand Total' theo quý để so sánh.")
        return

    for quarter in quarters_present:
        fig_quarter_compare.add_trace(go.Bar(
            x=filtered_data['Chuyên khoa'],
            y=filtered_data[f'Q{quarter}_Grand Total'],
            name=f'Q{quarter}'
        ))

    fig_quarter_compare.update_layout(
        title='So sánh tổng lượt đăng ký theo chuyên khoa và quý',
        xaxis_title='Chuyên khoa',
        yaxis_title='Lượt đăng ký',
        barmode='group',
        height=500,
        template='plotly_white'
    )
    st.plotly_chart(fig_quarter_compare, use_container_width=True)

    # Channel distribution for selected specialties (Overall)
    st.subheader("Phân bố kênh đăng ký tổng hợp theo chuyên khoa đã chọn")

    channels_available = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care']
    channels_to_plot = [ch for ch in channels_available if any(f'Q{q}_{ch}' in data.columns for q in range(1, 5))]

    if not channels_to_plot:
        st.warning("Không tìm thấy dữ liệu theo kênh để hiển thị phân bố.")
        return

    fig_channel_dist = go.Figure()

    # Calculate total per channel for each selected specialty
    channel_totals_by_specialty = {}
    for spec in selected_specialties:
        spec_data = filtered_data[filtered_data['Chuyên khoa'] == spec].iloc[0] # Get the row for the specialty
        channel_totals_by_specialty[spec] = {}
        for channel in channels_to_plot:
            channel_total = 0
            for q in quarters_present:
                col_name = f'Q{q}_{channel}'
                if col_name in spec_data:
                    channel_total += spec_data[col_name]
            channel_totals_by_specialty[spec][channel] = channel_total

    # Add traces for each channel
    for channel in channels_to_plot:
        y_values = [channel_totals_by_specialty[spec].get(channel, 0) for spec in selected_specialties]
        fig_channel_dist.add_trace(go.Bar(
            x=selected_specialties,
            y=y_values,
            name=channel
        ))

    fig_channel_dist.update_layout(
        title='Phân bố kênh đăng ký tổng hợp theo chuyên khoa',
        xaxis_title='Chuyên khoa',
        yaxis_title='Tổng lượt đăng ký',
        barmode='stack', # Stack channels for each specialty
        height=500,
        template='plotly_white'
    )
    st.plotly_chart(fig_channel_dist, use_container_width=True)

# --- Load data and run analysis ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    specialty_comparison(data_loaded)
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem phân tích.")