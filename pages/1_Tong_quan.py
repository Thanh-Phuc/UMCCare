# pages/1_Tong_Quan.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Tổng quan", layout="wide") # Optional: Can set page specific config

st.title("📊 Tổng quan dữ liệu đăng ký")

# --- Function from original script ---
def overview_analysis(data):
    """Perform overview analysis of the data"""
    st.header("Tổng quan dữ liệu đăng ký")

    # Create columns for metrics
    col1, col2, col3, col4 = st.columns(4)

    # Calculate total registrations by quarter, handling missing columns
    q_totals = {}
    total_registrations = 0
    for q in range(1, 5):
        col_name = f'Q{q}_Grand Total'
        q_totals[q] = data[col_name].sum() if col_name in data.columns else 0
        total_registrations += q_totals[q]

    # Display metrics
    with col1:
        st.metric("Tổng lượt đăng ký", f"{total_registrations:,.0f}")

    with col2:
        q3_total = q_totals.get(3, 0)
        q4_total = q_totals.get(4, 0)
        delta_q4_q3 = q4_total - q3_total
        if q3_total > 0:
            q4_vs_q3 = (delta_q4_q3 / q3_total) * 100
            st.metric("Q4 vs Q3", f"{q4_vs_q3:.1f}%", delta=f"{delta_q4_q3:,.0f}")
        else:
             st.metric("Q4 vs Q3", "N/A", delta=f"{delta_q4_q3:,.0f}") # Handle division by zero


    with col3:
        # Top channel across all quarters
        channels = ['Bàn Khám', 'PKH', 'Tổng đài', 'UMC Care']
        channel_totals = {}
        total_channel_regs = 0
        for channel in channels:
            channel_sum = 0
            for q in range(1, 5):
                 col_name = f'Q{q}_{channel}'
                 if col_name in data.columns:
                     channel_sum += data[col_name].sum()
            channel_totals[channel] = channel_sum
            total_channel_regs += channel_sum

        if total_channel_regs > 0:
            top_channel = max(channel_totals, key=channel_totals.get)
            top_channel_pct = (channel_totals[top_channel] / total_channel_regs) * 100
            st.metric("Kênh đăng ký hàng đầu", top_channel, f"{top_channel_pct:.1f}%")
        else:
            st.metric("Kênh đăng ký hàng đầu", "N/A", "0.0%")


    with col4:
        # Top specialty across all quarters (using pre-calculated 'Total_Registrations')
        if 'Total_Registrations' in data.columns and total_registrations > 0 and not data.empty:
            top_specialty_row = data.loc[data['Total_Registrations'].idxmax()]
            top_specialty = top_specialty_row['Chuyên khoa']
            top_specialty_total = top_specialty_row['Total_Registrations']
            top_specialty_pct = (top_specialty_total / total_registrations) * 100
            st.metric("Chuyên khoa hàng đầu", top_specialty, f"{top_specialty_pct:.1f}%")
        else:
            st.metric("Chuyên khoa hàng đầu", "N/A", "0.0%")

    # Create quarterly trend chart
    st.subheader("Xu hướng đăng ký theo quý")

    quarterly_data_list = []
    for q in range(1, 5):
        q_data = {'Quý': f'Q{q}'}
        q_data['Tổng lượt đăng ký'] = q_totals.get(q, 0)
        for channel in channels:
            col_name = f'Q{q}_{channel}'
            q_data[channel] = data[col_name].sum() if col_name in data.columns else 0
        quarterly_data_list.append(q_data)

    quarterly_df = pd.DataFrame(quarterly_data_list)

    # Plot
    fig_trend = go.Figure()

    # Add total line
    fig_trend.add_trace(go.Scatter(
        x=quarterly_df['Quý'],
        y=quarterly_df['Tổng lượt đăng ký'],
        mode='lines+markers',
        name='Tổng lượt đăng ký',
        line=dict(width=3, color='black'),
        marker=dict(size=10)
    ))

    # Add channel bars
    for channel in channels:
        fig_trend.add_trace(go.Bar(
            x=quarterly_df['Quý'],
            y=quarterly_df[channel],
            name=channel
        ))

    fig_trend.update_layout(
        title='Xu hướng đăng ký theo quý',
        xaxis_title='Quý',
        yaxis_title='Lượt đăng ký',
        barmode='stack',
        height=500,
        template='plotly_white'
    )

    st.plotly_chart(fig_trend, use_container_width=True)

    # Top 10 specialties by total registrations
    st.subheader("Top 10 chuyên khoa có lượt đăng ký cao nhất")

    if 'Total_Registrations' in data.columns and not data.empty:
        # Sort and get top 10
        top10_specialties = data.sort_values('Total_Registrations', ascending=False).head(10)

        # Create a horizontal bar chart
        fig_top10 = px.bar(
            top10_specialties,
            x='Total_Registrations',
            y='Chuyên khoa',
            orientation='h',
            color='Total_Registrations',
            color_continuous_scale='Viridis',
            labels={'Total_Registrations': 'Tổng lượt đăng ký', 'Chuyên khoa': 'Chuyên khoa'},
            text='Total_Registrations' # Show values on bars
        )
        fig_top10.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_top10.update_layout(
            title='Top 10 chuyên khoa có lượt đăng ký cao nhất',
            height=500,
            yaxis=dict(autorange="reversed"), # Keep highest at top
            xaxis_title='Tổng lượt đăng ký',
            yaxis_title='Chuyên khoa',
            template='plotly_white'
        )
        st.plotly_chart(fig_top10, use_container_width=True)
    else:
        st.info("Không có dữ liệu 'Total_Registrations' để hiển thị Top 10.")

# --- Load data and run analysis ---
if 'umc_data' in st.session_state and st.session_state['umc_data'] is not None:
    data_loaded = st.session_state['umc_data']
    overview_analysis(data_loaded)
else:
    st.warning("Vui lòng tải lên file dữ liệu ở trang chính để xem phân tích.")