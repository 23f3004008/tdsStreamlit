import streamlit as st
from PIL import Image
import numpy as np
import os
from io import BytesIO
import requests
import urllib.parse
from streamlit_oauth import OAuth2Component

def is_lossless(original_img, compressed_bytes):
    compressed_img = Image.open(BytesIO(compressed_bytes))
    if original_img.mode != 'RGB':
        original_img = original_img.convert('RGB')
    if compressed_img.mode != 'RGB':
        compressed_img = compressed_img.convert('RGB')
    
    original_array = np.array(original_img)
    compressed_array = np.array(compressed_img)
    
    return np.array_equal(original_array, compressed_array)

# Set up OAuth2Component
client_id = st.secrets["GOOGLE_CLIENT_ID"]
client_secret = st.secrets["GOOGLE_CLIENT_SECRET"]
redirect_uri = st.secrets["REDIRECT_URI"]

oauth2 = OAuth2Component(
    client_id=client_id,
    client_secret=client_secret,
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token",
    redirect_uri=redirect_uri,
    scopes=["openid", "email", "profile"],
)

st.header("🔐 Google Authentication (Get your id_token)")

result = oauth2.authorize_button("Authenticate with Google")

if result and "token" in result:
    id_token = result["token"].get("id_token")
    access_token = result["token"].get("access_token")
    st.success("Authentication successful!")
    st.markdown("### Your id_token JSON (copy and submit):")
    st.code({
        "id_token": id_token,
        "access_token": access_token,
        "client_id": client_id
    }, language="json")
elif result and "error" in result:
    st.error(f"OAuth error: {result['error']}")

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
