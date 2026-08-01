import os
import sqlite3
import streamlit as st
import requests

# ==========================================
# 🔑 設定・APIキー
# ==========================================
ADMIN_PASSWORD = "404@saya"
GOOGLE_API_KEY = "AIzaSyBLwxZBesL4VhBMac6toIPDCZxqN1vbDPY"
GOOGLE_CX = "526b7c083394b482d"  # 必要に応じてご自身のCXに書き換えてください
# ==========================================

st.set_page_config(
    page_title="404 CHECKER // IMAGE SEARCH",
    page_icon="⚡",
    layout="centered"
)

# --- サイバー・ダークテーマのカスタムCSS ---
st.markdown("""
    <style>
    .stApp {
        background-color: #030712;
        color: #f3f4f6;
        font-family: 'Courier New', Courier, monospace;
    }
    .cyber-title {
        color: #38bdf8;
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 2px;
        border-left: 4px solid #38bdf8;
        padding-left: 10px;
        margin-bottom: 25px;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    }
    .stButton>button {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
        color: #ffffff;
        border-radius: 2px;
        font-weight: bold;
        border: 1px solid #38bdf8;
        width: 100%;
        padding: 12px;
        letter-spacing: 1px;
        box-shadow: 0 0 15px rgba(2, 132, 199, 0.3);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.6);
        border-color: #7dd3fc;
    }
    .results-terminal {
        background-color: #050b14;
        padding: 20px;
        border-radius: 4px;
        margin-top: 25px;
        border: 1px solid #0284c7;
        box-shadow: 0 0 15px rgba(2, 132, 199, 0.15);
    }
    .results-terminal h4 {
        color: #38bdf8;
        margin-top: 0;
        font-size: 16px;
        letter-spacing: 1px;
        border-bottom: 1px dashed #1e293b;
        padding-bottom: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 簡易DB（認証用） ---
def init_db():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            license_key TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("INSERT OR IGNORE INTO keys (license_key) VALUES (?)", ("404-TEST-KEY",))
    conn.commit()
    conn.close()

init_db()

def verify_key(key):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT license_key FROM keys WHERE license_key = ?", (key,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.current_key = None

# --- 認証画面 ---
if not st.session_state.authenticated:
    st.markdown('<div class="cyber-title">404 CHECKER // ACCESS CONTROL</div>', unsafe_allow_html=True)
    input_key = st.text_input("ライセンスキー", type="password", placeholder="404-XXXX-XXXX または アドミンパスワード")
    if st.button("AUTHENTICATE"):
        entered_val = input_key.strip()
        if entered_val == ADMIN_PASSWORD or verify_key(entered_val):
            st.session_state.authenticated = True
            st.session_state.current_key = entered_val
            st.rerun()
        else:
            st.error("ACCESS DENIED")
    st.stop()

# --- メイン画面：画像検索専用ツール ---
st.markdown('<div class="cyber-title">404 CHECKER // IN-APP IMAGE SEARCH</div>', unsafe_allow_html=True)
st.sidebar.markdown(f"ACTIVE KEY: `{st.session_state.current_key}`")
if st.sidebar.button("LOGOUT"):
    st.session_state.authenticated = False
    st.rerun()

st.markdown("### [ 1. ターゲット画像のアップロード ]")
uploaded_file = st.file_uploader("画像をアップロード", type=["png", "jpg", "jpeg", "webp"], label_visibility="collapsed")

if uploaded_file is not None:
    st.image(uploaded_file, caption="UPLOADED TARGET", width=300)
    
    # 検索キーワードを入力できるようにして、403エラーの切り分けをしやすくする
    search_keyword = st.text_input("検索ワード（ファイル名から自動入力されます）", value=os.path.splitext(uploaded_file.name)[0])
    
    if st.button("Googleで類似画像を検索する"):
        with st.spinner("Googleインデックスから類似写真をスキャン中..."):
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": GOOGLE_API_KEY,
                "cx": GOOGLE_CX,
                "q": search_keyword,
                "searchType": "image"
            }
            
            try:
                res = requests.get(url, params=params, timeout=10)
                data = res.json()
                
                # エラーハンドリングの強化（Googleからのエラー詳細を表示）
                if res.status_code == 200:
                    items = data.get("items", [])
                    
                    st.markdown('<div class="results-terminal">', unsafe_allow_html=True)
                    st.markdown("<h4>⚡ 類似写真・一致リンク結果</h4>", unsafe_allow_html=True)
                    
                    if items:
                        cols = st.columns(3)
                        for i, item in enumerate(items[:6]):
                            with cols[i % 3]:
                                img_link = item.get("link")
                                page_link = item.get("image", {}).get("contextLink", "#")
                                title = item.get("title", "類似画像")
                                
                                st.image(img_link, use_column_width=True)
                                st.markdown(f"**[{title[:20]}...]**({page_link})", unsafe_allow_html=True)
                    else:
                        st.info("一致する類似写真のデータが見つかりませんでした。別のキーワードでもお試しください。")
                        
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    # Google APIから返ってきた具体的なエラー理由を表示
                    err_message = data.get("error", {}).get("message", "不明なエラー")
                    st.error(f"APIエラー ({res.status_code}): {err_message}")
            except Exception as e:
                st.error(f"通信エラーが発生しました: {e}")
else:
    st.info("検索したい画像をアップロードしてください。")
