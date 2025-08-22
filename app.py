import os
import sys
import tempfile
import subprocess
import time
import json
import threading
import uuid
import re
from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Global dictionary to store task status and results
tasks = {}

def check_package(package_name):
    """Check if a package is installed"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed and accessible"""
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_audio_with_ytdlp(youtube_url, task_id):
    """Download audio using yt-dlp with flexible format options"""
    import yt_dlp
    
    temp_dir = tempfile.gettempdir()
    base_filename = f"audio_{task_id}"
    output_template = os.path.join(temp_dir, f"{base_filename}.%(ext)s")
    
    # Try multiple format options in order of preference
    format_options = [
        'bestaudio/best',  # Best audio quality
        '140',  # m4a audio
        '251',  # webm audio
        '171',  # webm audio (high quality)
        'worstaudio'  # Worst audio quality (fallback)
    ]
    
    for format_option in format_options:
        try:
            ydl_opts = {
                'format': format_option,
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'keepvideo': False,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
            # Get video metadata
            title = info.get('title', 'Unknown Title')
            author = info.get('uploader', 'Unknown Author')
            description = info.get('description', '')
            length = info.get('duration', 0)
            views = info.get('view_count', 0)
            watch_url = info.get('webpage_url', youtube_url)
            
            # Find the actual downloaded file
            possible_files = [
                os.path.join(temp_dir, f"{base_filename}.mp3"),
                os.path.join(temp_dir, f"{base_filename}.mp3.mp3"),
                os.path.join(temp_dir, f"{base_filename}.webm"),
                os.path.join(temp_dir, f"{base_filename}.m4a")
            ]
            
            audio_file = None
            for file_path in possible_files:
                if os.path.exists(file_path):
                    audio_file = file_path
                    break
            
            if not audio_file:
                # If none of the expected files exist, try to find any file with our base name
                for file in os.listdir(temp_dir):
                    if file.startswith(base_filename) and file.endswith(('.mp3', '.webm', '.m4a')):
                        audio_file = os.path.join(temp_dir, file)
                        break
            
            if not audio_file:
                raise Exception("Could not find the downloaded audio file")
            
            # If the file has a double extension, rename it
            if audio_file.endswith('.mp3.mp3'):
                new_path = audio_file[:-4]  # Remove the last .mp3
                os.rename(audio_file, new_path)
                audio_file = new_path
            
            # Create a simple YouTube-like object for compatibility
            class SimpleYouTube:
                def __init__(self):
                    self.title = title
                    self.author = author
                    self.description = description
                    self.length = length
                    self.views = views
                    self.watch_url = watch_url
                    
            print(f"Successfully downloaded audio using format: {format_option}")
            return SimpleYouTube(), audio_file
                
        except Exception as e:
            print(f"Failed with format {format_option}: {str(e)}")
            continue
    
    # If all formats failed, raise an error
    raise Exception("Could not download audio with any available format")

def download_video_with_ytdlp(youtube_url, task_id):
    """Download video using yt-dlp with flexible format options"""
    import yt_dlp
    
    temp_dir = tempfile.gettempdir()
    base_filename = f"video_{task_id}"
    output_template = os.path.join(temp_dir, f"{base_filename}.%(ext)s")
    
    # Try multiple format options in order of preference
    format_options = [
        'best[ext=mp4]',  # Best quality MP4
        'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',  # Best video and audio separately
        'best[ext=webm]',  # Best quality WebM
        'best',  # Best available regardless of format
        'worst'  # Worst quality (fallback)
    ]
    
    for format_option in format_options:
        try:
            ydl_opts = {
                'format': format_option,
                'outtmpl': output_template,
                'quiet': True,
                'no_warnings': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                
            # Find the actual downloaded file
            possible_files = [
                os.path.join(temp_dir, f"{base_filename}.mp4"),
                os.path.join(temp_dir, f"{base_filename}.mkv"),
                os.path.join(temp_dir, f"{base_filename}.webm"),
                os.path.join(temp_dir, f"{base_filename}.flv"),
                os.path.join(temp_dir, f"{base_filename}.mov")
            ]
            
            video_file = None
            for file_path in possible_files:
                if os.path.exists(file_path):
                    video_file = file_path
                    break
            
            if not video_file:
                # If none of the expected files exist, try to find any file with our base name
                for file in os.listdir(temp_dir):
                    if file.startswith(base_filename):
                        video_file = os.path.join(temp_dir, file)
                        break
            
            if video_file:
                print(f"Successfully downloaded video using format: {format_option}")
                return video_file
                
        except Exception as e:
            print(f"Failed with format {format_option}: {str(e)}")
            continue
    
    # If all formats failed, raise an error
    raise Exception("Could not download video with any available format")

def extract_video_clip(video_file, start_time, duration=60, task_id=None):
    """Extract a clip from the video using ffmpeg"""
    # Create a permanent location for the clip
    if task_id:
        output_dir = os.path.join(os.getcwd(), 'static', 'videos')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"video_clip_{task_id}.mp4")
    else:
        output_file = os.path.join(os.path.dirname(video_file), "video_clip.mp4")
    
    # Extract the clip
    cmd = [
        'ffmpeg', '-i', video_file, '-ss', str(start_time), '-t', str(duration),
        '-c:v', 'copy', '-c:a', 'copy', output_file
    ]
    subprocess.run(cmd, check=True)
    
    return output_file

def generate_best_linkedin_post(transcript, summary, video_info):
    """Generate the best LinkedIn post using AI"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.9  # Higher creativity for best content
    )
    
    prompt = f"""
    You are a top-tier LinkedIn content creator specializing in viral professional content.
    Create the most engaging LinkedIn post possible based on the following video transcript and summary.
    
    Video Title: {video_info.title}
    Channel: {video_info.author}
    Video URL: {video_info.watch_url}
    
    Summary:
    {summary}
    
    Transcript (for reference):
    {transcript[:5000]}
    
    Create the absolute best LinkedIn post by following these guidelines:
    1. Start with an irresistible hook that grabs attention immediately
    2. Use storytelling techniques to make it compelling
    3. Include 3-5 of the most impactful insights from the video
    4. Add relevant statistics or surprising facts if applicable
    5. Make it thought-provoking and conversation-starting
    6. Include 5-7 highly relevant hashtags at the end
    7. Add a strong call to action to watch the full video
    8. Keep it under 3000 characters
    9. Use formatting (line breaks, emojis) to enhance readability
    10. Make it shareable and comment-worthy
    
    This should be your absolute best work - the kind of post that gets thousands of views and engagements.
    """
    
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content

def generate_best_twitter_thread(transcript, summary, video_info):
    """Generate the best Twitter thread using AI"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.9
    )
    
    prompt = f"""
    You are a master Twitter content creator specializing in viral threads.
    Create the most engaging Twitter thread possible based on the following video transcript and summary.
    
    Video Title: {video_info.title}
    Channel: {video_info.author}
    Video URL: {video_info.watch_url}
    
    Summary:
    {summary}
    
    Transcript (for reference):
    {transcript[:5000]}
    
    Create the absolute best Twitter thread by following these guidelines:
    1. Create a thread of exactly 7 tweets (each under 280 characters)
    2. Start with a powerful hook in the first tweet that makes people stop scrolling
    3. Each tweet should build on the previous one, creating a narrative flow
    4. Include 1-2 relevant emojis per tweet for visual appeal
    5. Add 2-3 relevant hashtags per tweet
    6. Use suspense, curiosity, and surprise throughout the thread
    7. Include a strong call to action in the last tweet
    8. Make it highly shareable and retweetable
    9. Format each tweet clearly with "Tweet 1/7:", "Tweet 2/7:", etc.
    10. This should be your absolute best work - the kind of thread that goes viral
    
    Make it impossible to ignore!
    """
    
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    return response.content

