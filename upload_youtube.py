import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def generate_ai_caption(topic):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: return "Video Shorts", "#Shorts"
        
    genai.configure(api_key=api_key)
    
    # PROMPT CERDAS YANG BISA BERUBAH PERAN
    prompt = f"""
    Kamu adalah Content Creator YouTube profesional.
    Topik video hari ini adalah: "{topic}".
    
    Tugas: Buatkan Judul dan Deskripsi Shorts.
    
    PERAN KAMU (Sesuaikan dengan topik):
    - Jika topik tentang ALAM: Jadilah Travel Vlogger yang puitis.
    - Jika topik tentang ANIME/JEPANG: Jadilah 'Otaku' yang antusias, gunakan istilah wibu jika perlu.
    - Jika topik tentang SEPAKBOLA: Jadilah Komentator Bola yang penuh semangat dan hype.
    
    Format Output JSON: {{"title": "...", "description": "..."}}
    Syarat Judul: Clickbait, Max 60 karakter, Ada Emoji.
    Syarat Deskripsi: 2 kalimat seru + 3 hashtag relevan.
    """
    
    # Auto-Detect Model (Flash -> Pro)
    chosen_model = 'gemini-1.5-flash'
    try:
        genai.GenerativeModel(chosen_model).generate_content("test")
    except:
        chosen_model = 'gemini-pro'

    try:
        model = genai.GenerativeModel(chosen_model)
        response = model.generate_content(prompt)
        data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        return data['title'], data['description']
    except Exception as e:
        print(f"Error AI: {e}")
        return f"Amazing {topic} 🔥", f"Watch this cool video about {topic}. #Shorts"

def upload_video(file_path, topic):
    print(f"AI sedang menulis caption untuk: {topic}...")
    title_ai, desc_ai = generate_ai_caption(topic)
    print(f"Judul: {title_ai}")

    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    youtube = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title': title_ai,
            'description': desc_ai,
            'tags': ['Shorts', topic, 'Viral'],
            'categoryId': '22' # 17=Sports, 1=Film/Anime, tapi 22 (People & Blogs) aman untuk semua.
        },
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }

    youtube.videos().insert(
        part='snippet,status', body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    ).execute()
    print(f"🎉 SUKSES UPLOAD!")
