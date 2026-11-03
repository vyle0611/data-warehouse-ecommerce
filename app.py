import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq

st.set_page_config(
    page_title="E-Commerce Executive Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #fafafa;
    }
    .kpi-box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 4px;
        padding: 12px 16px;
        text-align: left;
    }
    .kpi-title {
        font-size: 12px;
        color: #616161;
        text-transform: uppercase;
        font-weight: 600;
    }
    .kpi-value {
        font-size: 22px;
        font-weight: 700;
        color: #212121;
        margin-top: 4px;
    }
    </style>
""", unsafe_allow_html=True)

MOTHERDUCK_TOKEN = st.secrets.get("MOTHERDUCK_TOKEN", "")
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

@st.cache_resource
def get_db_connection(token):
    return duckdb.connect(f"md:ecommerce_db?token={token}")

if not MOTHERDUCK_TOKEN:
    st.error("Thieu MOTHERDUCK_TOKEN trong Streamlit Secrets.")
    st.stop()

with st.sidebar:
    st.title("He thong BI")
    st.write("Do an Data Warehouse & Analytics")
    st.divider()
    st.subheader("Ket noi")
    st.write("MotherDuck: Connected")
    st.write("Groq AI: " + ("Connected" if GROQ_API_KEY else "Missing Token"))
    st.divider()
    st.caption("Version 2.0")

st.title("E-Commerce Executive Dashboard & GenAI Insights")
st.write("Phan tich diem gay tang truong, du bao doanh thu va goi y khach hang.")

try:
    con = get_db_connection(MOTHERDUCK_TOKEN)
    
    sales_df = con.execute("SELECT sales_date, revenue FROM ecommerce_db.main_gold.fact_daily_sales ORDER BY sales_date").df()
    forecast_df = con.execute("SELECT forecast_date, predicted_revenue, revenue_lower_bound, revenue_upper_bound FROM ecommerce_db.main_gold.sales_forecast ORDER BY forecast_date").df()
    recs_df = con.execute("SELECT customer_id, recommended_product_id, rank, confidence_score FROM ecommerce_db.main_gold.user_recommendations LIMIT 100").df()

    sales_df['sales_date'] = pd.to_datetime(sales_df['sales_date'])
    forecast_df['forecast_date'] = pd.to_datetime(forecast_df['forecast_date'])

    total_revenue = sales_df['revenue'].sum()
    avg_daily_rev = sales_df['revenue'].mean()
    forecast_30d_rev = forecast_df['predicted_revenue'].sum()
    total_recs = len(recs_df)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Tong Doanh Thu Lich Su</div><div class="kpi-value">${total_revenue:,.0f}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Doanh Thu TB / Ngay</div><div class="kpi-value">${avg_daily_rev:,.0f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">Du Bao 30 Ngay Toi</div><div class="kpi-value">${forecast_30d_rev:,.0f}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-box"><div class="kpi-title">So Luong Khach Hang ALS</div><div class="kpi-value">{total_recs:,}</div></div>', unsafe_allow_html=True)

    st.write("")

    tab1, tab2, tab3 = st.tabs(["Doanh Thu & Du Bao", "Goi Y San Pham (ALS)", "GenAI Assistant"])

    with tab1:
        st.subheader("Doanh thu thuc te va Du bao Prophet")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=sales_df['sales_date'], 
            y=sales_df['revenue'],
            mode='lines', 
            name='Actual Revenue',
            line=dict(color='#29b6f6', width=1.5)
        ))

        fig.add_trace(go.Scatter(
            x=forecast_df['forecast_date'], 
            y=forecast_df['predicted_revenue'],
            mode='lines', 
            name='Forecast',
            line=dict(color='#ab47bc', width=1.5, dash='dash')
        ))

        if 'revenue_lower_bound' in forecast_df.columns and 'revenue_upper_bound' in forecast_df.columns:
            fig.add_trace(go.Scatter(
                x=pd.concat([forecast_df['forecast_date'], forecast_df['forecast_date'][::-1]]),
                y=pd.concat([forecast_df['revenue_upper_bound'], forecast_df['revenue_lower_bound'][::-1]]),
                fill='toself',
                fillcolor='rgba(171, 71, 188, 0.1)',
                line=dict(color='rgba(255,255,255,0)'),
                hoverinfo="skip",
                showlegend=False
            ))

        fig.update_layout(
            template="plotly_white",
            hovermode="x unified",
            xaxis_title="Date",
            yaxis_title="Revenue ($)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=30, b=10),
            height=420
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Danh sach goi y san pham cho khach hang (ALS Model)")
        
        search_cust = st.text_input("Filter theo Customer ID:", "")
        if search_cust:
            filtered_recs = recs_df[recs_df['customer_id'].astype(str).str.contains(search_cust)]
            st.dataframe(filtered_recs, use_container_width=True, hide_index=True)
        else:
            st.dataframe(recs_df, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("GenAI Business Advisor")
        
        if not GROQ_API_KEY:
            st.info("Chua co GROQ_API_KEY trong Streamlit Secrets.")
        else:
            groq_client = Groq(api_key=GROQ_API_KEY)
            
            user_query = st.text_area(
                "Yeu cau phan tich:",
                value="Dua tren du lieu doanh thu gan day va du bao 30 ngay toi, hay phan tich xu huong va goi y 3 mat hang me can nhap them (Restock) kem ly do.",
                height=90
            )

            if st.button("Chay phan tich"):
                recent_summary = sales_df.tail(30).describe().to_string()
                forecast_summary = forecast_df.head(10).to_string()
                
                prompt = f"""
                Ban la mot chuyên gia phan tich du lieu va chien luoc kinh doanh.
                
                Du lieu doanh thu 30 ngay gan nhat:
                {recent_summary}
                
                Du lieu du bao 10 ngay toi:
                {forecast_summary}
                
                Yeu cau: {user_query}
                Dua ra nhan xet ngan gon, vao thong so chinh, khong giai thich dong dai.
                """

                with st.spinner("Dang xu ly..."):
                    try:
                        response = groq_client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            model="llama3-8b-8192"
                        )
                        st.markdown("---")
                        st.markdown(response.choices[0].message.content)
                    except Exception as ai_err:
                        st.error(f"Loi truy van Groq API: {ai_err}")

except Exception as e:
    st.error(f"Loi ket noi MotherDuck hoac thuc thi truy van: {e}")
