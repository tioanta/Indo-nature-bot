import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def generate_ai_caption(topic):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return f"Amazing View: {topic} 🌍 #Shorts", f"Beautiful nature scenery in {topic}. #Travel"
        
    genai.configure(api_key=api_key)
    
    # Prompt tetap sama
    prompt = f"""
    Kamu adalah Travel Influencer.
    Buatkan Judul dan Deskripsi YouTube Shorts tentang: {topic}.
    
    Aturan:
    1. Judul: Clickbait, Max 60 char, Emoji Bendera Negara.
    2. Deskripsi: 2 kalimat memuji keindahan.
    3. Hashtags: 3-5 tags relevan.
    4. Output WAJIB JSON murni: {{"title": "...", "description": "..."}}
    """
    
    # DAFTAR MODEL YANG AKAN DICOBA (Urutan Prioritas)
    # Jika yang pertama gagal, dia akan coba yang kedua, dst.
    models_to_try = [
        'gemini-1.5-flash',          # Paling Cepat & Baru
        'gemini-1.5-flash-latest',   # Versi Alternatif
        'gemini-pro'                 # Versi Lama (Paling Stabil/Cadangan)
    ]
    
    for model_name in models_to_try:
        try:
            print(f"   🤖 Mencoba AI Model: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            # Bersihkan hasil
            clean_text = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            print("   ✅ Sukses membuat caption!")
            return data['title'], data['description']
            
        except Exception as e:
            print(f"   ❌ Gagal dengan model {model_name}: {e}")
            continue # Lanjut coba model berikutnya
            
    # Jika semua model gagal (kiamat internet), pakai caption manual
    print("   ⚠️ Semua model AI gagal. Menggunakan caption manual.")
    return f"Wanderlust: {topic} ✈️ #Shorts", f"Explore the beauty of {topic}. #Nature #Travel"

def upload_video(file_path, topic):
    # 1. Generate Caption dengan sistem Anti-Error
    print(f"AI sedang menulis caption untuk: {topic}...")
    title_ai, desc_ai = generate_ai_caption(topic)
    
    print(f"Judul Final: {title_ai}")

    # 2. Upload ke YouTube
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    if not token_json:
        raise Exception("Token YouTube tidak ditemukan")

    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_dict)

    youtube = build('youtube', 'v3', credentials=creds)

    request_body = {
        'snippet': {
            'title': title_ai,
            'description': desc_ai,
            'tags': ['Travel', 'Nature', 'Shorts', topic, 'Wanderlust'],
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
    print(f"🎉 SUKSES! Video uploaded ID: {response['id']}")
