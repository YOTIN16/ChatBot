from google.generativeai.types 
import HarmCategory, HarmBlockThreshold
import os
import time
import json
from datetime import datetime
import google.generativeai as genai
import streamlit as st
import dotenv

# ==========================================
# 0. 🛠️ ระบบจัดการ Path อัตโนมัติ
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_PATH = os.path.join(BASE_DIR, "Data_Content_Network.pdf")
HISTORY_FILE = os.path.join(BASE_DIR, "chat_history.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

dotenv.load_dotenv(ENV_PATH)

# --- ⚡ สร้างไฟล์ประวัติถ้ายังไม่มี ---
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)

# ==========================================
# 1. ตั้งค่า API
# ==========================================
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
if not GOOGLE_API_KEY:
    st.error("❌ ไม่พบ API Key กรุณาตรวจสอบไฟล์ .env")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# ==========================================
# 2. ตั้งค่าหน้าเว็บ
# ==========================================
st.set_page_config(
    page_title="Network Genius AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# 3. CSS Styling
# ==========================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Sarabun:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-color: #F0F9FF;
        --text-color: #334155;
    }

    .stApp {
        background-color: var(--bg-color);
        background-image: radial-gradient(#E0F2FE 1px, transparent 1px);
        background-size: 20px 20px;
        font-family: 'Sarabun', 'Inter', sans-serif;
        color: var(--text-color);
    }
    
    div[data-testid="stStatusWidget"], header, footer { display: none; }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 7rem !important;
        max-width: 900px !important;
    }

    /* Chat Bubbles */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]:first-child) {
        flex-direction: row-reverse;
        text-align: right;
    }
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]:first-child) [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #7DD3FC 0%, #0EA5E9 100%);
        color: white;
        border-radius: 20px 20px 4px 20px;
        box-shadow: 0 4px 10px rgba(14, 165, 233, 0.2);
        padding: 12px 20px;
        border: none;
    }
    div[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageContent"]:first-child)) [data-testid="stChatMessageContent"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(5px);
        color: var(--text-color);
        border: 1px solid #BAE6FD;
        border-radius: 20px 20px 20px 4px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
        padding: 12px 20px;
    }

    .stChatMessage .stChatMessageAvatar {
        background-color: white !important;
        border: 2px solid #E0F2FE;
        border-radius: 50%;
        padding: 2px;
    }

    /* Hero Section */
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
    .hero-icon { font-size: 5rem; margin-bottom: 0.5rem; animation: float 3s ease-in-out infinite; }
    .hero-title { font-size: 2rem; font-weight: 700; color: #0284C7; margin-bottom: 0.5rem; font-family: 'Inter', sans-serif; }
    .hero-subtitle { font-size: 1rem; color: #64748B; margin-bottom: 2rem; }

    /* Buttons */
    .stButton button {
        background-color: white !important;
        border: 1px solid #E0F2FE !important;
        border-radius: 16px !important;
        padding: 1rem !important;
        text-align: left !important;
        box-shadow: 0 4px 0px #E0F2FE !important;
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
    .stButton button p { font-size: 0.95rem; font-weight: 600; color: #475569 !important; }

    /* Input */
    .stChatInput { bottom: 20px !important; }
    .stChatInput > div {
        background-color: white; border-radius: 30px;
        box-shadow: 0 8px 30px rgba(14, 165, 233, 0.15);
        border: 1px solid #BAE6FD; padding-bottom: 0 !important;
    }
    .stChatInput textarea { height: 50px !important; padding-top: 12px !important; color: #334155 !important; }

    @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes float { 0% { transform: translateY(0px); } 50% { transform: translateY(-10px); } 100% { transform: translateY(0px); } }
    section[data-testid="stSidebar"] { background-color: white; border-right: 1px solid #F1F5F9; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. ฟังก์ชันช่วยเหลือ (Utility)
# ==========================================
def save_history(user_msg, ai_msg):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            try: history = json.load(f)
            except: pass
    history.append({'timestamp': datetime.now().isoformat(), 'user': user_msg, 'ai': ai_msg})
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history[-20:], f, ensure_ascii=False, indent=2)

@st.cache_resource
def get_available_models():
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini' in m.name:
                    models.append(m.name)
        return models
    except Exception as e:
        return ["models/gemini-1.5-flash"] 

@st.cache_resource(show_spinner=False)
def get_gemini_file(path):
    if not os.path.exists(path): return None
    try:
        file = genai.upload_file(path, mime_type="application/pdf")
        while file.state.name == "PROCESSING":
            time.sleep(1)
            file = genai.get_file(file.name)
        return file
    except Exception as e:
        st.error(f"Upload Error: {str(e)}")
        return None

# ==========================================
# 5. Sidebar (Control Panel)
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=70)
    st.title("Network Genius")
    st.markdown("<div style='color:#64748B; margin-top:-15px; font-size:0.9rem;'>AI Assistant for Network Ops</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # 1. Model Selector
    st.markdown("### ⚙️ เลือกโมเดล")
    available_models = get_available_models()
    if available_models:
        default_idx = 0
        for i, m in enumerate(available_models):
            if "flash" in m and "1.5" in m:
                default_idx = i
                break
        selected_model = st.selectbox("Available Models:", options=available_models, index=default_idx)
    else:
        st.error("Check API Key")
        selected_model = "models/gemini-pro"

    st.divider()
    
    # 2. PDF Status
    if "gemini_file" not in st.session_state:
        with st.spinner("☁️ Connecting to Knowledge Base..."):
            file_obj = get_gemini_file(PDF_PATH)
            if file_obj:
                st.session_state.gemini_file = file_obj
                st.success("✅ Knowledge Base Online")
            else:
                st.error(f"❌ ไม่พบไฟล์ PDF")
                st.warning("กรุณาวางไฟล์ Data_Content_Network.pdf ไว้คู่กับ app.py")
    else:
        st.info("✅ Database Active")

    st.divider()
    
    # 3. ปุ่มควบคุม (Reset & Clear History)
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("✨ รีเซ็ตแชท", use_container_width=True, type="primary"):
            st.session_state.messages = []
            st.rerun()
            
    with col_btn2:
        # ⭐ ปุ่มล้างประวัติ (เพิ่มใหม่) ⭐
        if st.button("🗑️ ล้างประวัติ", use_container_width=True):
            # ล้างไฟล์
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            # ล้างหน้าจอ
            st.session_state.messages = []
            st.rerun()
    
    st.markdown("---")

    # 4. แสดงประวัติ
    st.markdown("### 📜 ประวัติการสนทนา")
    if os.path.exists(HISTORY_FILE):
        with st.expander("คลิกเพื่อดูประวัติเก่า (Saved)"):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                try:
                    past_chats = json.load(f)
                    if not past_chats:
                        st.caption("ว่างเปล่า...")
                    for chat in reversed(past_chats):
                        timestamp = chat.get('timestamp', '').replace('T', ' ')[:16]
                        st.caption(f"🕒 {timestamp}")
                        st.markdown(f"**👤 You:** {chat.get('user')}")
                        st.info(f"**🤖 AI:** {chat.get('ai')}")
                        st.markdown("---")
                except:
                    st.error("ไฟล์ประวัติเสียหาย")
    else:
        st.caption("กำลังสร้างไฟล์ประวัติใหม่...")

    st.markdown("---")
    st.caption(f"Model: {selected_model}")

# ==========================================
# 6. Main Chat Interface
# ==========================================

if "messages" not in st.session_state: st.session_state.messages = []

hero_placeholder = st.empty()

if len(st.session_state.messages) == 0:
    with hero_placeholder.container():
        st.markdown("""
            <div class="hero-container">
                <div class="hero-icon">⚡</div>
                <div class="hero-title">สวัสดีครับ! ให้ผมช่วยเรื่อง Network นะครับ</div>
                <div class="hero-subtitle">ผมอ่านคู่มือ Network ของคุณเรียบร้อยแล้ว ถามได้ทุกเรื่องครับ</div>
            </div>
        """, unsafe_allow_html=True)
        
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

for message in st.session_state.messages:
    avatar = "🧑‍💻" if message["role"] == "user" else "⚡"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

if prompt := st.chat_input("พิมพ์คำถามของคุณที่นี่..."):
    final_prompt = prompt
elif "pending_prompt" in st.session_state:
    final_prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt
else:
    final_prompt = None

# ==========================================
# 7. AI Processing
# ==========================================
if final_prompt:
    hero_placeholder.empty()

    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(final_prompt)

    if "gemini_file" in st.session_state:
        with st.chat_message("assistant", avatar="⚡"):
            msg_placeholder = st.empty()
            full_res = ""
            try:
               # 1. ตั้งค่าโมเดล (Config Model)
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    generation_config={
                        "temperature": 0.3, 
                        "top_p": 0.8, 
                        "top_k": 40, 
                        "max_output_tokens": 2048
                    },
                    # ⭐ เพิ่มส่วนนี้: ปลดล็อกความปลอดภัย (เพราะเราคุยเรื่อง Network ไม่ใช่เรื่องผิดกฎหมาย)
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    },
                    # System Instruction 
                    system_instruction="""
                    You are 'Network Genius', an AI assistant specialized in Network Operations.
                    
                    Instructions:
                    1. Identity: If the user asks "Who are you?" or greets you, introduce yourself politely as an AI assistant helping with the uploaded Network documentation.
                    2. Knowledge Base: For technical questions, answer based ONLY on the provided PDF file.
                    3. Unknowns: If the answer is not in the file, say 'ขออภัย ข้อมูลส่วนนี้ไม่มีในเอกสาร'.
                    4. Tone: Helpful, professional, and concise.
                    """
                )
                # ... (ส่วนโค้ดด้านล่างเหมือนเดิม) ...
                
                history = [{"role": "user", "parts": [st.session_state.gemini_file, "Answer based on this file. Do not use outside knowledge."]}]
                for m in st.session_state.messages[:-1]:
                    role = "model" if m["role"] == "assistant" else "user"
                    history.append({"role": role, "parts": [m["content"]]})

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
                err_msg = str(e)
                if "429" in err_msg:
                    st.error(f"⚠️ โมเดล {selected_model} โควตาเต็ม! กรุณาเลือกตัวอื่นจาก Dropdown ด้านซ้าย")
                elif "404" in err_msg:
                    st.error(f"⚠️ โมเดล {selected_model} ใช้ไม่ได้กับ Key นี้ กรุณาเลือกตัวอื่นจาก Dropdown")
                else:
                    st.error(f"Error: {err_msg}")
    else:

        st.error("Connection Lost. Please refresh.")
