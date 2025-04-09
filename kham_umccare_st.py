# kham_umccare_app.py
import streamlit as st
import pandas as pd
import numpy as np # Keep numpy import if needed by data processing

# Set page configuration (do this ONLY in the main script)
st.set_page_config(
    page_title="Phân tích lượt khám UMC",
    page_icon="🏥",
    layout="wide"
)

# --- Data Loading Function (Modified slightly for clarity) ---
@st.cache_data # Cache the data loading and processing
def load_process_umc_data(uploaded_file_obj):
    """Load and process the UMC Care data from an uploaded file object."""
    try:
        df_list = pd.read_excel(uploaded_file_obj, sheet_name=None)

        if not df_list:
            st.error("File Excel không chứa sheet nào.")
            return None

        # --- Attempt to intelligently parse different possible structures ---
        all_data = {}
        specialties = None
        processed_sheets = 0

        for sheet_name, raw_data in df_list.items():
            st.write(f"Đang xử lý sheet: {sheet_name}") # Debug info

            # Attempt 1: Structure with Quarterly Columns (like Q1_Bàn Khám)
            if 'Chuyên khoa' in raw_data.columns and any(col.startswith('Q') and '_' in col for col in raw_data.columns):
                st.info("Phát hiện cấu trúc dữ liệu theo quý trong một sheet.")
                if specialties is None:
                    specialties = raw_data['Chuyên khoa'].tolist()
                    for spec in specialties:
                        all_data[spec] = {} # Initialize dict for each specialty

                for idx, row in raw_data.iterrows():
                    spec = row['Chuyên khoa']
                    if spec in all_data:
                        for col in raw_data.columns:
                            if col != 'Chuyên khoa':
                                all_data[spec][col] = row[col]
                processed_sheets += 1
                # Assume if one sheet has this structure, it contains all data
                break # Stop processing other sheets if this format is found


            # Attempt 2: Structure with one sheet per Quarter/Time Period
            elif 'Chuyên khoa' in raw_data.columns and raw_data.shape[1] >= 6:
                 st.info(f"Phát hiện cấu trúc theo kênh trong sheet '{sheet_name}'.")
                 # Assume standard channel names if structure seems right
                 expected_channels = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care', 'Grand Total']
                 current_cols = raw_data.columns.tolist()
                 # Use first 6 columns if names don't match exactly
                 cols_map = {current_cols[i]: expected_channels[i-1] for i in range(1, min(6, len(current_cols)))}

                 if specialties is None:
                     specialties = raw_data['Chuyên khoa'].tolist()
                     for spec in specialties:
                         all_data[spec] = {} # Initialize

                 # Try to determine quarter (e.g., from sheet name or order)
                 quarter_num = processed_sheets + 1 # Simple ordering
                 # You might need more robust logic based on sheet_name if possible

                 if quarter_num > 4: continue # Limit to 4 quarters

                 for idx, row in raw_data.iterrows():
                    spec = row['Chuyên khoa']
                    if spec in all_data:
                        for i in range(1, min(6, len(current_cols))):
                             original_col_name = current_cols[i]
                             channel_name = cols_map.get(original_col_name, f"Kênh_{i}") # Fallback name
                             data_key = f'Q{quarter_num}_{channel_name}'
                             all_data[spec][data_key] = row[original_col_name]
                 processed_sheets += 1


            else:
                st.warning(f"Sheet '{sheet_name}' không có cấu trúc được nhận dạng. Bỏ qua.")

        # --- Assemble Final DataFrame ---
        if not all_data or specialties is None:
             st.error("Không thể xử lý dữ liệu từ file. Không tìm thấy chuyên khoa hoặc dữ liệu phù hợp.")
             return None

        final_data_list = []
        all_expected_cols = set()
        for q in range(1, 5):
            for ch in ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care', 'Grand Total']:
                all_expected_cols.add(f"Q{q}_{ch}")

        for spec in specialties:
            row_data = {'Chuyên khoa': spec}
            row_data.update(all_data.get(spec, {}))
            # Ensure all expected quarter_channel columns exist, fill with 0 if missing
            for col in all_expected_cols:
                if col not in row_data:
                    row_data[col] = 0
            final_data_list.append(row_data)

        final_df = pd.DataFrame(final_data_list)

        # Ensure numeric types and handle NaNs
        for col in final_df.columns:
            if col != 'Chuyên khoa':
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)


        # Recalculate Grand Total per Quarter if necessary
        for q in range(1, 5):
            channels_for_total = [f'Q{q}_{ch}' for ch in ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care'] if f'Q{q}_{ch}' in final_df.columns]
            if channels_for_total: # Only calculate if component columns exist
                 final_df[f'Q{q}_Grand Total'] = final_df[channels_for_total].sum(axis=1)


        # Calculate overall total for sorting/analysis
        total_cols = [f'Q{q}_Grand Total' for q in range(1, 5) if f'Q{q}_Grand Total' in final_df.columns]
        if total_cols:
            final_df['Total_Registrations'] = final_df[total_cols].sum(axis=1)
        else:
            final_df['Total_Registrations'] = 0 # Fallback if no Grand Total columns found


        st.success("Đã xử lý dữ liệu thành công!")
        return final_df

    except Exception as e:
        st.error(f"Lỗi khi đọc hoặc xử lý file Excel: {e}")
        import traceback
        st.error(traceback.format_exc()) # More detailed error for debugging
        return None

# --- Sidebar for File Upload ---
st.sidebar.title("Tải Dữ Liệu")
uploaded_file = st.sidebar.file_uploader("Tải lên file Excel UMC Care", type=["xlsx", "xls"])

# --- Load and Store Data in Session State ---
# Initialize session state if it doesn't exist
if 'umc_data' not in st.session_state:
    st.session_state['umc_data'] = None

if uploaded_file is not None:
    # Process the newly uploaded file and update session state
    data = load_process_umc_data(uploaded_file)
    st.session_state['umc_data'] = data
    # Optional: Clear the uploader after processing if desired
    # st.sidebar.empty() # Might cause issues if user wants to re-upload easily
elif st.session_state['umc_data'] is None:
    # If no file uploaded AND no data in session state, maybe show sample or prompt
    st.info("Vui lòng tải lên file dữ liệu UMC Care qua thanh bên trái để bắt đầu phân tích.")
    # Optionally load sample data here if needed for initial view
    # st.session_state['umc_data'] = load_sample_data_function() # Define this if needed

# --- Main Page Content ---
st.title("🏥 Phân tích dữ liệu lượt khám UMC Care")

st.markdown("""
Chào mừng bạn đến với ứng dụng phân tích dữ liệu lượt đăng ký khám bệnh tại UMC Care.

Sử dụng thanh bên trái để tải lên file dữ liệu của bạn (định dạng Excel).
Sau đó, chọn các trang phân tích khác nhau từ thanh điều hướng bên trái.

**Các trang bao gồm:**
*   **Tổng quan:** Các chỉ số chính và xu hướng chung.
*   **Phân tích kênh đăng ký:** Phân bố và xu hướng theo từng kênh (Bàn khám, PKH, Tổng đài, UMC Care).
*   **So sánh chuyên khoa:** So sánh lượt đăng ký giữa các chuyên khoa khác nhau.
*   **Dữ liệu chi tiết:** Xem bảng dữ liệu gốc hoặc lọc theo quý/kênh.
""")

if st.session_state['umc_data'] is not None:
    st.success("Dữ liệu đã sẵn sàng. Chọn một trang từ thanh bên để xem phân tích.")
    st.dataframe(st.session_state['umc_data'].head())
else:
     st.warning("Chưa có dữ liệu để hiển thị. Vui lòng tải file lên.")

# Add navigation hint
st.sidebar.success("Chọn một trang phân tích ở trên.")

# --- End of Main App Script ---