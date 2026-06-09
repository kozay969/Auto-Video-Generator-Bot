#!/usr/bin/env python3
"""
Step 3: FFmpeg + Pillow သုံးပြီး Video ထုတ်မည်
Background images + subtitle text + audio
"""

import json
import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont
import math


# Video settings
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 9:16 vertical (phone-friendly)
FPS = 24
BG_COLOR = (15, 15, 30)       # Dark blue-black
ACCENT_COLOR = (99, 102, 241)  # Indigo
TEXT_COLOR = (255, 255, 255)   # White
SUBTITLE_BG = (0, 0, 0, 180)  # Semi-transparent black


def create_background_frame(width: int, height: int, frame_num: int, total_frames: int) -> Image.Image:
    """Animated gradient background ဖန်တီးမည်"""
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Animated gradient effect
    progress = frame_num / max(total_frames, 1)
    
    # Draw gradient circles (pulsing effect)
    for i in range(3):
        offset = math.sin(progress * 2 * math.pi + i * 2.1) * 50
        cx = width // 2 + int(offset)
        cy = height // 3 + int(offset * 0.5)
        radius = 400 + int(math.sin(progress * 2 * math.pi + i) * 50)
        
        colors = [
            (30, 20, 60),
            (20, 40, 80),
            (10, 30, 70),
        ]
        
        x0 = cx - radius
        y0 = cy - radius
        x1 = cx + radius
        y1 = cy + radius
        
        draw.ellipse([x0, y0, x1, y1], fill=colors[i])
    
    return img


