import streamlit as st
from langchain_openai import ChatOpenAI
from agent_logic import create_travel_agent, get_langchain_plan
from tools import generate_ics_content
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==================== Streamlit UI 设置 ====================
st.set_page_config(
    page_title="GGGroup 的AI 旅行计划器",
    page_icon="✈️",
    layout="wide"
)

st.title("GGGroup 的AI 旅行计划器 ✈️")
st.caption("由大语言模型驱动，为您自动规划个性化行程。")

# 初始化 session state
if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None
if 'destination' not in st.session_state:
    st.session_state.destination = ""
if 'num_days' not in st.session_state:
    st.session_state.num_days = 7

# ==================== 配置设置 ====================
# 直接从环境变量获取API密钥
api_key = os.getenv("DASHSCOPE_API_KEY") or st.secrets.get("DASHSCOPE_API_KEY")
base_url = os.getenv("DASHSCOPE_BASE_URL") or st.secrets.get(
    "DASHSCOPE_BASE_URL", 
    "https://dashscope.aliyuncs.com/compatible-mode/v1"
)
serp_api_key = os.getenv("SERP_API_KEY") or st.secrets.get("SERP_API_KEY")
model_id = "qwen-max"  # 固定使用阿里云 Qwen 模型

# ==================== 初始化客户端和 Agent ====================
agent_executor = None

if api_key and serp_api_key:
    try:
        llm = ChatOpenAI(
            model=model_id,
            api_key=api_key,
            base_url=base_url,
            temperature=0,
            streaming=True
        )
        agent_executor = create_travel_agent(llm, serp_api_key)
    except Exception as e:
        st.error(f"初始化 AI 客户端或 Agent 时出错: {e}")
else:
    missing_keys = []
    if not api_key:
        missing_keys.append("DashScope API密钥")
    if not serp_api_key:
        missing_keys.append("SerpAPI密钥")
    st.error(f"❌ 缺少必需的API密钥: {', '.join(missing_keys)}")
    st.stop()

# ==================== 主界面 ====================
st.header("📝 输入您的旅行需求")

col1, col2 = st.columns([2, 1])
with col1:
    destination = st.text_input(
        "您想去哪里？", 
        placeholder="例如：日本东京",
        value=st.session_state.destination,
        key="destination_input"
    )
with col2:
    num_days = st.number_input(
        "您想旅行多少天？", 
        min_value=1, 
        max_value=30, 
        value=st.session_state.num_days,
        key="days_input"
    )

interests = st.text_area(
    "您的兴趣和偏好（可选）", 
    placeholder="例如：我喜欢美食、历史文化和自然风光，希望行程不要太赶。",
    height=100
)

if st.button("🚀 生成行程", use_container_width=True, type="primary"):
    if not destination:
        st.warning("请输入目的地。")
    else:
        st.session_state.destination = destination
        st.session_state.num_days = num_days
        st.session_state.itinerary = None
        
        with st.spinner("AI Agent 正在思考和规划中，这可能需要一些时间..."):
            try:
                itinerary_text = get_langchain_plan(agent_executor, destination, num_days)
                st.session_state.itinerary = itinerary_text
                
                # 添加成功提示
                st.success("行程生成成功！")
                
            except Exception as e:
                st.error(f"Agent 执行出错: {e}")
                st.stop()

if st.session_state.itinerary:
    st.header("📅 您的专属行程")
    
    # 使用 expander 使行程显示更整洁
    with st.expander("查看完整行程", expanded=True):
        st.markdown(st.session_state.itinerary)
    
    st.divider()
    st.subheader("📥 导出行程")
    
    try:
        ics_content = generate_ics_content(st.session_state.itinerary)
        st.download_button(
            label="下载为日历文件 (.ics)",
            data=ics_content,
            file_name=f"{destination.replace(' ', '_')}_travel_itinerary.ics",
            mime="text/calendar",
            use_container_width=True,
            icon="📅"
        )
    except Exception as e:
        st.error(f"生成日历文件时出错: {e}")
        
    # 添加重新生成按钮
    if st.button("🔄 重新生成行程", use_container_width=True):
        st.session_state.itinerary = None
        st.rerun()

# 添加使用说明
with st.expander("使用说明"):
    st.markdown("""
    1. 输入您的旅行目的地和天数
    2. 可选：添加您的兴趣和偏好
    3. 点击"生成行程"按钮
    4. 查看生成的行程并可以下载为日历文件
    
    **注意**: 本应用使用阿里云 Qwen 大模型和网络搜索功能为您生成个性化旅行计划。
    """)

# 添加页脚
st.divider()
st.caption("GGGroup 2025短学期项目 - AI 旅行计划器")
