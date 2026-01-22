import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def generate_ai_caption(topic):
    # Setup Gemini
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # Fallback jika lupa pasang API Key
        return "Saudi Arabia Hidden Gem 🇸🇦 #Shorts", "Beautiful nature in Saudi Arabia. #Travel"
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Kamu adalah Social Media Manager profesional.
    Buatkan Judul (Title) dan Deskripsi untuk YouTube Shorts tentang pemandangan: '{topic}' di Arab Saudi.
    
    Syarat:
    1. Judul: Maksimal 60 karakter, Clickbait, Menarik, ada Emoji. Bahasa Indonesia campur Inggris.
    2. Deskripsi: Singkat (2 kalimat), estetik, mengajak orang berkunjung. Sertakan 5 hashtags relevan.
    3. Output WAJIB format JSON murni: {{"title": "...", "description": "..."}}
    """

    try:
        response = model.generate_content(prompt)
        # Bersihkan format markdown ```json jika ada
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data['title'], data['description']
    except Exception as e:
        print(f"Error AI: {e}")
        return f"Amazing {topic} in Saudi Arabia 🇸🇦", "#SaudiArabia #Nature #Shorts"

def upload_video(file_path, topic="Saudi Arabia Nature"):
    # 1. Generate Caption Dulu
    print(f"Sedang meminta AI membuat caption untuk topik: {topic}...")
    title_ai, desc_ai = generate_ai_caption(topic)
    
    print(f"Judul: {title_ai}")
    print(f"Deskripsi: {desc_ai}")

    # 2. Proses Upload
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_json:
        raise Exception("Token YouTube tidak ditemukan di Secrets")

    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_dict)

    youtube = build('youtube', 'v3', credentials=creds)

    request_body = {
        'snippet': {
            'title': title_ai,
            'description': desc_ai,
            'tags': ['Saudi Arabia', 'Travel', 'Shorts', topic],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    request = youtube.videos().insert(
        part='snippet,status',
        body=request_body,
        media_body=media
    )

    response = request.execute()
    print(f"Video uploaded! ID: {response['id']}")
