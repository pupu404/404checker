import base64
import os
import requests
import sqlite3
import streamlit as st
from tavily import TavilyClient

# ==========================================
# 🔑 設定・APIキー
# ==========================================
ADMIN_PASSWORD = "404@saya"
GOOGLE_API_KEY = "AQ.Ab8RN6JQzuK7xzgWOEKEfYQX_wrGbJc1rZsczZtXh6M-5mgf1w"
GOOGLE_CX = "526b7c083394b482d"
TAVILY_KEY = "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"
IMGBB_API_KEY = "07119f4007850a4ec9908cfdcd65b533"  # 画像一時ホスティング用キー
# ==========================================

st.set_page_config(
    page_title="404 CHECKER // SECURE TERMINAL", page_icon="⚡", layout="centered"
)

# --- サイバー・ダークテーマのカスタムCSS ---
st.markdown(
    """
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
    .admin-box {
        background-color: #0f172a;
        padding: 20px;
        border-radius: 4px;
        border: 1px solid #1e293b;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
        margin-bottom: 20px;
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
    .cyber-link {
        color: #38bdf8 !important;
        text-decoration: none;
        font-weight: bold;
        transition: color 0.2s;
    }
    .cyber-link:hover {
        color: #7dd3fc !important;
        text-decoration: underline;
    }
    .stTextInput>div>div>input, .stFileUploader>div>div {
        background-color: #0b0f19 !important;
        color: #38bdf8 !important;
        border: 1px solid #1e293b !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- データベース・認証処理 ---
def init_db():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            license_key TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute(
        "INSERT OR IGNORE INTO keys (license_key) VALUES (?)", ("404-TEST-KEY",)
    )
    conn.commit()
    conn.close()


init_db()


def verify_key(key):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT license_key FROM keys WHERE license_key = ?", (key,)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def generate_new_key():
    random_bytes = os.urandom(4)
    new_key = f"404-{random_bytes.hex().upper()}"
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO keys (license_key) VALUES (?)", (new_key,))
        conn.commit()
        return new_key
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_all_keys():
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("SELECT license_key, created_at FROM keys")
    results = cursor.fetchall()
    conn.close()
    return results


def delete_key(key):
    conn = sqlite3.connect("licenses.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM keys WHERE license_key = ?", (key,))
    conn.commit()
    conn.close()


# 安定性の高いBase64方式でImgBBに画像をホスティングする関数
def upload_to_image_hosting(image_file):
    if not IMGBB_API_KEY:
        return None
    try:
        image_file.seek(0)
        image_bytes = image_file.read()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        payload = {"key": IMGBB_API_KEY, "image": encoded_image}
        response = requests.post("https://api.imgbb.com/1/upload", data=payload)
        data = response.json()

        if data.get("success"):
            return data["data"]["url"]
        else:
            # エラー内容をコンソールやログ用に確認できるようにする
            print(f"ImgBB Error Details: {data}")
    except Exception as e:
        print(f"Exception during upload: {e}")
    return None


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.current_key = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False


# ==========================================
# 1. 管理者画面
# ==========================================
if st.session_state.is_admin:
    st.markdown(
        '<div class="cyber-title">404 CHECKER // ADMIN CONSOLE</div>',
        unsafe_allow_html=True,
    )

    if st.sidebar.button("SESSION TERMINATE"):
        st.session_state.is_admin = False
        st.session_state.authenticated = False
        st.rerun()

    st.markdown('<div class="admin-box">', unsafe_allow_html=True)
    st.markdown("### [ SYSTEM LICENSE MANAGER ]")

    if st.button("GENERATE NEW LICENSE KEY"):
        created = generate_new_key()
        if created:
            st.success(f"KEY GENERATED: {created}")
        else:
            st.error("ERROR: DUPLICATE KEY")

    st.markdown("---")
    st.markdown("### [ ACTIVE KEYS ]")
    keys = get_all_keys()
    if keys:
        for k, date in keys:
            col1, col2, col3 = st.columns([3, 2, 1])
            col1.markdown(f"`{k}`")
            col2.text(date)
            if col3.button("REVOKE", key=f"del_{k}"):
                delete_key(k)
                st.success(f"REVOKED: {k}")
                st.rerun()
    else:
        st.info("NO ACTIVE KEYS FOUND")

    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ==========================================
# 2. 認証画面
# ==========================================
if not st.session_state.authenticated:
    st.markdown(
        '<div class="cyber-title">404 CHECKER // ACCESS CONTROL</div>',
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown("### [ ENTER LICENSE KEY OR ROOT PASS ]")
        input_key = st.text_input(
            "ライセンスキー",
            type="password",
            placeholder="404-XXXX-XXXX または アドミンパスワード",
        )

        if st.button("AUTHENTICATE"):
            entered_val = input_key.strip()
            if entered_val == ADMIN_PASSWORD:
                st.session_state.is_admin = True
                st.session_state.authenticated = True
                st.success("ROOT ACCESS GRANTED")
                st.rerun()
            elif verify_key(entered_val):
                st.session_state.authenticated = True
                st.session_state.current_key = entered_val
                st.success("ACCESS GRANTED")
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID KEY OR PASSWORD")

    st.stop()


# ==========================================
# 3. メインコンソール
# ==========================================
st.markdown(
    '<div class="cyber-title">404 CHECKER // ULTIMATE TERMINAL</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(f"ACTIVE KEY: `{st.session_state.current_key}`")
if st.sidebar.button("SESSION TERMINATE"):
    st.session_state.authenticated = False
    st.session_state.current_key = None
    st.rerun()

if "logs" not in st.session_state:
    st.session_state.logs = "[404 SYSTEM] Initialized. Ready for target scan..."


def add_log(msg):
    st.session_state.logs += f"\n{msg}"


tab_choice1, tab_choice2 = st.tabs(["🖼️ 拾い画チェック (画像検索)", "🔍 キーワード検索 (Google & Tavily)"])

with tab_choice1:
    st.markdown("### [ TARGET IMAGE UPLOAD ]")
    uploaded_file = st.file_uploader(
        "画像アップロード",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        st.image(uploaded_file, caption="TARGET PREVIEW", use_column_width=True)

    if st.button("EXECUTE IMAGE 404 SCAN"):
        if uploaded_file is not None:
            add_log(f"[+] Target loaded: {uploaded_file.name}")
            add_log("[*] Uploading image via Base64 payload...")

            hosted_url = upload_to_image_hosting(uploaded_file)

            if hosted_url:
                add_log(f"[+] Buffer created: {hosted_url}")
                google_lens_url = f"https://lens.google.com/uploadbyurl?url={hosted_url}"
                tineye_url = f"https://tineye.com/search?url={hosted_url}"

                add_log("[+] Scan complete. Direct endpoints ready.")

                st.markdown(
                    f"""
                    <div class="results-terminal">
                    <h4>⚡ 404 CHECKER // DIRECT IMAGE SEARCH ENDPOINTS</h4>
                    <p><b>[Google Lens Direct Search]:</b><br><a href="{google_lens_url}" target="_blank" class="cyber-link">👉 検索結果ページを開く (Google Lens)</a></p>
                    <p><b>[TinEye Match Trace]:</b><br><a href="{tineye_url}" target="_blank" class="cyber-link">👉 一致結果ページを開く (TinEye)</a></p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                add_log("[-] ERROR: Image hosting failed.")
                st.error("画像のアップロード（ImgBBへのホスティング）に失敗しました。APIキーを確認してください。")
        else:
            add_log("[-] ERROR: No target image provided.")
            st.warning("画像をアップロードしてください。")

with tab_choice2:
    st.markdown("### [ SEARCH QUERY INPUT ]")
    query = st.text_input("検索キーワードを入力", "拾い画 チェック")

    if st.button("EXECUTE API 404 SCAN"):
        if not query:
            st.warning("検索ワードを入力してください。")
        else:
            add_log(f"[*] Executing API search for: '{query}'")
            sub_tab1, sub_tab2 = st.tabs(["🖼️ Google Custom Search", "🤖 Tavily AI Web Search"])

            with sub_tab1:
                st.subheader("Google Custom Search (画像検索)")
                with st.spinner("Google検索中..."):
                    url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        "key": GOOGLE_API_KEY,
                        "cx": GOOGLE_CX,
                        "q": query,
                        "searchType": "image",
                        "lr": "lang_ja",
                    }
                    res = requests.get(url, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        items = data.get("items", [])
                        if items:
                            cols = st.columns(3)
                            for i, item in enumerate(items):
                                with cols[i % 3]:
                                    st.image(
                                        item.get("link"),
                                        caption=item.get("title"),
                                        use_column_width=True,
                                    )
                            add_log("[+] Google Image Search completed.")
                        else:
                            st.info("画像が見つかりませんでした。")
                    else:
                        st.error(f"APIエラー: {res.status_code} (Google)")

            with sub_tab2:
                st.subheader("Tavily AI (ウェブ要約)")
                with st.spinner("Tavily AI検索中..."):
                    try:
                        client = TavilyClient(api_key=TAVILY_KEY)
                        response = client.search(
                            query=query,
                            search_depth="advanced",
                            include_images=True
                        )
                        
                        st.write("**🤖 AI要約:**")
                        answer = response.get("answer")
                        if answer:
                            st.info(answer)
                        else:
                            st.write("要約はありません")

                        st.write("---")
                        st.write("**🔗 関連リンク:**")
                        for result in response.get("results", []):
                            st.markdown(
                                f"- [{result.get('title')}]({result.get('url')})"
                            )
                            st.write(result.get("content"))
                        add_log("[+] Tavily AI Search completed.")
                    except Exception as e:
                        st.error(f"Tavily APIエラー: {e}")
                        add_log(f"[!] Tavily API Error: {e}")

st.markdown("---")

st.markdown("### [ EXECUTION LOG ]")
st.text_area(
    "ログ",
    value=st.session_state.logs,
    height=150,
    label_visibility="collapsed",
)
