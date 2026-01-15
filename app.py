import os
import time
import json
from datetime import datetime
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold 
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
    
    :root { --bg-color: #F0F9FF; --text-color: #334155; }
    .stApp { background-color: var(--bg-color); font-family: 'Sarabun', 'Inter', sans-serif; color: var(--text-color); }
    div[data-testid="stStatusWidget"], header, footer { display: none; }
    .block-container { padding-top: 2rem !important; padding-bottom: 7rem !important; max-width: 900px !important; }

    /* Chat Bubbles */
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]:first-child) { flex-direction: row-reverse; text-align: right; }
    div[data-testid="stChatMessage"]:has([data-testid="stChatMessageContent"]:first-child) [data-testid="stChatMessageContent"] {
        background: linear-gradient(135deg, #7DD3FC 0%, #0EA5E9 100%); color: white; border-radius: 20px 20px 4px 20px;
    }
    div[data-testid="stChatMessage"]:not(:has([data-testid="stChatMessageContent"]:first-child)) [data-testid="stChatMessageContent"] {
        background: rgba(255, 255, 255, 0.9); border: 1px solid #BAE6FD; border-radius: 20px 20px 20px 4px;
    }
    .stChatMessage .stChatMessageAvatar { background-color: white !important; border: 2px solid #E0F2FE; border-radius: 50%; padding: 2px; }

    /* Hero & Buttons */
    .hero-container { text-align: center; padding: 3rem 1rem; background: rgba(255, 255, 255, 0.7); border-radius: 24px; border: 1px solid #E0F2FE; margin-bottom: 2rem; }
    .hero-icon { font-size: 5rem; margin-bottom: 0.5rem; }
    .hero-title { font-size: 2rem; font-weight: 700; color: #0284C7; }
    .stButton button { background-color: white !important; border: 1px solid #E0F2FE !important; border-radius: 16px !important; text-align: left !important; }
    .stButton button:hover { border-color: #38BDF8 !important; transform: translateY(-2px); }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. Utility Functions
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
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                models.append(m.name)
        return models
    except: return ["models/gemini-1.5-flash"]

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

# ==========================================
# 5. Sidebar
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/4712/4712109.png", width=70)
    st.title("Network Genius")
    st.divider()
    
    # Model Selector
    st.markdown("### ⚙️ เลือกโมเดล")
    available_models = get_available_models()
    if available_models:
        default_idx = 0
        for i, m in enumerate(available_models):
            if "flash" in m and "1.5" in m: default_idx = i; break
        selected_model = st.selectbox("Model:", options=available_models, index=default_idx)
    else: selected_model = "models/gemini-pro"

    st.divider()
    
    # PDF Status
    if "gemini_file" not in st.session_state:
        with st.spinner("Connecting..."):
            file_obj = get_gemini_file(PDF_PATH)
            if file_obj: st.session_state.gemini_file = file_obj; st.success("✅ PDF Online")
            else: st.error(f"❌ PDF Not Found"); st.warning(f"Check: {PDF_PATH}")
    else: st.info("✅ Database Active")

    st.divider()
    
    # Buttons
    c1, c2 = st.columns(2)
    with c1: 
        if st.button("✨ รีเซ็ต", use_container_width=True, type="primary"): st.session_state.messages = []; st.rerun()
    with c2: 
        if st.button("🗑️ ล้างประวัติ", use_container_width=True):
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f: json.dump([], f)
            st.session_state.messages = []; st.rerun()
    
    st.markdown("---")
    
    # History Log
    st.markdown("### 📜 ประวัติ")
    if os.path.exists(HISTORY_FILE):
        with st.expander("ดูประวัติเก่า"):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                try:
                    for chat in reversed(json.load(f)):
                        st.caption(f"🕒 {chat.get('timestamp','').replace('T',' ')[:16]}")
                        st.markdown(f"**You:** {chat.get('user')}")
                        st.info(f"**AI:** {chat.get('ai')}")
                        st.markdown("---")
                except: pass

# ==========================================
# 6. Main Chat
# ==========================================
if "messages" not in st.session_state: st.session_state.messages = []

hero_placeholder = st.empty()
if len(st.session_state.messages) == 0:
    with hero_placeholder.container():
        st.markdown("""<div class="hero-container"><div class="hero-icon">⚡</div><div class="hero-title">สวัสดีครับ! ให้ผมช่วยเรื่อง Network นะครับ</div></div>""", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📝 สรุปเนื้อหาสำคัญ", use_container_width=True): st.session_state.pending_prompt = "ช่วยสรุป Concept หลักจากไฟล์ PDF นี้ให้หน่อย"; st.rerun()
        with c2:
            if st.button("🌐 อธิบาย OSPF", use_container_width=True): st.session_state.pending_prompt = "อธิบายหลักการทำงานของ OSPF แบบเข้าใจง่าย"; st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🧑‍💻" if msg["role"]=="user" else "⚡"): st.markdown(msg["content"])

if prompt := st.chat_input("พิมพ์คำถาม..."): final_prompt = prompt
elif "pending_prompt" in st.session_state: final_prompt = st.session_state.pending_prompt; del st.session_state.pending_prompt
else: final_prompt = None

# ==========================================
# 7. AI Logic (พร้อม Safety Fix & Identity Fix)
# ==========================================
if final_prompt:
    hero_placeholder.empty()
    st.session_state.messages.append({"role": "user", "content": final_prompt})
    with st.chat_message("user", avatar="🧑‍💻"): st.markdown(final_prompt)

    if "gemini_file" in st.session_state:
        with st.chat_message("assistant", avatar="⚡"):
            msg_placeholder = st.empty(); full_res = ""
            try:
                # ✅ 1. ตั้งค่า Model + Safety Settings (แก้ Error finish_reason 2)
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    generation_config={"temperature": 0.3, "top_p": 0.8, "top_k": 40, "max_output_tokens": 2048},
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    },
                    # ✅ 2. System Instruction (แก้ให้แนะนำตัวได้)
                    system_instruction="""
                    You are 'Network Genius', an AI assistant specialized in Network Operations.
                    1. If asked "Who are you", introduce yourself politely.
                    2. For technical questions, answer based ONLY on the provided PDF file.
                    3. If answer is not in file, say 'ขออภัย ข้อมูลส่วนนี้ไม่มีในเอกสาร'.
                    """
                )
                
                # ✅ 3. ส่ง PDF + History
                history = [{"role": "user", "parts": [st.session_state.gemini_file, "Answer based on this file."]}]
                for m in st.session_state.messages[:-1]:
                    history.append({"role": "model" if m["role"]=="assistant" else "user", "parts": [m["content"]]})

                chat = model.start_chat(history=history)
                response = chat.send_message(final_prompt, stream=True)
                
                for chunk in response:
                    if chunk.text: full_res += chunk.text; msg_placeholder.markdown(full_res + "▌"); time.sleep(0.01)
                
                msg_placeholder.markdown(full_res)
                st.session_state.messages.append({"role": "assistant", "content": full_res})
                save_history(final_prompt, full_res)
                
            except Exception as e:
                err = str(e)
                if "429" in err: st.error(f"⚠️ โควตาเต็ม (Model: {selected_model}) -> ลองเปลี่ยนโมเดล")
                elif "finish_reason" in err: st.error("⚠️ AI หยุดทำงาน (Safety/Length) -> กดปุ่ม 'ล้างประวัติ' แล้วลองใหม่")
                else: st.error(f"Error: {err}")
    else: st.error("Connection Lost. Refresh page.")
