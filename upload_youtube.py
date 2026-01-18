import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def upload_video(file_path):
    # Load credentials dari Environment Variable (GitHub Secrets)
    token_json = os.environ.get("YOUTUBE_TOKEN_JSON")
    
    if not token_json:
        raise Exception("Token YouTube tidak ditemukan di Secrets")

    # Konversi string JSON kembali ke Dictionary lalu ke Object Credentials
    creds_dict = json.loads(token_json)
    creds = Credentials.from_authorized_user_info(creds_dict)

    youtube = build('youtube', 'v3', credentials=creds)

    request_body = {
        'snippet': {
            'title': 'Saudi Arabia Hidden Gem #Nature #Shorts',
            'description': 'Beautiful nature scenery from Saudi Arabia. #SaudiArabia #Travel #Nature',
            'tags': ['Saudi Arabia', 'Nature', 'Shorts', 'Travel'],
            'categoryId': '22' # Category: People & Blogs
        },
        'status': {
            'privacyStatus': 'public', # Langsung publish
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

if __name__ == "__main__":
    upload_video("final_short.mp4")
