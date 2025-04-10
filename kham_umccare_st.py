# kham_umccare_app.py
import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime, date # Import the date object
import re

# Set page configuration (do this ONLY in the main script)
st.set_page_config(
    page_title="Phân tích lượt khám UMC",
    page_icon="🏥",
    layout="wide"
)

# --- Configuration ---
MAX_MONTHS = 12
EXPECTED_CHANNELS = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care']
EXCLUDE_SPECIALTY_TERMS = ['grand total', 'tổng cộng', 'total']

# --- Helper Function to Parse Sheet Names ---
# ...(No changes needed here)...
def parse_sheet_name_to_date(sheet_name):
    """Attempts to parse common month/year formats from sheet names."""
    sheet_name_lower = str(sheet_name).lower().strip()
    formats_to_try = [
        "%b-%y", "%b %y", "%B-%y", "%B %y", "%b-%Y", "%b %Y", "%B-%Y", "%B %Y",
        "T%m-%y", "T%m_%y", "T%m-%Y", "T%m_%Y", "thang%m_%y", "thang%m-%y",
        "thang%m_%Y", "thang%m-%Y", "%m/%Y", "%m-%Y", "%Y/%m", "%Y-%m"
    ]
    cleaned_name = re.sub(r'^(sheet|data|thang|t)(\s*|-|_)?', '', sheet_name_lower)
    for fmt in formats_to_try:
        try:
            # Return as Timestamp initially, convert later if needed
            return pd.to_datetime(cleaned_name, format=fmt).replace(day=1)
        except ValueError:
            continue
    # st.warning(f"Không thể tự động nhận dạng tháng/năm từ tên sheet: '{sheet_name}'. Bỏ qua sheet này.") # Reduce noise
    return None