def create_title_frame(title: str, width: int, height: int) -> Image.Image:
    """Title card ဖန်တီးမည်"""
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Gradient background
    for y in range(height):
        ratio = y / height
        r = int(BG_COLOR[0] + (ACCENT_COLOR[0] - BG_COLOR[0]) * ratio * 0.3)
        g = int(BG_COLOR[1] + (ACCENT_COLOR[1] - BG_COLOR[1]) * ratio * 0.3)
        b = int(BG_COLOR[2] + (ACCENT_COLOR[2] - BG_COLOR[2]) * ratio * 0.3)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Decorative lines
    for i in range(5):
        y_pos = height // 4 + i * 3
        draw.line([(width//4, y_pos), (3*width//4, y_pos)], fill=ACCENT_COLOR, width=2)
    
    # Load font (fallback to default)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Channel branding
    draw.text((width//2, height//3), "▶ AUTO VIDEO", font=font_small, 
              fill=ACCENT_COLOR, anchor="mm")
    
    # Title (wrap long text)
    wrapped = textwrap.wrap(title, width=18)
    y_start = height // 2 - len(wrapped) * 40
    
    for line in wrapped:
        draw.text((width//2, y_start), line, font=font_large,
                  fill=TEXT_COLOR, anchor="mm")
        y_start += 80
    
    return img


def create_subtitle_overlay(img: Image.Image, text: str, width: int, height: int) -> Image.Image:
    """Subtitle text overlay ထည့်မည်"""
    img = img.copy()
    
    if not text.strip():
        return img
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
    except:
        font = ImageFont.load_default()
    
    # Word wrap
    wrapped_lines = textwrap.wrap(text, width=22)
    if not wrapped_lines:
        return img
    
    # Keep only last 2 lines for readability
    display_lines = wrapped_lines[-2:]
    
    line_height = 55
    total_text_height = len(display_lines) * line_height + 30
    
    # Position: bottom 1/4 of screen
    text_y = int(height * 0.75)
    
    # Semi-transparent background
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    max_line_width = max([font.getlength(line) for line in display_lines]) + 60
    bg_x = (width - max_line_width) // 2
    
    overlay_draw.rounded_rectangle(
        [bg_x, text_y - 15, bg_x + max_line_width, text_y + total_text_height],
        radius=12,
        fill=(0, 0, 0, 180)
    )
    
    img = img.convert('RGBA')
    img = Image.alpha_composite(img, overlay)
    img = img.convert('RGB')
    
    draw = ImageDraw.Draw(img)
    
    for i, line in enumerate(display_lines):
        y = text_y + i * line_height
        # Shadow
        draw.text((width//2 + 2, y + 2), line, font=font, fill=(0, 0, 0), anchor="mm")
        # Main text
        draw.text((width//2, y), line, font=font, fill=TEXT_COLOR, anchor="mm")
    
    return img


def generate_frames(script_data: dict, audio_duration: float, output_dir: str):
    """Video frames များ ထုတ်မည်"""
    os.makedirs(output_dir, exist_ok=True)
    
    total_frames = int(audio_duration * FPS)
    title = script_data.get("title", "Video")
    full_script = script_data.get("full_script", "")
    
    print(f"🎞️ {total_frames} frames ထုတ်မည် ({audio_duration:.1f}s @ {FPS}fps)")
    
    # Split script into timed chunks for subtitles
    words = full_script.split()
    words_per_frame = max(1, len(words) / total_frames)
    
    # Title card (first 3 seconds)
    title_frames = FPS * 3
    
    for frame_num in range(total_frames):
        frame_path = f"{output_dir}/frame_{frame_num:06d}.png"
        
        if frame_num < title_frames:
            # Title card
            img = create_title_frame(title, VIDEO_WIDTH, VIDEO_HEIGHT)
        else:
            # Content frame with background
            img = create_background_frame(
                VIDEO_WIDTH, VIDEO_HEIGHT, 
                frame_num - title_frames,
                total_frames - title_frames
            )
            
            # Calculate subtitle text
            content_frame = frame_num - title_frames
            word_start = int(content_frame * words_per_frame)
            word_end = min(word_start + 15, len(words))
            
            if word_start < len(words):
                subtitle_text = " ".join(words[word_start:word_end])
                img = create_subtitle_overlay(img, subtitle_text, VIDEO_WIDTH, VIDEO_HEIGHT)
        
        img.save(frame_path, quality=85, optimize=True)
        
        if frame_num % (FPS * 10) == 0:
            print(f"  📸 Frame {frame_num}/{total_frames} ({frame_num*100//total_frames}%)")
    
    print(f"✅ {total_frames} frames ထုတ်ပြီး")
    return total_frames


def main():
    print("🎬 Video ဖန်တီးနေသည်...")
    
    # Load data
    with open("output/script_data.json", "r", encoding="utf-8") as f:
        script_data = json.load(f)
    
    with open("output/audio_info.json", "r") as f:
        audio_info = json.load(f)
    
    audio_duration = audio_info["duration"]
    audio_path = audio_info["path"]
    
    print(f"🎵 Audio duration: {audio_duration:.1f}s")
    
    frames_dir = "output/frames"
    
    # Generate frames
    generate_frames(script_data, audio_duration, frames_dir)
    
    # Combine frames + audio with FFmpeg
    print("🔗 Video + Audio ပေါင်းစပ်နေသည်...")
    
    output_video = "output/final_video.mp4"
    
    subprocess.run([
        'ffmpeg', '-y',
        '-framerate', str(FPS),
        '-i', f'{frames_dir}/frame_%06d.png',
        '-i', audio_path,
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-shortest',
        '-movflags', '+faststart',
        '-pix_fmt', 'yuv420p',
        output_video
    ], check=True)
    
    # Get file size
    size_mb = os.path.getsize(output_video) / (1024 * 1024)
    print(f"✅ Video ထုတ်ပြီး: {output_video} ({size_mb:.1f} MB)")
    
    # Save video info
    with open("output/video_info.json", "w") as f:
        json.dump({
            "path": output_video,
            "duration": audio_duration,
            "size_mb": size_mb,
            "title": script_data.get("title", ""),
        }, f)


if __name__ == "__main__":
    main()
    
