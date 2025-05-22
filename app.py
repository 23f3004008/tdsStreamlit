import streamlit as st
from PIL import Image
import numpy as np
import os
from io import BytesIO
import requests
import urllib.parse
from streamlit_google_auth import Authenticate

# --- Google Auth Section ---

st.title('Streamlit Google Auth Example')

authenticator = Authenticate(
    secret_credentials_path='google_credentials.json',
    cookie_name='my_cookie_name',
    cookie_key='this_is_secret',
    redirect_uri=os.environ.get('REDIRECT_URI', 'http://localhost:8501'),
)

# Catch the login event
authenticator.check_authentification()

# Create the login button
authenticator.login()

if st.session_state.get('connected'):
    st.image(st.session_state['user_info'].get('picture'))
    st.write('Hello, '+ st.session_state['user_info'].get('name'))
    st.write('Your email is '+ st.session_state['user_info'].get('email'))
    st.write('Your id: ' + str(st.session_state.get('oauth_id')))
    st.write('Raw user info:')
    st.code(st.session_state['user_info'], language='json')
    if st.button('Log out'):
        authenticator.logout()

# --- Lossless Image Compressor Section ---

def is_lossless(original_img, compressed_bytes):
    compressed_img = Image.open(BytesIO(compressed_bytes))
    if original_img.mode != 'RGB':
        original_img = original_img.convert('RGB')
    if compressed_img.mode != 'RGB':
        compressed_img = compressed_img.convert('RGB')
    
    original_array = np.array(original_img)
    compressed_array = np.array(compressed_img)
    
    return np.array_equal(original_array, compressed_array)

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