# --- Data Loading Function ---
# ...(No changes needed in the core logic, just ensure it returns Timestamps or None)...
@st.cache_data(ttl=3600)
def load_process_umc_data_monthly(uploaded_file_obj):
    """Loads data assuming each sheet is a month, EXCLUDING 'Grand Total' specialty rows."""
    st.info("Đang đọc file Excel...")
    try:
        df_sheets = pd.read_excel(uploaded_file_obj, sheet_name=None)
        if not df_sheets:
            st.error("File Excel không chứa sheet nào.")
            return None

        all_monthly_data = []
        valid_sheets_found = 0
        parsed_sheet_names = [] # Keep track to avoid duplicate warnings

        for sheet_name, raw_data in df_sheets.items():
            month_date = parse_sheet_name_to_date(sheet_name)
            if month_date is None:
                if sheet_name not in parsed_sheet_names: # Show warning only once per name
                    st.warning(f"Bỏ qua sheet '{sheet_name}' do không nhận dạng được ngày tháng.")
                    parsed_sheet_names.append(sheet_name)
                continue

            if 'Chuyên khoa' not in raw_data.columns:
                st.warning(f"Sheet '{sheet_name}' ({month_date.strftime('%b %Y')}) thiếu cột 'Chuyên khoa'. Bỏ qua.")
                continue

            # Exclude Grand Total / Summary Rows
            raw_data['Chuyên khoa'] = raw_data['Chuyên khoa'].astype(str)
            mask_keep = ~raw_data['Chuyên khoa'].str.lower().str.strip().isin(EXCLUDE_SPECIALTY_TERMS)
            data_cleaned = raw_data[mask_keep].copy()
            # num_excluded = len(raw_data) - len(data_cleaned) # Reduce verbose output
            # if num_excluded > 0:
            #      st.write(f"Sheet '{sheet_name}': Đã loại bỏ {num_excluded} dòng tổng cộng.")
            if data_cleaned.empty:
                 st.warning(f"Sheet '{sheet_name}' ({month_date.strftime('%b %Y')}) không còn dữ liệu sau khi loại bỏ dòng tổng cộng. Bỏ qua.")
                 continue

            present_channels = [ch for ch in EXPECTED_CHANNELS if ch in data_cleaned.columns]
            # Don't skip if channels are missing, just process what's there + Grand Total later

            cols_to_keep = ['Chuyên khoa'] + present_channels
            # Handle potential missing channel columns gracefully when selecting
            cols_to_keep = [col for col in cols_to_keep if col in data_cleaned.columns]
            monthly_df = data_cleaned[cols_to_keep].copy()
            monthly_df['Month'] = month_date

            # Process present channels
            for channel in present_channels: # Only loop through channels actually found
                monthly_df[channel] = pd.to_numeric(monthly_df[channel], errors='coerce').fillna(0).astype(int)

            # Add/Recalculate Grand Total column
            if present_channels: # Only calculate if there were any channels found
                 monthly_df['Grand Total'] = monthly_df[present_channels].sum(axis=1)
            else:
                 monthly_df['Grand Total'] = 0 # Assign 0 if no standard channels were found

            all_monthly_data.append(monthly_df)
            valid_sheets_found += 1

        if not all_monthly_data:
            st.error("Không tìm thấy sheet hợp lệ nào chứa dữ liệu chuyên khoa (sau khi loại bỏ dòng tổng cộng).")
            return None

        combined_df = pd.concat(all_monthly_data, ignore_index=True)

        # --- Pivot ---
        pivot_values = [ch for ch in EXPECTED_CHANNELS if ch in combined_df.columns] + ['Grand Total']
        pivot_values = list(set(col for col in pivot_values if col in combined_df.columns)) # Ensure unique and present values

        try:
             # Check for duplicates before pivoting
             duplicates = combined_df[combined_df.duplicated(subset=['Month', 'Chuyên khoa'], keep=False)]
             if not duplicates.empty:
                 st.warning("Phát hiện dữ liệu chuyên khoa trùng lặp trong cùng một tháng. Sẽ cộng gộp giá trị.")
                 # st.dataframe(duplicates.sort_values(by=['Month', 'Chuyên khoa'])) # Optional: show duplicates

             pivoted_df = combined_df.pivot_table(
                 index=['Month', 'Chuyên khoa'],
                 values=pivot_values,
                 fill_value=0,
                 aggfunc='sum' # Use sum to handle potential duplicates
             )
        except Exception as pivot_error:
             st.error(f"Lỗi khi tổng hợp dữ liệu: {pivot_error}")
             return None

        pivoted_df = pivoted_df.sort_index()

        # Calculate overall total
        if 'Grand Total' in pivoted_df.columns:
             pivoted_df['Total_Registrations_AllM'] = pivoted_df.groupby(level='Chuyên khoa')['Grand Total'].transform('sum')
        else:
             channel_sum_cols = [ch for ch in EXPECTED_CHANNELS if ch in pivoted_df.columns]
             if channel_sum_cols:
                  pivoted_df['Temp_Total'] = pivoted_df[channel_sum_cols].sum(axis=1)
                  pivoted_df['Total_Registrations_AllM'] = pivoted_df.groupby(level='Chuyên khoa')['Temp_Total'].transform('sum')
                  if 'Temp_Total' in pivoted_df.columns: del pivoted_df['Temp_Total']
             else:
                  pivoted_df['Total_Registrations_AllM'] = 0

        st.success(f"Đã xử lý thành công dữ liệu từ {valid_sheets_found} sheet.")
        return pivoted_df

    except Exception as e:
        st.error(f"Lỗi khi đọc hoặc xử lý file Excel: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

# --- Sidebar ---
st.sidebar.title("Tải & Cấu hình")
uploaded_file = st.sidebar.file_uploader("Tải lên file Excel UMC Care (Sheet theo Tháng)", type=["xlsx", "xls"])

# Initialize session state
if 'umc_data' not in st.session_state: st.session_state['umc_data'] = None
if 'start_date' not in st.session_state: st.session_state['start_date'] = None
if 'end_date' not in st.session_state: st.session_state['end_date'] = None
if 'min_date' not in st.session_state: st.session_state['min_date'] = None
if 'max_date' not in st.session_state: st.session_state['max_date'] = None

# Load and Store Data in Session State
if uploaded_file is not None:
    data = load_process_umc_data_monthly(uploaded_file) # Use the updated function
    st.session_state['umc_data'] = data
    # Reset dates when new file is uploaded
    if data is not None and not data.empty:
        # Store min/max as Timestamp initially
        min_ts = data.index.get_level_values('Month').min()
        max_ts = data.index.get_level_values('Month').max()
        st.session_state['min_date'] = min_ts
        st.session_state['max_date'] = max_ts
        # Default selection to the full range
        st.session_state['start_date'] = min_ts
        st.session_state['end_date'] = max_ts
    else:
        st.session_state['min_date'] = None
        st.session_state['max_date'] = None
        st.session_state['start_date'] = None
        st.session_state['end_date'] = None
    # Clear uploader buffer maybe? Helps avoid re-processing same file on rerun
    # uploaded_file.seek(0) # Reset buffer - might be needed sometimes


# --- Date Range Selector - WITH FIX ---
if st.session_state['umc_data'] is not None and not st.session_state['umc_data'].empty:
    # Retrieve Timestamps from session state
    min_ts = st.session_state.get('min_date')
    max_ts = st.session_state.get('max_date')
    start_ts = st.session_state.get('start_date')
    end_ts = st.session_state.get('end_date')

    # Convert Timestamps to datetime.date objects for the widget
    min_dt = min_ts.date() if min_ts else date.today() # Provide default if None
    max_dt = max_ts.date() if max_ts else date.today()
    start_dt_val = start_ts.date() if start_ts else min_dt
    end_dt_val = end_ts.date() if end_ts else max_dt

    st.sidebar.markdown("---")
    st.sidebar.subheader("Chọn Khoảng Thời Gian Phân Tích")
    selected_start_date_obj = st.sidebar.date_input( # Returns a datetime.date object
        "Từ tháng", # Changed label slightly
        value=start_dt_val,
        min_value=min_dt,      # PASS datetime.date object
        max_value=max_dt,      # PASS datetime.date object
        key='date_start',
        format="YYYY/MM/DD"    # Use Streamlit's format (displays month/year well usually)
    )

    selected_end_date_obj = st.sidebar.date_input( # Returns a datetime.date object
        "Đến tháng", # Changed label slightly
        value=end_dt_val,
        min_value=min_dt,      # PASS datetime.date object
        max_value=max_dt,      # PASS datetime.date object
        key='date_end',
        format="YYYY/MM/DD"    # Use Streamlit's format
    )

    # --- Validation and State Update ---
    # Ensure end date is not before start date
    if selected_end_date_obj < selected_start_date_obj:
        st.sidebar.warning("Ngày kết thúc không thể trước ngày bắt đầu.")
        # Don't automatically adjust here, let user fix it, but prevent state update with invalid range
        valid_range = False
    else:
        valid_range = True

    # Convert selected date objects back to first-of-month Timestamps for filtering consistency
    new_start_ts = pd.to_datetime(selected_start_date_obj).replace(day=1)
    new_end_ts = pd.to_datetime(selected_end_date_obj).replace(day=1)

    # Check if the state needs updating (compare Timestamps)
    update_needed = False
    if valid_range:
        if st.session_state.get('start_date') != new_start_ts:
            st.session_state['start_date'] = new_start_ts
            update_needed = True
        if st.session_state.get('end_date') != new_end_ts:
            st.session_state['end_date'] = new_end_ts
            update_needed = True

    # Rerun if state was updated
    if update_needed:
         st.experimental_rerun()

else:
    st.sidebar.info("Tải file dữ liệu lên để chọn khoảng thời gian.")


# --- Main Page Content ---
# ...(Same as previous version)...
st.title("🏥 Phân tích dữ liệu lượt khám UMC Care (Theo Tháng)")
st.markdown("""
Chào mừng bạn đến với ứng dụng phân tích dữ liệu lượt đăng ký khám bệnh tại UMC Care.

1.  Sử dụng thanh bên trái để **tải lên file dữ liệu** của bạn (Excel, mỗi sheet là một tháng, cột là kênh).
2.  Sử dụng bộ chọn ngày bên trái để **chọn khoảng thời gian** bạn muốn phân tích.
3.  Chọn các trang phân tích (`Tổng quan`, `Kênh Đăng Ký`,...) từ thanh điều hướng bên trái.
""")

if st.session_state['umc_data'] is not None:
    start_dt_display = st.session_state.get('start_date')
    end_dt_display = st.session_state.get('end_date')
    if start_dt_display and end_dt_display:
         st.success(f"Dữ liệu đã sẵn sàng. Phân tích từ {start_dt_display.strftime('%b %Y')} đến {end_dt_display.strftime('%b %Y')}. Chọn một trang từ thanh bên.")
         st.dataframe(st.session_state['umc_data'].head())
    else:
         st.error("Không thể xác định khoảng thời gian từ dữ liệu đã tải.")
else:
     st.warning("Chưa có dữ liệu để hiển thị. Vui lòng tải file lên.")

st.sidebar.success("Chọn một trang phân tích ở trên.")