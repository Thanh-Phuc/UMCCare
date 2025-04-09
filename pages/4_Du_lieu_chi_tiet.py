# pages/4_Du_Lieu_Chi_Tiet.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dữ liệu chi tiết", layout="wide")

st.title("📄 Dữ liệu chi tiết")

# --- Function from original script ---
def data_details(data):
    """Display detailed data"""
    st.header("Xem và lọc dữ liệu")

    # Allow user to select which data to view
    view_option = st.radio(
        "Chọn cách xem dữ liệu:",
        ["Dữ liệu tổng hợp đầy đủ", "Lọc theo quý", "Lọc theo kênh"],
        key='data_view_option'
    )

    if view_option == "Dữ liệu tổng hợp đầy đủ":
        st.dataframe(data)

    elif view_option == "Lọc theo quý":
        quarters_present = [f"Q{q}" for q in range(1, 5) if f'Q{q}_Grand Total' in data.columns]
        if not quarters_present:
            st.warning("Không tìm thấy dữ liệu theo quý.")
            return

        quarter_selection = st.selectbox("Chọn quý:", quarters_present, key='data_quarter_select')
        q_num = int(quarter_selection[1])

        # Filter columns for the selected quarter
        quarter_cols = ['Chuyên khoa'] + [col for col in data.columns if col.startswith(f'Q{q_num}_')]
        st.dataframe(data[quarter_cols])

    else:  # Lọc theo kênh
        channels_available = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care', 'Grand Total']
        channels_present = [ch for ch in channels_available if any(f'Q{q}_{ch}' in data.columns for q in range(1, 5))]
        if not channels_present:
            st.warning("Không tìm thấy dữ liệu theo kênh.")
            return

        channel_selection = st.selectbox("Chọn kênh đăng ký:", channels_present, key='data_channel_select')

        # Filter columns for the selected channel across all quarters
        channel_cols = ['Chuyên khoa'] + [f'Q{q}_{channel_selection}' for q in range(1,5) if f'Q{q}_{channel_selection}' in data.columns]
        # Optionally add a total column for the channel if desired
        # data[f'{channel_selection}_Total'] = data[channel_cols[1:]].sum(axis=1)
        # channel_cols.append(f'{channel_selection}_Total')

        st.dataframe(data[channel_cols])

# --- Load data and run analysis ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    data_details(data_loaded)
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem dữ liệu chi tiết.")