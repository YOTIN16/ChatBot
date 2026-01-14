import os
import time
import json
from datetime import datetime
import google.generativeai as genai
import streamlit as st
import dotenv

# Load Environment Variables
dotenv.load_dotenv()

# ================= Configuration =================
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    st.error("❌ ไม่พบ API Key กรุณาตรวจสอบไฟล์ .env")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)
PDF_PATH = r"Data_Content_Network.pdf"

# ================= Page Config =================
st.set_page_config(
    page_title="Network Genius AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ================= Soft Sky Blue Theme UI & CSS =================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sarabun:wght@300;400;500;600;700&display=swap');
    
    :root {
        /* Soft Sky Blue Palette */
        --primary-color: #38BDF8; /* Sky Blue */
        --primary-dark: #0284C7;  /* Deep Sky */
        --secondary-color: #E0F2FE; /* Pale Blue */
        --text-color: #334155;    /* Slate Gray */
        --bg-color: #F0F9FF;      /* Alice Blue */
        --white: #FFFFFF;
    }

    /* Reset & Base */
    .stApp {
        background-color: var(--bg-color);
        background-image: radial-gradient(#E0F2FE 1px, transparent 1px);
        background-size: 20px 20px;
        font-family: 'Sarabun', 'Inter', sans-serif;
        color: var(--text-color);
    }
    
    /* Hide Default Elements */
    div[data-testid="stStatusWidget"], header, footer { display: none; }
    
    /* Layout Adjustment */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
        max-width: 900px !important;
    }

    /* ========== 1. Chat Bubbles (Soft Blue Style) ========== */
    /* User Message */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]:first-child) {
        flex-direction: row-reverse;
        text-align: right;
    }
    
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]:first-child) [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #7DD3FC 0%, #0EA5E9 100%); /* Soft Gradient */
        color: white;
        border-radius: 20px 20px 4px 20px;
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.2);
        padding: 12px 20px;
        border: none;
    }

    /* AI Message */
    div[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageContent"]:first-child)) [data-testid="stChatMessageContent"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(5px);
        color: var(--text-color);
        border: 1px solid #BAE6FD;
        border-radius: 20px 20px 20px 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        padding: 12px 20px;
    }

    /* Avatars */
    .stChatMessage .stChatMessageAvatar {
        background-color: white !important;
        border: 2px solid #E0F2FE;
        border-radius: 50%;
        padding: 2px;
    }

    /* ========== 2. Hero Section (Empty State) ========== */
    .hero-container {
        text-align: center;
        padding: 3rem 1rem;
        background: rgba(255, 255, 255, 0.7);
        border-radius: 24px;
        border: 1px solid #E0F2FE;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(14, 165, 233, 0.05);
        animation: fadeIn 0.8s ease-out;
    }
    
    .hero-icon {
        font-size: 5rem;
        margin-bottom: 0.5rem;
        filter: drop-shadow(0 4px 6px rgba(14, 165, 233, 0.2));
        animation: float 3s ease-in-out infinite;
    }
    
    .hero-title {
        font-size: 2rem;
        font-weight: 700;
        color: #0284C7; /* Darker blue text */
        margin-bottom: 0.5rem;
        font-family: 'Inter', sans-serif;
    }
    
    .hero-subtitle {
        font-size: 1rem;
        color: #64748B;
        margin-bottom: 2rem;
    }

    /* Suggestion Cards Grid */
    .suggestion-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-top: 2rem;
    }

    /* Custom Button Style for Suggestions */
    .stButton button {
        background-color: white !important;
        border: 1px solid #E0F2FE !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        text-align: left !important;
        box-shadow: 0 4px 0px #E0F2FE !important; /* Cute 3D effect */
        transition: all 0.2s ease !important;
        height: 100% !important;
        width: 100% !important;
    }

    .stButton button:hover {
        border-color: #38BDF8 !important;
        background-color: #F0F9FF !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 0px #BAE6FD !important;
        color: #0284C7 !important;
    }
    
    .stButton button p {
        font-size: 0.95rem;
        font-weight: 600;
        color: #475569 !important;
    }

    /* ========== 3. Input Area ========== */
    .stChatInput {
        bottom: 20px !important;
    }
    
    .stChatInput > div {
        background-color: white;
        border-radius: 30px;
        box-shadow: 0 8px 30px rgba(14, 165, 233, 0.15);
        border: 1px solid #BAE6FD;
        padding-bottom: 0 !important;
    }
    
    .stChatInput textarea {
        height: 50px !important;
        padding-top: 12px !important;
        color: #334155 !important;
    }

    /* ========== Animations ========== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: white;
        border-right: 1px solid #F1F5F9;
    }
    
    </style>
""", unsafe_allow_html=True)

# ================= Logic =================

HISTORY_FILE = "chat_history.json"

def save_history(user_msg, ai_msg):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try: history = json.load(f)
            except: pass
    history.append({'timestamp': datetime.now().isoformat(), 'user': user_msg, 'ai': ai_msg})
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history[-20:], f, ensure_ascii=False, indent=2)

@st.cache_resource(show_spinner=False)
def get_gemini_file(path):
    if not os.path.exists(path): return None
    try:
        file = genai.upload_file(path, mime_type="application/pdf")
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
        return file
    except: return None

# ================= UI Structure =================

# 1. Sidebar (Control Panel)
with st.sidebar:
    # รูปบอท AI และข้อความตามที่คุณต้องการ
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=70)
    st.title("Network Genius")
    st.markdown("<div style='color:#64748B; margin-top:-15px; font-size:0.9rem;'>AI Assistant for Network Ops</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # File Status Indicator
    if "gemini_file" not in st.session_state:
        with st.spinner("☁️ Connecting to Knowledge Base..."):
            file_obj = get_gemini_file(PDF_PATH)
            if file_obj:
                st.session_state.gemini_file = file_obj
                st.success("✅ Knowledge Base Online")
            else:
                st.error("❌ Knowledge Base Offline")
    else:
        st.info("✅ Database Active")

    st.divider()
    
    if st.button("✨ เริ่มบทสนทนาใหม่", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    st.caption(f"Powered by Gemini 2.5 Flash\nChat Session: {datetime.now().strftime('%H:%M')}")

# 2. Main Chat Interface
if "messages" not in st.session_state: st.session_state.messages = []

# ใช้ Placeholder เพื่อจัดการ Hero Section (แก้ปัญหาต้องพิมพ์ 2 ครั้ง)
hero_placeholder = st.empty()

# --- HERO SECTION (Empty State) ---
if len(st.session_state.messages) == 0:
    with hero_placeholder.container():
        st.markdown("""
            <div class="hero-container">
                <div class="hero-icon">⚡</div>
                <div class="hero-title">สวัสดีครับ! ให้ผมช่วยเรื่อง Network นะครับ</div>
                <div class="hero-subtitle">ผมอ่านคู่มือ Network ของคุณเรียบร้อยแล้ว ถามได้ทุกเรื่องครับ</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Interactive Suggestion Cards
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📝 สรุปเนื้อหาสำคัญ\nช่วยสรุป Concept หลักจากไฟล์ PDF นี้ให้หน่อย", use_container_width=True):
                st.session_state.pending_prompt = "ช่วยสรุป Concept หลักจากไฟล์ PDF นี้ให้หน่อย"
                st.rerun()
            if st.button("🔧 เทคนิคการ Config\nสอนวิธี Config VLAN และ Trunking บน Switch", use_container_width=True):
                st.session_state.pending_prompt = "สอนวิธี Config VLAN และ Trunking บน Switch"
                st.rerun()
                
        with col2:
            if st.button("🌐 อธิบาย OSPF\nอธิบายหลักการทำงานของ OSPF แบบเข้าใจง่าย", use_container_width=True):
                st.session_state.pending_prompt = "อธิบายหลักการทำงานของ OSPF แบบเข้าใจง่าย"
                st.rerun()
            if st.button("🛡️ การแก้ปัญหา\nแนะนำขั้นตอนการ Troubleshoot เบื้องต้น", use_container_width=True):
                st.session_state.pending_prompt = "แนะนำขั้นตอนการ Troubleshoot เบื้องต้น"
                st.rerun()

# --- CHAT HISTORY ---
# แสดงประวัติการคุย (อยู่นอกเงื่อนไข else เพื่อให้แสดงผลเสมอหลังจากพิมพ์)
for message in st.session_state.messages:
    # Custom Avatar Logic
    avatar = "🧑‍💻" if message["role"] == "user" else "⚡"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 3. Input Handling
if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
    final_prompt = prompt
elif "pending_prompt" in st.session_state:
    final_prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt
else:
    final_prompt = None

# 4. Processing (Logic fix: Removed st.rerun loop)
if final_prompt:
    # เคลียร์ Hero Section ทันทีเมื่อมีการพิมพ์
    hero_placeholder.empty()

    # Show User Message
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(final_prompt)

    # Generate Response
    if "gemini_file" in st.session_state:
        with st.chat_message("assistant", avatar="⚡"):
            msg_placeholder = st.empty()
            full_res = ""
            try:
               # --- MODEL CONFIGURATION: ปรับจูนให้แม่นยำที่สุด ---
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash", 
                    
                    # 1. ปรับ Temperature เป็น 0.0 (ห้ามมั่ว เอาชัวร์ 100%)
                    generation_config={"temperature": 0.15},
                    
                    # 2. ใส่คำสั่งกำกับพฤติกรรมอย่างละเอียด (System Instruction)
                    system_instruction="""
                    You are a strict Network Engineering Expert. 
                    Your goal is to answer questions based ONLY on the provided PDF file.
                    
                    Rules:
                    1. Accuracy: Use the information from the file as your primary source of truth.
                    2. Configuration: If asked for 'Config', provide exact CLI commands found in the document.
                    3. Unknowns: If the answer is NOT in the file, politely say 'ขออภัยครับ ข้อมูลส่วนนี้ไม่มีในเอกสารอ้างอิง'. Do not make up answers.
                    4. Tone: Professional, concise, and technical.
                    """
                )
                
                # History Logic (Exclude current user message to avoid duplication in context if needed, but Gemini handles it)
                history = [{"role": "user", "parts": [st.session_state.gemini_file, "Answer based on this file."]}]
                for m in st.session_state.messages[:-1]: # เอาประวัติเก่า (ไม่รวมคำถามปัจจุบัน)
                    role = "model" if m["role"] == "assistant" else "user"
                    history.append({"role": role, "parts": [m["content"]]})

                # Stream
                chat = model.start_chat(history=history)
                response = chat.send_message(final_prompt, stream=True)
                
                for chunk in response:
                    if chunk.text:
                        full_res += chunk.text
                        msg_placeholder.markdown(full_res + "▌")
                        time.sleep(0.01)
                
                msg_placeholder.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                save_history(final_prompt, full_res)
                
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:

        st.error("Connection Lost. Please refresh.")
