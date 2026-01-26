import os
import json
import google.generativeai as genai
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_manual_caption(topic):
    """Context-aware fallback caption tanpa API"""
    topic_lower = topic.lower()
    
    if "manchester" in topic_lower:
        title = "Glory Glory Man United! 🔴 #Shorts"
        desc = "Semangat legendaris Old Trafford! 🏟️ Saksikan keajaiban sepak bola di stadion paling ikonik. #ManUnited #Football #Shorts"
    elif "masjid" in topic_lower or "makkah" in topic_lower:
        title = "Keindahan Masjidil Haram 🕌 #Shorts"
        desc = "Saksikan kemegahan rumah Allah yang penuh berkah. Subhanallah! 💫 #Islam #Makkah #Shorts"
    elif "japan" in topic_lower or "tokyo" in topic_lower:
        title = "Tokyo Aesthetic ✨ #Shorts"
        desc = "Keajaiban Jepang yang memukau mata. Modern dan tradisional berpadu indah. 🗾 #Japan #Travel #Shorts"
    elif "kyoto" in topic_lower:
        title = "Kyoto Culture 🏮 #Shorts"
        desc = "Jelajahi keindahan budaya Kyoto yang abadi. Setiap detail berbicara sejarah. 🌸 #Kyoto #Japan #Shorts"
    else:
        title = f"{topic} Amazing Content 🎬 #Shorts"
        desc = f"Jangan lewatkan keindahan {topic}! Subscribe untuk lebih banyak konten menarik. 🌟 #Shorts #Content"
    
    return title, desc

def generate_caption(topic):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print(f"   ⚠️ GEMINI_API_KEY tidak ditemukan, gunakan caption fallback")
        return get_manual_caption(topic)
    
    genai.configure(api_key=api_key)
    
    print(f"   🤖 Gemini: Membuat Caption Shorts untuk {topic}...")
    
    # Auto-detect available model
    try:
        all_models = list(genai.list_models())
        valid_models = [m.name for m in all_models if 'generateContent' in m.supported_generation_methods]
        
        # Try priority: gemini-2.0-flash > gemini-1.5-flash > gemini-pro > first available
        chosen_model = None
        for priority_model in ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-pro', 'gemini-1.0-pro']:
            for m in valid_models:
                if priority_model in m:
                    chosen_model = m
                    break
            if chosen_model:
                break
        
        if not chosen_model and valid_models:
            chosen_model = valid_models[0]
        
        if not chosen_model:
            print("   ⚠️ Tidak ada model yang tersedia, gunakan fallback")
            return get_manual_caption(topic)
        
        print(f"   Using model: {chosen_model}")
        model = genai.GenerativeModel(chosen_model)
    except Exception as e:
        print(f"   ⚠️ Error detect model: {e}, gunakan fallback")
        return get_manual_caption(topic)
    
    prompt = f"""
    Kamu adalah expert YouTube Shorts. Buatkan Metadata untuk video pendek tentang: "{topic}".
    
    Gaya Bahasa:
    - Jika tentang Manchester United: Semangat, Fanatik, Glory Glory Man Utd.
    - Jika tentang Masjidil Haram: Islami, Menyejukkan hati, Masya Allah.
    - Jika tentang Japan: Aesthetic, Vibe tenang, Travel goals.
    
    Output JSON WAJIB:
    {{
        "title": "Judul clickbait pendek (<50 char) + #Shorts",
        "description": "Caption menarik 2 kalimat ajakan + 3-4 hashtags relevan"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(text)
        print(f"   ✅ Caption generated successfully")
        return data['title'], data['description']
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "429" in error_msg:
            print(f"   ⚠️ Gemini quota exceeded, gunakan caption fallback")
        else:
            print(f"   ⚠️ Generate caption error: {e}")
        return get_manual_caption(topic)

def upload_video(file_path, topic):
    title, desc = generate_caption(topic)
    print(f"   Judul: {title}")
    
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    creds = Credentials.from_authorized_user_info(json.loads(token_json))
    youtube = build('youtube', 'v3', credentials=creds)

    body = {
        'snippet': {
            'title': title,
            'description': desc,
            'tags': ["Shorts", "Vertical", "Vibes", topic],
            'categoryId': '10' # Music/Entertainment
        },
        'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
    }

    youtube.videos().insert(
        part='snippet,status', body=body,
        media_body=MediaFileUpload(file_path, chunksize=-1, resumable=True)
    ).execute()
