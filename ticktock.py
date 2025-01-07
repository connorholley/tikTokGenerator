import os
import torch
from diffusers import StableDiffusionPipeline
from PIL import Image
import io
from moviepy import ImageClip, concatenate_videoclips, AudioFileClip, TextClip, CompositeVideoClip, ColorClip, vfx
import tempfile
import numpy as np
from dotenv import load_dotenv
import uuid
import subprocess
import platform
import webbrowser
import requests

# Load environment variables from .env file
load_dotenv()

class LocalStableDiffusion:
    def __init__(self):
        self.pipe = None
        self.initialize_model()
    
    def initialize_model(self):
        """Initialize the Stable Diffusion model locally"""
        model_id = "runwayml/stable-diffusion-v1-5"  # You can change this to other models
        
        # Initialize the pipeline
        self.pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float32  # Use float32 for CPU-based operation
        )
        
        # Correctly disable the safety checker (returning two elements as expected by the pipeline)
        self.pipe.safety_checker = lambda images, **kwargs: (images, [False] * len(images))

        # Move the model to CPU (since MacBook Air doesn't have CUDA GPU)
        self.pipe = self.pipe.to("cpu")
        
        # Optional: Enable attention slicing for lower memory usage
        self.pipe.enable_attention_slicing()


    def generate_image(self, prompt, output_path):
        """Generate image using local Stable Diffusion and resize to TikTok dimensions"""
        try:
            # Generate the image
            image = self.pipe(
                prompt,
                height=512,  # Initial size for faster generation
                width=384,   # Initial size
                num_inference_steps=20,  # Lower number of steps for faster output
            ).images[0]
            
            # Resize the image to TikTok dimensions (1080x1920)
            tiktok_size = (1080, 1920)
            image_resized = image.resize(tiktok_size)
            
            # Generate unique filename
            unique_filename = os.path.join(output_path, f"{uuid.uuid4()}.png")
            
            # Save the resized image
            image_resized.save(unique_filename)
            
            return image_resized, unique_filename
            
        except Exception as e:
            print(f"Error generating image: {e}")
            return None, None


def generate_speech_elevenlabs(text):
    """Generate speech using ElevenLabs API"""
    api_key = os.getenv('ELEVENLABS_KEY')
    if not api_key:
        print("ElevenLabs API Key is not set.")
        return None
    
    url = "https://api.elevenlabs.io/v1/text-to-speech/N2lVS1w4EtoT3dr4eOWO" 
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.content
        else:
            print(f"Error: {response.status_code}")
            print(f"Response content: {response.text}")
            return None
    except Exception as e:
        print(f"Error generating speech: {e}")
        return None

def get_mac_font():
    font_paths = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSDisplay.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            return path
    
    return "/System/Library/Fonts/Helvetica.ttc"

def create_tiktok_video(text, background_music_path=None, output_path="output"):
    # Create an instance of the LocalStableDiffusion class
    local_sd = LocalStableDiffusion()
    
    # Ensure output directory exists
    output_path = os.path.expanduser(output_path)
    os.makedirs(output_path, exist_ok=True)
    
    sentences = text.split('.')
    clips = []
    temp_files = []
    
    # Setup background for text captions
    caption_bg = ColorClip((1080, 300), color=(0, 0, 0))
    caption_bg = caption_bg.with_opacity(0.7)
    
    # Get font for captions
    font_path = get_mac_font()
    
    # Process each sentence and generate corresponding content
    for i, sentence in enumerate(sentences):
        if not sentence.strip():
            continue
        
        try:
            # Create prompt for image generation
            prompt = f"Create a vertical format illustration of: {sentence[:200]}..."
            
            # Call the generate_image method from LocalStableDiffusion instance
            image, image_path = local_sd.generate_image(prompt, output_path)
            
            if image and image_path:
                temp_files.append(image_path)
                
                # Generate speech using ElevenLabs API
                audio_content = generate_speech_elevenlabs(sentence)
                if audio_content:
                    audio_path = os.path.join(output_path, f"audio_{uuid.uuid4()}.mp3")
                    with open(audio_path, 'wb') as f:
                        f.write(audio_content)
                    temp_files.append(audio_path)
                    
                    audio = AudioFileClip(audio_path)
                    image_clip = (ImageClip(image_path)
                                  .with_duration(audio.duration))
                    
                    # Create text caption for the sentence
                    txt_clip = (TextClip(text=sentence, 
                                       font_size=40,
                                       color='white',
                                       size=(1000, None),
                                       method='caption',
                                       font=font_path)
                               .with_position(('center', 'bottom'))
                               .with_duration(audio.duration))
                    
                    # Position background for captions
                    caption_bg_sized = (caption_bg
                                        .with_duration(audio.duration)
                                        .with_position(('center', 'bottom')))
                    
                    # Combine all clips into one video clip
                    video_clip = CompositeVideoClip([
                        image_clip,
                        caption_bg_sized,
                        txt_clip
                    ])
                    
                    # Set audio for the video clip
                    video_clip = video_clip.with_audio(audio)
                    clips.append(video_clip)
                
        except Exception as e:
            print(f"Error processing sentence {i+1}: {e}")
            continue
    
    # Combine all video clips into the final video
    if clips:
        final_video = concatenate_videoclips(clips)
        
        # Save final video
        output_file = os.path.join(output_path, f"tiktok_video_{uuid.uuid4()}.mp4")
        final_video.write_videofile(
            output_file,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            threads=os.cpu_count()
        )
        
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                os.remove(temp_file)
            except Exception as e:
                print(f"Error removing temporary file {temp_file}: {e}")
                
        return output_file
    
    return None

def get_user_input():
    print("\nEnter your text for the TikTok video (press Enter twice when done):")
    lines = []
    while True:
        line = input()
        if line:
            lines.append(line)
        elif lines:
            break
    return ' '.join(lines)

def open_video(video_path):
    try:
        if platform.system() == 'Darwin':
            subprocess.run(['open', video_path])
        elif platform.system() == 'Windows':
            os.startfile(video_path)
        else:
            subprocess.run(['xdg-open', video_path])
        return True
    except Exception as e:
        print(f"Error opening video: {e}")
        return False

def open_tiktok():
    webbrowser.open("https://www.tiktok.com/")

def handle_video_options(video_path):
    while True:
        print("\n=== Video Options ===")
        print("1. View video")
        print("2. Delete video")
        print("3. Keep video and return to main menu")
        
        choice = input("\nEnter your choice (1-3): ")
        
        if choice == "1":
            print("\nOpening video...")
            if open_video(video_path):
                print("Video opened in default player")
            else:
                print("Failed to open video")
                
        elif choice == "2":
            confirm = input("\nAre you sure you want to delete the video? (y/n): ")
            if confirm.lower() == 'y':
                try:
                    os.remove(video_path)
                    print("Video deleted successfully")
                    return
                except Exception as e:
                    print(f"Error deleting video: {e}")
            
        elif choice == "3":
            return
        
        else:
            print("\nInvalid choice. Please try again.")

def main():
    while True:
        print("\n=== TikTok Content Manager ===")
        print("1. Create new TikTok video")
        print("2. Open TikTok")
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
            open_tiktok()
        
        elif choice == "3":
            print("\nGoodbye!")
            break
        
        else:
            print("\nInvalid choice. Please try again.")

if __name__ == "__main__":
    main()
