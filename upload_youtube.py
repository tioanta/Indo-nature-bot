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
        return f"Amazing View: {topic} 🌍 #Shorts", f"Beautiful nature scenery in {topic}. #Travel"
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Prompt dinamis yang mengikuti topik negara
    prompt = f"""
    Kamu adalah Travel Influencer profesional.
    Buatkan Judul dan Deskripsi YouTube Shorts untuk video pemandangan tentang: '{topic}'.
    
    Aturan:
    1. Judul: Bikin penasaran (Clickbait), Max 60 karakter, Gunakan Emoji bendera negara tersebut.
    2. Deskripsi: 2 kalimat singkat yang memuji keindahan tempat itu. Bahasa Indonesia mix Inggris gaul.
    3. Hashtags: Berikan 3-5 hashtag relevan (nama negara, nama tempat, #Travel).
    4. Output WAJIB JSON murni: {{"title": "...", "description": "..."}}
    """
    
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_text)
        return data['title'], data['description']
    except Exception as e:
        print(f"Error AI: {e}")
        # Fallback caption jika AI error
        return f"Wanderlust: {topic} ✈️ #Shorts", f"Explore the beauty of {topic}. #Nature #Travel"

def upload_video(file_path, topic):
    # 1. Minta AI bikin caption sesuai topik negara
    print(f"AI sedang menulis caption untuk: {topic}...")
    title_ai, desc_ai = generate_ai_caption(topic)
    
    print(f"Judul: {title_ai}")

    # 2. Upload
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
            'categoryId': '22' # People & Blogs
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
    print(f"Sukses! Video uploaded ID: {response['id']}")
