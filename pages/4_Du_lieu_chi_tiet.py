# pages/4_Du_Lieu_Chi_Tiet.py
import streamlit as st
import pandas as pd
from datetime import datetime

# --- Configuration ---
EXPECTED_CHANNELS = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care', 'Grand Total']

st.set_page_config(page_title="Dữ liệu chi tiết", layout="wide")
st.title("📄 Dữ liệu chi tiết")

# --- Display Function ---
def data_details(data, start_date, end_date):
    """Display detailed data with filtering options based on selected date range using pivoted data."""

    # Filter data first based on the main date selection
    mask = (data.index.get_level_values('Month') >= start_date) & \
           (data.index.get_level_values('Month') <= end_date)
    # Important: Reset index here to make filtering by column easier later
    data_filtered_main = data[mask].reset_index()

    date_range_str = f"{start_date.strftime('%b %Y')} - {end_date.strftime('%b %Y')}"
    st.header(f"Xem và lọc dữ liệu ({date_range_str})")

    if data_filtered_main.empty:
        st.warning(f"Không có dữ liệu trong khoảng thời gian đã chọn ({date_range_str}).")
        return

    # Get available months and channels/specialties within the filtered data
    available_months_dt = sorted(data_filtered_main['Month'].unique())
    # Ensure Timestamps are converted back to datetime before formatting
    month_labels = [pd.to_datetime(m).strftime("%b %Y") for m in available_months_dt]
    available_channels = [ch for ch in EXPECTED_CHANNELS if ch in data_filtered_main.columns]
    available_specialties = sorted(data_filtered_main['Chuyên khoa'].unique())

    # --- Filtering Options ---
    filter_option = st.radio(
        "Chọn cách xem dữ liệu:",
        [f"Dữ liệu tổng hợp ({date_range_str})", "Lọc theo tháng cụ thể", "Lọc theo kênh cụ thể", "Lọc theo chuyên khoa cụ thể"],
        key='data_filter_option_page4',
        horizontal=True
    )

    st.markdown("---")

    # --- Display Data Based on Filter ---
    if filter_option == f"Dữ liệu tổng hợp ({date_range_str})":
        st.subheader(f"Hiển thị dữ liệu từ {date_range_str}")
        # Format Month column for better display in dataframe
        data_to_display = data_filtered_main.copy()
        data_to_display['Month'] = data_to_display['Month'].dt.strftime('%Y-%m')
        st.dataframe(data_to_display.sort_values(by=['Month', 'Chuyên khoa']))

    elif filter_option == "Lọc theo tháng cụ thể":
        if not available_months_dt:
             st.warning("Không có tháng nào trong khoảng thời gian đã chọn.")
             return

        month_selection_str = st.selectbox(
            "Chọn tháng cụ thể để xem:",
            options=month_labels,
            key='data_month_select_page4'
        )
        selected_month_dt = available_months_dt[month_labels.index(month_selection_str)]

        st.subheader(f"Dữ liệu chi tiết cho tháng {month_selection_str}")
        month_data_df = data_filtered_main[data_filtered_main['Month'] == selected_month_dt].copy()
        # Format Month column
        month_data_df['Month'] = month_data_df['Month'].dt.strftime('%Y-%m')
        st.dataframe(month_data_df.sort_values(by=['Chuyên khoa']))

    elif filter_option == "Lọc theo kênh cụ thể":
        if not available_channels:
             st.warning("Không tìm thấy kênh nào có dữ liệu trong khoảng thời gian đã chọn.")
             return

        channel_selection = st.selectbox(
            "Chọn kênh đăng ký để xem dữ liệu theo tháng:",
            options=available_channels,
            key='data_channel_select_page4'
        )

        st.subheader(f"Dữ liệu chi tiết cho kênh '{channel_selection}' ({date_range_str})")
        cols_to_show = ['Month', 'Chuyên khoa', channel_selection]
        channel_data_df = data_filtered_main[cols_to_show].copy()
        # Format Month column
        channel_data_df['Month'] = channel_data_df['Month'].dt.strftime('%Y-%m')
        st.dataframe(channel_data_df.sort_values(by=['Month', 'Chuyên khoa']))

    elif filter_option == "Lọc theo chuyên khoa cụ thể":
        if not available_specialties:
             st.warning("Không tìm thấy chuyên khoa nào trong khoảng thời gian đã chọn.")
             return

        specialty_selection = st.selectbox(
            "Chọn chuyên khoa để xem dữ liệu theo tháng:",
            options=available_specialties,
            key='data_specialty_select_page4'
        )
        st.subheader(f"Dữ liệu chi tiết cho chuyên khoa '{specialty_selection}' ({date_range_str})")
        spec_data_df = data_filtered_main[data_filtered_main['Chuyên khoa'] == specialty_selection].copy()
        # Format Month column
        spec_data_df['Month'] = spec_data_df['Month'].dt.strftime('%Y-%m')
        st.dataframe(spec_data_df.sort_values(by=['Month']))


# --- Load data and run ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    start_date = st.session_state.get('start_date')
    end_date = st.session_state.get('end_date')

    if start_date and end_date:
         # Pass the original loaded pivoted data (DataFrame) to the function
         data_details(data_loaded, start_date, end_date)
    else:
         st.warning("Vui lòng chọn khoảng thời gian phân tích ở thanh bên trái.")
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem dữ liệu chi tiết.")