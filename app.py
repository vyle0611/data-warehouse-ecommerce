import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from groq import Groq

# 1. Cấu hình trang Dashboard
st.set_page_config(page_title="E-Commerce Executive Dashboard & GenBI", layout="wide")
st.title("E-Commerce Executive Dashboard & GenAI Insights")

# 2. Đọc Secrets từ Streamlit Cloud
MOTHERDUCK_TOKEN = st.secrets.get("MOTHERDUCK_TOKEN", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

@st.cache_resource
def get_db_connection(token):
    return duckdb.connect(f"md:ecommerce_db?token={token}")

if not MOTHERDUCK_TOKEN:
    st.warning("Vui lòng cấu hình MOTHERDUCK_TOKEN trong phần Settings > Secrets trên Streamlit Cloud!")
    st.stop()

try:
    con = get_db_connection(MOTHERDUCK_TOKEN)
    
    # 3. Tải dữ liệu từ tầng Gold (main_gold)
    sales_df = con.execute("SELECT sales_date, revenue FROM ecommerce_db.main_gold.fact_daily_sales ORDER BY sales_date").df()
    forecast_df = con.execute("SELECT forecast_date, predicted_revenue, revenue_lower_bound, revenue_upper_bound FROM ecommerce_db.main_gold.sales_forecast ORDER BY forecast_date").df()
    recs_df = con.execute("SELECT customer_id, recommended_product_id, rank, confidence_score FROM ecommerce_db.main_gold.user_recommendations LIMIT 100").df()

    # 4. Phân chia giao diện dạng Tab
    tab1, tab2, tab3 = st.tabs(["Doanh Thu & Dự Báo", "Gợi Ý Sản Phẩm (ALS)", "GenAI Assistant (Llama 3)"])

    with tab1:
        st.subheader("Doanh Thu Thực Tế (Historical Sales)")
        fig_sales = px.line(sales_df, x='sales_date', y='revenue', title="Biểu Đồ Doanh Thu Thực Tế")
        st.plotly_chart(fig_sales, use_container_width=True)

        st.subheader("Dự Báo Doanh Thu 30 Ngày Tới (Prophet)")
        fig_forecast = px.line(forecast_df, x='forecast_date', y='predicted_revenue', title="Biểu Đồ Dự Báo Doanh Thu")
        st.plotly_chart(fig_forecast, use_container_width=True)

    with tab2:
        st.subheader("Danh Sách Sản Phẩm Gợi Ý Cho Khách Hàng")
        st.dataframe(recs_df, use_container_width=True)

    with tab3:
        st.subheader("GenAI Assistant (Llama 3 Business Advisor)")
        if not GROQ_API_KEY:
            st.info("Vui lòng bổ sung GROQ_API_KEY vào Streamlit Secrets để dùng tính năng tư vấn AI.")
        else:
            groq_client = Groq(api_key=GROQ_API_KEY)
            user_query = st.text_input(
                "Hỏi AI về chiến lược kinh doanh:",
                value="Dựa trên dữ liệu doanh thu gần đây và dự báo 30 ngày tới, hãy phân tích xu hướng và gợi ý 3 mặt hàng cần nhập thêm (Restock) kèm lý do."
            )

            if st.button("Phân tích ngay"):
                recent_summary = sales_df.tail(30).describe().to_string()
                forecast_summary = forecast_df.head(10).to_string()
                
                prompt = f"""
                Bạn là một chuyên gia tư vấn chiến lược kinh doanh thương mại điện tử.
                
                Dữ liệu doanh thu 30 ngày gần đây:
                {recent_summary}
                
                Dữ liệu dự báo doanh thu 10 ngày tiếp theo:
                {forecast_summary}
                
                Yêu cầu của người dùng: {user_query}
                Hãy đưa ra nhận xét ngắn gọn, chuyên nghiệp và có tính ứng dụng cao.
                """

                with st.spinner("Llama 3 đang phân tích..."):
                    response = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="openai/gpt-oss-120b"  # Model mới đang được hỗ trợ chính thức trên Groq API
                    )
                    st.write("### Kết quả Phân tích:")
                    st.write(response.choices[0].message.content)

except Exception as e:
    st.error(f"Lỗi hệ thống hoặc truy vấn dữ liệu: {e}")
