import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq

st.set_page_config(
    page_title="Hệ thống Báo cáo Quản trị Thương mại Điện tử", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS phong cách Enterprise Dashboard
st.markdown("""
    <style>
    .stApp {
        background-color: #f4f5f7;
    }
    .kpi-card {
        background-color: #ffffff;
        border: 1px solid #dcdfe6;
        border-radius: 4px;
        padding: 14px 18px;
    }
    .kpi-label {
        font-size: 13px;
        color: #606266;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 6px;
    }
    .kpi-val {
        font-size: 24px;
        font-weight: 700;
        color: #1f2d3d;
    }
    </style>
""", unsafe_allow_html=True)

MOTHERDUCK_TOKEN = st.secrets.get("MOTHERDUCK_TOKEN", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

@st.cache_resource
def get_db_connection(token):
    return duckdb.connect(f"md:ecommerce_db?token={token}")

if not MOTHERDUCK_TOKEN:
    st.error("Cấu hình MOTHERDUCK_TOKEN chưa khả dụng trong Streamlit Secrets.")
    st.stop()

# Sidebar hệ thống
with st.sidebar:
    st.title("Báo cáo Quản trị BI")
    st.caption("Dự án Phân tích Dữ liệu DWH & ML")
    st.divider()
    
    st.markdown("**Trạng thái hệ thống:**")
    st.text(f"MotherDuck: Đã kết nối")
    st.text(f"Groq API: {'Đã kết nối' if GROQ_API_KEY else 'Chưa cấu hình'}")
    
    st.divider()
    st.caption("Phiên bản 2.1")

st.title("Dashboard Tổng quan Doanh số & Dự báo")
st.write("Hệ thống theo dõi chỉ số kinh doanh, dự báo doanh thu và phân tệp gợi ý sản phẩm.")

try:
    con = get_db_connection(MOTHERDUCK_TOKEN)
    
    sales_df = con.execute("SELECT sales_date, revenue FROM ecommerce_db.main_gold.fact_daily_sales ORDER BY sales_date").df()
    forecast_df = con.execute("SELECT forecast_date, predicted_revenue, revenue_lower_bound, revenue_upper_bound FROM ecommerce_db.main_gold.sales_forecast ORDER BY forecast_date").df()
    recs_df = con.execute("SELECT customer_id, recommended_product_id, rank, confidence_score FROM ecommerce_db.main_gold.user_recommendations LIMIT 100").df()

    sales_df['sales_date'] = pd.to_datetime(sales_df['sales_date'])
    forecast_df['forecast_date'] = pd.to_datetime(forecast_df['forecast_date'])

    tot_rev = sales_df['revenue'].sum()
    avg_rev = sales_df['revenue'].mean()
    fc_rev = forecast_df['predicted_revenue'].sum()
    tot_rec_cust = recs_df['customer_id'].nunique()

    # Thẻ KPI tổng quan
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Tổng doanh thu lịch sử</div><div class="kpi-val">${tot_rev:,.0f}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Doanh thu trung bình / ngày</div><div class="kpi-val">${avg_rev:,.0f}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Dự báo 30 ngày tiếp theo</div><div class="kpi-val">${fc_rev:,.0f}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="kpi-card"><div class="kpi-label">Khách hàng được gợi ý</div><div class="kpi-val">{tot_rec_cust:,}</div></div>', unsafe_allow_html=True)

    st.write("")

    # Phân tab chức năng
    t1, t2, t3 = st.tabs(["Doanh số & Dự báo", "Danh sách Gợi ý ALS", "Trợ lý Phân tích AI"])

    with t1:
        st.subheader("Biểu đồ Xu hướng Doanh thu Thực tế & Dự báo")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=sales_df['sales_date'], 
            y=sales_df['revenue'],
            mode='lines', 
            name='Doanh thu thực tế',
            line=dict(color='#1f77b4', width=1.8)
        ))

        fig.add_trace(go.Scatter(
            x=forecast_df['forecast_date'], 
            y=forecast_df['predicted_revenue'],
            mode='lines', 
            name='Dự báo (Prophet)',
            line=dict(color='#ff7f0e', width=1.8, dash='dash')
        ))

        if 'revenue_lower_bound' in forecast_df.columns and 'revenue_upper_bound' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([forecast_df['forecast_date'], forecast_df['forecast_date'][::-1]]),
                y=pd.concat([forecast_df['revenue_upper_bound'], forecast_df['revenue_lower_bound'][::-1]]),
                fill='toself',
                fillcolor='rgba(255, 127, 14, 0.12)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=False
            ))

        fig.update_layout(
            template="plotly_white",
            hovermode="x unified",
            xaxis_title="Thời gian",
            yaxis_title="Doanh thu ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=15, r=15, t=35, b=15),
            height=430
        )
        st.plotly_chart(fig, use_container_width=True)

    with t2:
        st.subheader("Bảng Kết quả Gợi ý Sản phẩm Cá nhân hóa")
        
        cust_filter = st.text_input("Lọc theo Mã khách hàng (Customer ID):", "")
        if cust_filter:
            res_df = recs_df[recs_df['customer_id'].astype(str).str.contains(cust_filter)]
            st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(recs_df, use_container_width=True, hide_index=True)

    with t3:
        st.subheader("Truy vấn Phân tích Kinh doanh (GenAI)")
        
        if not GROQ_API_KEY:
            st.warning("Vui lòng cấu hình GROQ_API_KEY trong Streamlit Secrets để truy cập tính năng này.")
        else:
            groq_client = Groq(api_key=GROQ_API_KEY)
            
            prompt_input = st.text_area(
                "Nội dung câu hỏi phân tích:",
                value="Dựa trên dữ liệu doanh thu gần đây và dự báo 30 ngày tới, hãy phân tích xu hướng và gợi ý các hành động vận hành cần thiết.",
                height=90
            )

            if st.button("Thực hiện phân tích"):
                recent_summary = sales_df.tail(30).describe().to_string()
                forecast_summary = forecast_df.head(10).to_string()
                
                full_prompt = f"""
                Bạn là chuyên gia phân tích dữ liệu kinh doanh thương mại điện tử.
                
                Thống kê doanh thu 30 ngày gần đây:
                {recent_summary}
                
                Dự báo doanh thu 10 ngày tới:
                {forecast_summary}
                
                Yêu cầu: {prompt_input}
                Hãy đưa ra nhận xét ngắn gọn, tập trung vào số liệu thực tế và đề xuất hành động ngắn gọn.
                """

                with st.spinner("Đang truy vấn mô hình LLM..."):
                    try:
                        response = groq_client.chat.completions.create(
                            messages=[{"role": "user", "content": full_prompt}],
                            model="openai/gpt-oss-120b"
                        )
                        st.markdown("---")
                        st.markdown(response.choices[0].message.content)
                    except Exception as ai_err:
                        st.error(f"Lỗi truy vấn Groq API: {ai_err}")

except Exception as e:
    st.error(f"Lỗi kết nối MotherDuck hoặc thực thi truy vấn: {e}")
