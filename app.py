import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
from groq import Groq

st.set_page_config(page_title="E-Commerce Analytics & GenBI", layout="wide")
st.title("👗 E-Commerce Executive Dashboard & GenAI Insights")

# 1. Kết nối MotherDuck & Groq API
MOTHERDUCK_TOKEN = st.secrets.get("MOTHERDUCK_TOKEN", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

@st.cache_resource
def get_db_connection():
    return duckdb.connect(f"md:ecommerce_db?token={MOTHERDUCK_TOKEN}")

if MOTHERDUCK_TOKEN:
    con = duckdb.connect(f"md:eccomerce_db?token={MOTHERDUCK_TOKEN}")
    
    # 2. Query dữ liệu Doanh thu tầng Bronze/Gold
    try:
        sales_df = con.execute("SELECT * FROM bronze.sales ORDER BY Date").df()
        
        st.subheader("📈 Doanh thu Thực tế (Historical Sales 2012-2022)")
        fig = px.line(sales_df, x='Date', y='Revenue', title="Biểu đồ Doanh thu Theo Ngày")
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. Tích hợp GenBI Assistant (Groq Cloud API với Llama 3)
        if GROQ_API_KEY:
            st.subheader("🤖 GenAI Assistant (Llama 3 Business Advisor)")
            groq_client = Groq(api_key=GROQ_API_KEY)
            
            user_query = st.text_input("Hỏi AI về chiến lược kinh doanh:", 
                                      "Dựa trên dữ liệu doanh thu gần nhất, hãy phân tích xu hướng và gợi ý 3 hành động kinh doanh.")
            
            if st.button("Phân tích ngay"):
                recent_summary = sales_df.tail(30).describe().to_string()
                prompt = f"Dữ liệu 30 ngày gần đây:\n{recent_summary}\n\nYêu cầu: {user_query}"
                
                with st.spinner("Llama 3 đang phân tích..."):
                    response = groq_client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="llama3-8b-8192"
                    )
                    st.write("### Kết quả Phân tích:")
                    st.write(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Lỗi truy vấn dữ liệu: {e}")
else:
    st.warning("Vui lòng cấu hình MOTHERDUCK_TOKEN trong Streamlit Secrets!")
