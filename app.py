import streamlit as st
from PIL import Image
import numpy as np
import os
from io import BytesIO
import requests
import urllib.parse
from dotenv import load_dotenv

def is_lossless(original_img, compressed_bytes):
    compressed_img = Image.open(BytesIO(compressed_bytes))
    if original_img.mode != 'RGB':
        original_img = original_img.convert('RGB')
    if compressed_img.mode != 'RGB':
        compressed_img = compressed_img.convert('RGB')
    
    original_array = np.array(original_img)
    compressed_array = np.array(compressed_img)
    
    return np.array_equal(original_array, compressed_array)

load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8501/")

def get_auth_url():
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": REDIRECT_URI,
        "access_type": "offline",
        "prompt": "consent"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    resp = requests.post("https://oauth2.googleapis.com/token", data=data)
    return resp.json()

# --- Google OAuth2 Section ---
st.header("🔐 Google Authentication (Get your id_token)")

if "auth_code" not in st.session_state and "id_token" not in st.session_state:
    st.markdown("1. Click the button below to authenticate with Google.")
    auth_url = get_auth_url()
    st.markdown(f"[Authenticate with Google]({auth_url})", unsafe_allow_html=True)

    st.markdown("""
    2. After logging in, you'll be redirected to a URL like `http://localhost:8501/?code=...`.
    3. Copy the `code` value from the URL and paste it below:
    """)
    code_input = st.text_input("Paste the code from the URL here")

    if st.button("Exchange code for id_token") and code_input:
        token_data = exchange_code_for_token(code_input)
        if "id_token" in token_data:
            st.session_state["id_token"] = token_data["id_token"]
            st.session_state["client_id"] = GOOGLE_CLIENT_ID
            st.success("Authentication successful!")
        else:
            st.error(f"Failed to get id_token: {token_data}")

if "id_token" in st.session_state:
    result_json = {
        "id_token": st.session_state["id_token"],
        "client_id": st.session_state["client_id"]
    }
    st.markdown("### Your id_token JSON (copy and submit):")
    st.code(result_json, language="json")
    st.button("Clear Authentication", on_click=lambda: st.session_state.clear())

st.title("📷 Lossless Image Compressor (WebP ≤ 400 bytes)")

uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg"])

if uploaded_file:
    img = Image.open(uploaded_file)
    st.image(img, caption="Original Image", use_column_width=True)

    if img.mode != 'RGB':
        img = img.convert('RGB')

    base_name = os.path.splitext(uploaded_file.name)[0]
    output_path = f"{base_name}_lossless.webp"

    # Compress to WebP losslessly
    buffer = BytesIO()
    try:
        img.save(buffer, format="WEBP", lossless=True, quality=100)
        compressed_bytes = buffer.getvalue()
        compressed_size = len(compressed_bytes)

        st.write(f"📦 Compressed size: {compressed_size} bytes")

        if compressed_size <= 400 and is_lossless(img, compressed_bytes):
            st.success("✅ Compression is lossless and ≤ 400 bytes!")
            st.download_button("📥 Download Compressed Image", compressed_bytes, output_path, mime="image/webp")
        else:
            st.error("❌ Compression failed to meet requirements.\n\nTry using a smaller/simpler image or a different format.")
            st.info("💡 Ask in the group for help if needed.")
    except Exception as e:
        st.error(f"❌ An error occurred during compression: {e}")
