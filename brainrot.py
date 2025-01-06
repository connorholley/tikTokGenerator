import os
import requests
from PIL import Image
import io
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, TextClip, CompositeVideoClip, ColorClip, vfx
from gtts import gTTS
import tempfile
import numpy as np
from dotenv import load_dotenv
import uuid
import subprocess
import platform

# Load environment variables from .env file
load_dotenv()

def generate_image(prompt, output_path):
    """Generate image with a unique filename"""
    api_key = os.getenv('STABILITY_KEY')
    if not api_key:
        print("API Key is not set.")
        return None
    
    url = "https://api.stability.ai/v2beta/stable-image/generate/core"
    
    headers = {
        "authorization": f"Bearer {api_key}",
        "accept": "image/*",
    }
    
    data = {
        "prompt": prompt,
        "output_format": "png",
    }
    
    try:
        response = requests.post(url, headers=headers, files={"none": ''}, data=data)
        
        if response.status_code == 200:
            # Generate unique filename using UUID
            unique_filename = os.path.join(output_path, f"{uuid.uuid4()}.png")
            
            # Save the image with the unique filename
            with open(unique_filename, 'wb') as file:
                file.write(response.content)
            
            # Open and return the saved image
            image = Image.open(unique_filename)
            return image, unique_filename
        else:
            print(f"Error: {response.status_code}")
            print(f"Response content: {response.text}")
            return None, None
    except Exception as e:
        print(f"Error generating image: {e}")
        return None, None

def get_mac_font():
    font_paths = [
        "/System/Library/Fonts/SFNS.ttf",  # San Francisco (modern macOS)
        "/System/Library/Fonts/SFNSDisplay.ttf",  # San Francisco Display
        "/System/Library/Fonts/Helvetica.ttc",  # Helvetica
        "/Library/Fonts/Arial.ttf"  # Arial
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            return path
    
    # Fallback to a font we know exists on macOS
    return "/System/Library/Fonts/Helvetica.ttc"

def create_tiktok_video(text, background_music_path=None, output_path="output"):
    # Create output directory if it doesn't exist
    output_path = os.path.expanduser(output_path)  # Expand ~ if used
    os.makedirs(output_path, exist_ok=True)
    
    sentances = text.split('.')
    clips = []
    temp_files = []  # Keep track of temporary files
    
    # Create background for captions
    caption_bg = ColorClip((1080, 300), color=(0, 0, 0))
    caption_bg = caption_bg.with_opacity(0.7)
    
    # Get macOS specific font
    font_path = get_mac_font()
    
    for i, sentance in enumerate(sentances):
        if not sentance.strip():
            continue
        
        try:
            # Generate image with unique filename
            prompt = f"Create a vertical format illustration of: {sentance[:200]}..."
            image, image_path = generate_image(prompt, output_path)
            
            if image and image_path:
                temp_files.append(image_path)
                
                # Generate speech
                tts = gTTS(text=sentance, lang='en', tld='ie')
                audio_path = os.path.join(output_path, f"audio_{uuid.uuid4()}.mp3")
                tts.save(audio_path)
                temp_files.append(audio_path)
                
                # Create video elements
                audio = AudioFileClip(audio_path)
                image_clip = (ImageClip(image_path)
                            #  .resize(width=1080)  # TikTok width
                             .with_duration(audio.duration))
                
                # Add captions with macOS font
                txt_clip = (TextClip(text=sentance, 
                                   font_size=40,
                                   color='white',
                                   size=(1000, None),
                                   method='caption',
                                   font=font_path)
                           .with_position(('center', 'bottom'))
                           .with_duration(audio.duration))
                
                # Combine image and captions
                caption_bg_sized = (caption_bg
                                  .with_duration(audio.duration)
                                  .with_position(('center', 'bottom')))
                
                video_clip = CompositeVideoClip([
                    image_clip,
                    caption_bg_sized,
                    txt_clip
                ])
                
                video_clip = video_clip.with_audio(audio)
                clips.append(video_clip)
                
        except Exception as e:
            print(f"Error processing sentance {i+1}: {e}")
            continue
    
    # Combine all clips
# Combine all clips
    if clips:
        final_video = concatenate_videoclips(clips)
        
        # Export in TikTok format without background music
        output_file = os.path.join(output_path, f"tiktok_video_{uuid.uuid4()}.mp4")
        final_video.write_videofile(
            output_file,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            threads=os.cpu_count()
        )
        
        # Cleanup temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Error removing temporary file {temp_file}: {e}")
                
        return output_file
    
    return None

# Example usage

def view_tiktok_stats():
    """View TikTok profile statistics using TikTok API"""
    print("got tick tock stats")

def get_user_input():
    """Get text input from user for video creation"""
    print("\nEnter your text for the TikTok video (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        elif lines:  # Empty line and we have content
            break
    return ' '.join(lines)


def open_video(video_path):
    """Open video with default system video player"""
    try:
        if platform.system() == 'Darwin':       # macOS
            subprocess.run(['open', video_path])
        elif platform.system() == 'Windows':     # Windows
            os.startfile(video_path)
        else:                                   # Linux
            subprocess.run(['xdg-open', video_path])
        return True
    except Exception as e:
        print(f"Error opening video: {e}")
        return False

def post_to_tiktok(video_path):
    """Post video to TikTok using TikTok API"""
    print("video posted to tiktok")

def handle_video_options(video_path):
    """Handle post-creation video options"""
    while True:
        print("\n=== Video Options ===")
        print("1. View video")
        print("2. Post to TikTok")
        print("3. Delete video")
        print("4. Keep video and return to main menu")
        
        choice = input("\nEnter your choice (1-4): ")
        
        if choice == "1":
            print("\nOpening video...")
            if open_video(video_path):
                print("Video opened in default player")
            else:
                print("Failed to open video")
                
        elif choice == "2":
            print("\nPosting to TikTok...")
            if post_to_tiktok(video_path):
                print("Would you like to keep the local copy?")
                if input("Enter 'y' to keep or any other key to delete: ").lower() != 'y':
                    os.remove(video_path)
                    print("Local video file deleted")
                return
            
        elif choice == "3":
            confirm = input("\nAre you sure you want to delete the video? (y/n): ")
            if confirm.lower() == 'y':
                try:
                    os.remove(video_path)
                    print("Video deleted successfully")
                    return
                except Exception as e:
                    print(f"Error deleting video: {e}")
            
        elif choice == "4":
            return
        
        else:
            print("\nInvalid choice. Please try again.")

def main():
    while True:
        print("\n=== TikTok Content Manager ===")
        print("1. Create new TikTok video")
        print("2. View profile statistics")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            text = get_user_input()
            if text:
                print("\nCreating video...")
                output_video = create_tiktok_video(text)
                if output_video:
                    print(f"\nVideo created successfully: {output_video}")
                    handle_video_options(output_video)
        
        elif choice == "2":
            view_tiktok_stats()
        
        elif choice == "3":
            print("\nGoodbye!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()
    