# TikTok Content Manager

## Overview
The **TikTok Content Manager** is a Python application designed to streamline the creation of TikTok-ready videos. Using **Stable Diffusion** for image generation, **ElevenLabs** for text-to-speech synthesis, and **MoviePy** for video editing, the program allows users to create engaging content with minimal effort.

### Key Features
- **AI-Powered Image Generation**: Uses Stable Diffusion to create illustrations based on user-provided text.
- **Text-to-Speech**: Integrates with the ElevenLabs API for high-quality voiceovers.
- **Customizable Captions**: Adds text captions to videos with a dynamic background.
- **TikTok-Optimized Output**: Produces videos in a vertical format (1080x1920) ready for TikTok upload.
- **Interactive Video Management**: Provides options to view, delete, or keep generated videos.

---

## Requirements
### Hardware
- A machine with a CPU (CUDA GPU support is optional but not required).

### Software
- Python 3.8 or later
- Dependencies listed in `requirements.txt` (install using `pip install -r requirements.txt`).

### Environment Variables
- **ELEVENLABS_KEY**: API key for ElevenLabs (stored in a `.env` file).


