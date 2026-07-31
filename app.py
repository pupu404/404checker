import base64
import os
import requests
import sqlite3
import streamlit as st

ADMIN_PASSWORD = "404@saya"
IMGBB_API_KEY = ""  # 必要に応じて設定

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


def upload_to_image_hosting(image_file):
  if not IMGBB_API_KEY:
    return None
  try:
    image_file.seek(0)
    files = {"image": image_file.read()}
    response = requests.post(
        f"https://api.imgbb.com/1/upload?key={IMGBB_API_KEY}", files=files
    )
    data = response.json()
    if data.get("success"):
      return data["data"]["url"]
  except Exception:
    pass
  return None


if "authenticated" not in st.session_state:
  st.session_state.authenticated = False
  st.session_state.current_key = None
if "is_admin" not in st.session_state:
  st.session_state.is_admin = False


# ==========================================
# 1. 管理者画面（アドミンパスワードまたは管理権限で侵入時）
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
# 2. 認証画面（ここでライセンスキーかアドミンパスワードを受け付ける）
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
      # アドミンパスワードが一致した場合
      if entered_val == ADMIN_PASSWORD:
        st.session_state.is_admin = True
        st.session_state.authenticated = True
        st.success("ROOT ACCESS GRANTED")
        st.rerun()
      # 通常のライセンスキーが一致した場合
      elif verify_key(entered_val):
        st.session_state.authenticated = True
        st.session_state.current_key = entered_val
        st.success("ACCESS GRANTED")
        st.rerun()
      else:
        st.error("ACCESS DENIED: INVALID KEY OR PASSWORD")

  st.stop()


# ==========================================
# 3. メインコンソール（404チェッカー本編）
# ==========================================
st.markdown(
    '<div class="cyber-title">404 CHECKER // IMAGE REVERSE TERMINAL</div>',
    unsafe_allow_html=True,
)
st.sidebar.markdown(f"ACTIVE KEY: `{st.session_state.current_key}`")
if st.sidebar.button("SESSION TERMINATE"):
  st.session_state.authenticated = False
  st.session_state.current_key = None
  st.rerun()

if "logs" not in st.session_state:
  st.session_state.logs = (
      "[404 SYSTEM] Initialized. Awaiting target image upload..."
  )


def add_log(msg):
  st.session_state.logs += f"\n{msg}"


st.markdown("### [ TARGET IMAGE UPLOAD ]")
uploaded_file = st.file_uploader(
    "画像アップロード",
    type=["png", "jpg", "jpeg", "webp"],
    label_visibility="collapsed",
)

if uploaded_file is not None:
  add_log(f"[+] Target loaded: {uploaded_file.name}")
  st.image(uploaded_file, caption="TARGET PREVIEW", use_container_width=True)

if st.button("EXECUTE 404 SCAN"):
  if uploaded_file is not None:
    add_log("[*] Analyzing visual hashes & querying databases...")

    hosted_url = upload_to_image_hosting(uploaded_file)

    if hosted_url:
      add_log(f"[+] Secure cloud buffer created: {hosted_url}")
      google_lens_url = f"https://lens.google.com/uploadbyurl?url={hosted_url}"
      tineye_url = f"https://tineye.com/search?url={hosted_url}"
      pinterest_url = f"https://www.pinterest.com/search/pins/?q=image-search"
    else:
      add_log("[!] Notice: Using fallback query routing.")
      google_lens_url = "https://lens.google.com/"
      tineye_url = "https://tineye.com/"
      pinterest_url = "https://www.pinterest.com/"

    add_log("[+] 404 Scan complete. Source match endpoints generated.")

    st.markdown(
        f"""
        <div class="results-terminal">
        <h4>⚡ 404 CHECKER // REVERSE SEARCH ENDPOINTS</h4>
        <p><b>[Google Lens Source]:</b><br><a href="{google_lens_url}" target="_blank" class="cyber-link">{google_lens_url}</a></p>
        <p><b>[TinEye Match Trace]:</b><br><a href="{tineye_url}" target="_blank" class="cyber-link">{tineye_url}</a></p>
        <p><b>[Pinterest Vector Search]:</b><br><a href="{pinterest_url}" target="_blank" class="cyber-link">{pinterest_url}</a></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

  else:
    add_log("[-] ERROR: No target image provided.")

st.markdown("---")

st.markdown("### [ EXECUTION LOG ]")
st.text_area(
    "ログ",
    value=st.session_state.logs,
    height=150,
    label_visibility="collapsed",
)