def identify_best_video_segment(transcript, video_duration):
    """Use AI to identify the most engaging 60-second segment"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.7
    )
    
    prompt = f"""
    You are an expert video editor specializing in identifying the most engaging content.
    Analyze the following transcript and identify the most compelling 60-second segment for a social media video.
    
    Video Duration: {video_duration} seconds
    
    Transcript:
    {transcript[:8000]}
    
    Your task:
    1. Identify the most engaging, surprising, or impactful 60-second segment
    2. This segment should work well as a standalone clip for Instagram Reels/TikTok
    3. Look for segments with:
       - Strong emotional impact
       - Surprising revelations
       - Key insights
       - Actionable takeaways
       - Natural cliffhangers or hooks
    
    Respond with a JSON object containing:
    {{
        "start_time": [start time in seconds],
        "end_time": [end time in seconds],
        "reason": "Brief explanation of why this segment was chosen"
    }}
    
    The segment must be exactly 60 seconds long.
    """
    
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    
    try:
        # Extract JSON from response
        response_text = response.content
        
        # Try to find JSON pattern
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            segment_info = json.loads(json_str)
            return segment_info
        else:
            # If no JSON found, return default
            return {
                "start_time": video_duration // 2 - 30,
                "end_time": video_duration // 2 + 30,
                "reason": "Default middle segment"
            }
    except Exception as e:
        print(f"Error parsing segment info: {e}")
        # Default to middle 60 seconds
        return {
            "start_time": video_duration // 2 - 30,
            "end_time": video_duration // 2 + 30,
            "reason": "Default middle segment"
        }

def generate_ai_video_script_and_prompt(transcript, summary, video_info):
    """Generate the best AI video script and prompt"""
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.schema import HumanMessage
    
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.9
    )
    
    prompt = f"""
    You are a master AI video creator specializing in viral short-form content.
    Create the perfect 60-second AI video based on the following video transcript and summary.
    
    Video Title: {video_info.title}
    Channel: {video_info.author}
    Video URL: {video_info.watch_url}
    
    Summary:
    {summary}
    
    Transcript (for reference):
    {transcript[:5000]}
    
    Your task:
    1. Create a compelling 60-second video script (exactly 150-180 words)
    2. Generate a detailed prompt for an AI video generation tool
    
    Video Script Requirements:
    - Start with a powerful hook in the first 3 seconds
    - Cover the most exciting/revelatory parts of the content
    - Include 3-5 key points with visual descriptions
    - End with a strong call to action
    - Use conversational, energetic language
    - Include natural pauses for visual transitions
    
    AI Video Prompt Requirements:
    - Create a detailed prompt for an AI video generation tool (like Runway, Pika, etc.)
    - Include visual style, tone, and pacing instructions
    - Specify scene descriptions for key moments
    - Include text overlay suggestions
    - Add music/sound effect recommendations
    - Make it production-ready
    
    Respond with a JSON object:
    {{
        "video_script": "[The 60-second script]",
        "ai_video_prompt": "[The detailed AI video generation prompt]"
    }}
    """
    
    messages = [HumanMessage(content=prompt)]
    response = llm.invoke(messages)
    
    try:
        # Extract JSON from response
        response_text = response.content
        
        # Try to find JSON pattern
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            content_info = json.loads(json_str)
            return content_info
        else:
            # If no JSON found, return default
            return {
                "video_script": "Error generating script",
                "ai_video_prompt": "Error generating prompt"
            }
    except Exception as e:
        print(f"Error parsing video content: {e}")
        return {
            "video_script": "Error generating script",
            "ai_video_prompt": "Error generating prompt"
        }

def process_video(youtube_url, task_id):
    """Process the video and generate all content"""
    try:
        # Update task status
        tasks[task_id]['status'] = 'downloading_audio'
        
        # Step 1: Download audio using yt-dlp
        try:
            yt, audio_file = download_audio_with_ytdlp(youtube_url, task_id)
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"Audio download failed: {str(e)}"
            return
        
        # Verify the file exists before proceeding
        if not os.path.exists(audio_file):
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = "Audio file not found after download"
            return
        
        # Update task status
        tasks[task_id]['status'] = 'transcribing'
        
        # Step 2: Transcribe audio
        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(audio_file, word_timestamps=True)
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"Transcription failed: {str(e)}"
            # Clean up audio file
            if os.path.exists(audio_file):
                os.remove(audio_file)
            return
        
        # Create full text transcript
        full_text = result['text']
        
        # Clean up temporary audio file
        os.remove(audio_file)
        
        # Update task status
        tasks[task_id]['status'] = 'generating_summary'
        
        # Step 3: Generate summary
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain.schema import HumanMessage
            
            llm = ChatGoogleGenerativeAI(
                model="models/gemini-1.5-flash",
                google_api_key=api_key,
                temperature=0.7
            )
            
            prompt = f"""
            Please provide a concise summary of the following video transcript. 
            Include the main topics discussed and key takeaways:
            
            {full_text[:15000]}
            """
            
            messages = [HumanMessage(content=prompt)]
            summary_response = llm.invoke(messages)
            summary = summary_response.content
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"Summary generation failed: {str(e)}"
            return
        
        # Update task status
        tasks[task_id]['status'] = 'generating_posts'
        
        # Step 4: Generate best social media posts
        try:
            linkedin_post = generate_best_linkedin_post(full_text, summary, yt)
            twitter_thread = generate_best_twitter_thread(full_text, summary, yt)
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"Social media posts generation failed: {str(e)}"
            return
        
        # Update task status
        tasks[task_id]['status'] = 'downloading_video'
        
        # Step 5: Download video and identify best segment
        try:
            video_file = download_video_with_ytdlp(youtube_url, task_id)
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"Video download failed: {str(e)}"
            return
        
        # Update task status
        tasks[task_id]['status'] = 'identifying_segment'
        
        try:
            segment_info = identify_best_video_segment(full_text, yt.length)
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"Segment identification failed: {str(e)}"
            # Clean up video file
            if os.path.exists(video_file):
                os.remove(video_file)
            return
        
        # Update task status
        tasks[task_id]['status'] = 'extracting_clip'
        
        try:
            # Extract the best segment
            clip_file = extract_video_clip(video_file, segment_info['start_time'], 60, task_id)
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"Clip extraction failed: {str(e)}"
            # Clean up video file
            if os.path.exists(video_file):
                os.remove(video_file)
            return
        
        # Update task status
        tasks[task_id]['status'] = 'generating_ai_video'
        
        try:
            # Step 6: Generate AI video script and prompt
            video_content = generate_ai_video_script_and_prompt(full_text, summary, yt)
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = f"AI video content generation failed: {str(e)}"
            # Clean up video file
            if os.path.exists(video_file):
                os.remove(video_file)
            return
        
        # Clean up the full video file
        os.remove(video_file)
        
        # Store results
        results = {
            'video_info': {
                'title': yt.title,
                'author': yt.author,
                'length': yt.length,
                'views': yt.views,
                'watch_url': yt.watch_url
            },
            'transcript': full_text,
            'summary': summary,
            'linkedin_post': linkedin_post,
            'twitter_thread': twitter_thread,
            'segment_info': segment_info,
            'video_content': video_content,
            'clip_file': clip_file
        }
        
        # Update task status and results
        tasks[task_id]['status'] = 'completed'
        tasks[task_id]['results'] = results
        
    except Exception as e:
        # Update task status with error
        tasks[task_id]['status'] = 'error'
        tasks[task_id]['error'] = f"Unexpected error: {str(e)}"
        
        # Clean up in case of error
        if 'audio_file' in locals() and os.path.exists(audio_file):
            os.remove(audio_file)
        if 'video_file' in locals() and os.path.exists(video_file):
            os.remove(video_file)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    # Get YouTube URL from form
    youtube_url = request.form.get('youtube_url')
    
    if not youtube_url:
        return jsonify({'error': 'YouTube URL is required'}), 400
    
    # Generate a unique task ID
    task_id = str(uuid.uuid4())
    
    # Store task ID in session
    session['current_task_id'] = task_id
    
    # Initialize task
    tasks[task_id] = {
        'status': 'starting',
        'youtube_url': youtube_url,
        'results': None,
        'error': None
    }
    
    # Start processing in a separate thread
    thread = threading.Thread(target=process_video, args=(youtube_url, task_id))
    thread.start()
    
    # Return task ID
    return jsonify({'task_id': task_id})

@app.route('/status/<task_id>')
def status(task_id):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    return jsonify({
        'status': tasks[task_id]['status'],
        'error': tasks[task_id].get('error')
    })

@app.route('/loading/<task_id>')
def loading(task_id):
    if task_id not in tasks:
        return redirect(url_for('index'))
    
    return render_template('loading.html', task_id=task_id)

@app.route('/results')
def results():
    # Get task ID from session
    task_id = session.get('current_task_id')
    
    if not task_id or task_id not in tasks:
        return redirect(url_for('index'))
    
    task = tasks[task_id]
    
    if task['status'] != 'completed':
        return redirect(url_for('index'))
    
    # Create video URL
    video_url = url_for('static', filename=f'videos/video_clip_{task_id}.mp4')
    
    return render_template('results.html', task=task, task_id=task_id, video_url=video_url)

@app.route('/download/<task_id>/<file_type>')
def download(task_id, file_type):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Task not completed'}), 400
    
    if file_type == 'video':
        video_path = os.path.join(os.getcwd(), 'static', 'videos', f"video_clip_{task_id}.mp4")
        if os.path.exists(video_path):
            return send_file(video_path, as_attachment=True, download_name='best_60sec_video.mp4')
        else:
            return jsonify({'error': 'Video file not found'}), 404
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/text/<task_id>/<text_type>')
def get_text(task_id, text_type):
    if task_id not in tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Task not completed'}), 400
    
    if text_type == 'linkedin':
        return jsonify({'text': task['results']['linkedin_post']})
    elif text_type == 'twitter':
        return jsonify({'text': task['results']['twitter_thread']})
    elif text_type == 'ai_video_script':
        return jsonify({'text': task['results']['video_content']['video_script']})
    elif text_type == 'ai_video_prompt':
        return jsonify({'text': task['results']['video_content']['ai_video_prompt']})
    
    return jsonify({'error': 'Invalid text type'}), 400

if __name__ == '__main__':
    # Check required packages
    required_packages = ['whisper', 'langchain_google_genai', 'yt_dlp']
    missing_packages = [pkg for pkg in required_packages if not check_package(pkg)]
    
    if missing_packages:
        print("Missing required packages:")
        for pkg in missing_packages:
            print(f"  - {pkg}")
        print("\nPlease install them using:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)
    
    # Check FFmpeg
    if not check_ffmpeg():
        print("FFmpeg is not installed or not in your PATH.")
        sys.exit(1)
    
    app.run(debug=True)