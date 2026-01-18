import generate_video
import upload_youtube
import os

def main():
    print("1. Mencari dan Memproses Video...")
    raw_video = generate_video.get_pexels_video(query="Saudi Arabia Desert Nature")
    
    if raw_video:
        final_video = generate_video.process_video(raw_video)
        
        print("2. Mengupload ke YouTube...")
        upload_youtube.upload_video(final_video)
        
        print("Selesai! Video tayang.")
    else:
        print("Gagal mendapatkan video.")

if __name__ == "__main__":
    main()
