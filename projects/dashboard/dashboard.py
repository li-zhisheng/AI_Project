"""
AI项目五：AI数据可视化智能大屏
1.基于 Streamlit + Plotly + Pandas + 大模型 API 开发企业级数据可视化仪表盘
2.支持 Excel 一键上传、自动数据解析、AI 智能分析、多图表可视化展示
3.拥有炫酷深色 UI、数据卡片、自动结论生成，具备真实商业看板体验
4.可公网访问，适合运营、销售、财务等多场景自动分析
5.技术栈：Python、Streamlit、Plotly、Pandas、AI 大模型、可视化工程
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import requests

# 页面配置
st.set_page_config(
    page_title="AI 数据可视化智能大屏",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# 自定义 CSS
st.markdown("""
    <style>
    .stMetric label {color: #555 !important;}
    .stMetric div {color: #0068c9 !important;}
    </style>
""", unsafe_allow_html=True)

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("DOUBAO_API_KEY")
API_URL = os.getenv("DOUBAO_LLM_API_URL")
MODEL_NAME = os.getenv("DOUBAO_MODEL_NAME")

# 侧边栏配置
with st.sidebar:
    st.header("⚙️ 配置信息")
    if not API_KEY or not API_URL:
        st.error("❌ 配置错误：缺少 DOUBAO_API_KEY 或 DOUBAO_LLM_API_URL")
        st.stop()
    else:
        st.success("✅ 环境变量加载成功")
        st.info(f"当前模型：{MODEL_NAME}")
    
    st.markdown("---")
    st.markdown("### 📖 使用说明")
    st.markdown("""
    1. 上传 Excel 文件 (.xlsx)
    2. 等待 AI 自动分析数据概况
    3. 查看自动生成的可视化图表
    """)

# LLM 分析函数
def ai_analyze_data(df):
    desc_str = df.describe().to_string()
    if len(desc_str) > 2000:
        desc_str = desc_str[:2000] + "...(数据截断)"
    
    prompt = f"""
    你是专业数据分析师。请分析以下数据概况，生成简洁专业的分析报告。
    【数据概况】
    - 行数：{len(df)}
    - 列名：{', '.join(df.columns)}
    - 数值统计摘要：
    {desc_str}
    【输出要求】
    请严格按照以下格式输出（使用 Markdown 格式）：
    ### 1. 数据整体情况
    (简述数据规模和完整性)
    ### 2. 关键发现
    - 发现点 1
    - 发现点 2
    ### 3. 业务建议
    - 建议 1
    - 建议 2
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    try:
        res = requests.post(API_URL, headers=headers, json=data, timeout=60)
        res.raise_for_status()
        result = res.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return "⚠️ 返回格式异常，未找到分析内容"
    except requests.exceptions.Timeout:
        return "⏳ 请求超时，AI 分析暂时不可用"
    except Exception as e:
        return f"❌ AI 服务连接失败：{str(e)}"

# 主标题
st.title("🤖 AI 数据可视化智能大屏")
st.markdown("### 企业级运营数据分析看板")
st.divider()

# 上传文件
uploaded_file = st.file_uploader("📂 上传 Excel 文件 (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        st.success("✅ 文件上传并解析成功！")
        
        # 第一部分：数据概览
        with st.expander("🔍 点击展开：原始数据预览"):
            st.dataframe(df, use_container_width=True, height=300)
        
        # 第二部分：核心指标卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 总行数", f"{len(df):,}")
        with col2:
            st.metric("🏷️ 字段数量", len(df.columns))
        with col3:
            missing_vals = df.isna().sum().sum()
            st.metric("⚠️ 缺失值总数", f"{missing_vals:,}", 
                      delta="正常" if missing_vals == 0 else "需关注")
        with col4:
            numeric_cols_count = df.select_dtypes(include=["number"]).shape[1]
            st.metric("🔢 数值列数", numeric_cols_count)
        
        st.divider()

        # 第三部分：AI 智能分析
        st.subheader("🧠 AI 智能分析结论")
        with st.spinner("🤖 AI 正在深度分析数据，请稍候..."):
            ai_result = ai_analyze_data(df)
        
        st.markdown(ai_result)
        st.divider()

        # 第四部分：自动化可视化
        st.subheader("📈 智能可视化图表")
        num_cols = df.select_dtypes(include=["number"]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()
        
        if len(num_cols) == 0:
            st.warning("⚠️ 未检测到数值型列，无法生成统计图表。")
        else:
            # 策略 1：如果有分类列和数值列
            if len(cat_cols) > 0 and len(num_cols) > 0:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"### 📊 {num_cols[0]} 按 {cat_cols[0]} 分布")
                    top_cats = df[cat_cols[0]].value_counts().head(50).index
                    df_filtered = df[df[cat_cols[0]].isin(top_cats)]
                    
                    fig_bar = px.bar(df_filtered, x=cat_cols[0], y=num_cols[0],
                                     title=f"{num_cols[0]} Top50 分布", 
                                     color=num_cols[0],
                                     color_continuous_scale="Blues")
                    st.plotly_chart(fig_bar, use_container_width=True)
                
                with c2:
                    st.markdown(f"### 🥧 {num_cols[0]} 占比分析 (按 {cat_cols[0]})")
                    pie_data = df.groupby(cat_cols[0])[num_cols[0]].sum().reset_index()
                    
                    if len(pie_data) > 10:
                        pie_data = pie_data.sort_values(by=num_cols[0], ascending=False)
                        top_10 = pie_data.head(10)
                        other_sum = pie_data[10:][num_cols[0]].sum()
                        if other_sum > 0:
                            other_row = pd.DataFrame({cat_cols[0]: ["其他"], num_cols[0]: [other_sum]})
                            pie_data = pd.concat([top_10, other_row])
                    
                    fig_pie = px.pie(pie_data, values=num_cols[0], names=cat_cols[0], 
                                     title=f"{num_cols[0]} 构成比例", hole=0.4)
                    st.plotly_chart(fig_pie, use_container_width=True)
            
            
            if len(cat_cols) == 0 or (len(cat_cols) > 0 and len(num_cols) > 1):
                 pass 

            # 更稳健的逻辑：如果只有数值列，走策略2
            if len(cat_cols) == 0:
                c3, c4 = st.columns(2)
                with c3:
                    st.markdown(f"### 📉 {num_cols[0]} 趋势/分布")
                    fig_line = px.line(df, y=num_cols[0], title=f"{num_cols[0]} 变化趋势", markers=True)
                    st.plotly_chart(fig_line, use_container_width=True)
                
                with c4:
                    if len(num_cols) > 1:
                        st.markdown(f"### 🔗 {num_cols[0]} vs {num_cols[1]} 相关性")
                        fig_scatter = px.scatter(df, x=num_cols[0], y=num_cols[1], 
                                                 title=f"{num_cols[0]} 与 {num_cols[1]} 关系",
                                                 trendline="ols")
                        st.plotly_chart(fig_scatter, use_container_width=True)
                    else:
                        st.markdown(f"### 📊 {num_cols[0]} 直方图")
                        fig_hist = px.histogram(df, x=num_cols[0], title=f"{num_cols[0]} 频率分布")
                        st.plotly_chart(fig_hist, use_container_width=True)

        st.balloons()
        st.success("🎉 AI 数据大屏加载完成！")

    except Exception as e:
        st.error(f"❌ 文件处理出错：{str(e)}")
        # 开发模式下打印详细错误堆栈
        import traceback
        st.code(traceback.format_exc())
        st.stop()

else:
    col_empty1, col_empty2, col_empty3 = st.columns([1, 2, 1])
    with col_empty2:
        st.info("👆 请在上方上传 Excel 文件以开始分析")
        st.markdown("""
        **支持的分析场景：**
        - 🛒 销售数据复盘
        - 👥 用户行为分析
        - 📦 库存运营监控
        - 💰 财务报表概览
        
        *系统会自动识别数值列与分类列，生成最合适的图表。*
        """)