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
    """Get system font path for macOS"""
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
    
    paragraphs = text.split('\n\n')
    clips = []
    temp_files = []  # Keep track of temporary files
    
    # Create background for captions
    caption_bg = ColorClip((1080, 300), color=(0, 0, 0))
    caption_bg = caption_bg.with_opacity(0.7)
    
    # Get macOS specific font
    font_path = get_mac_font()
    
    for i, paragraph in enumerate(paragraphs):
        if not paragraph.strip():
            continue
        
        try:
            # Generate image with unique filename
            prompt = f"Create a vertical format illustration of: {paragraph[:200]}..."
            image, image_path = generate_image(prompt, output_path)
            
            if image and image_path:
                temp_files.append(image_path)
                
                # Generate speech
                tts = gTTS(text=paragraph, lang='en', tld='co.in')
                audio_path = os.path.join(output_path, f"audio_{uuid.uuid4()}.mp3")
                tts.save(audio_path)
                temp_files.append(audio_path)
                
                # Create video elements
                audio = AudioFileClip(audio_path)
                image_clip = (ImageClip(image_path)
                            #  .resize(width=1080)  # TikTok width
                             .with_duration(audio.duration))
                
                # Add captions with macOS font
                txt_clip = (TextClip(text=paragraph, 
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
            print(f"Error processing paragraph {i+1}: {e}")
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
if __name__ == "__main__":
    text = """Am I Overreacting?

Okay, so here's the deal: I work with this super talented software developer named Nicholas Palichuk. He's honestly one of the cutest people I've ever met—like, he's got that perfect mix of brainy and adorable. And every time I see him working on code, I can’t help but get a little distracted. 🧑‍💻💖

I know I should be focused on my own work, but there’s something about the way he codes (seriously, he’s fast and efficient) and the way he casually cracks jokes during team meetings that just makes my heart skip a beat. Plus, he always seems so approachable and friendly, and I’m starting to think I might have a little crush on him... or maybe it's just admiration for his programming skills? 🤔

But, here’s where I’m unsure—whenever I catch myself staring at him (totally not on purpose, I swear!), I feel like I might be overthinking it. Does anyone else get distracted by cute colleagues, or is it just me? And is it okay to have a little crush on someone at work, or should I just focus on being a professional and stop daydreaming about pairing with him on a project?

I mean, he’s honestly so cute that even his pull requests are adorable. 😅
"""
    
    # Example with path that might include ~
    output_video = create_tiktok_video(text, 'what_is_love.mp3')
    if output_video:
        print(f"Video created successfully: {output_video}")