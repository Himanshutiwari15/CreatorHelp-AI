# YouTube Video to Social Media Content Converter

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3.3-green.svg)
![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)

A powerful AI-powered web application that transforms YouTube videos into optimized social media content across multiple platforms. Leveraging cutting-edge AI models, this tool automatically generates engaging posts for LinkedIn, viral Twitter threads, Instagram-ready video clips, and professional AI video scripts.

## 🌟 Key Features

### 🎯 Smart Content Generation
- **AI-Powered Transcription**: Automatically transcribes YouTube videos using OpenAI's Whisper model with word-level timestamps.
- **Intelligent Content Creation**: Utilizes Google's Gemini AI to generate platform-optimized content.
- **Multi-Platform Support**: Creates tailored content for LinkedIn, Twitter, and Instagram.
- **Video Clip Extraction**: Identifies and extracts the most engaging 60-second segments from videos.

### 🚀 Advanced Capabilities
- **Real-Time Processing**: Live progress tracking with detailed status updates.
- **One-Click Sharing**: Instant copy buttons for all generated content.
- **Video Preview**: Built-in video player for extracted clips before download.
- **AI Video Tools**: Generates both video scripts and detailed AI video generation prompts.

### 🎨 User Experience
- **Responsive Design**: Clean, modern interface that works seamlessly on all devices.
- **Progress Tracking**: Visual progress indicators for each processing step.
- **Error Handling**: Comprehensive error messages and automatic cleanup.
- **Download Management**: Direct download links for all generated content.

## 🛠️ Technology Stack

### Backend
- **Flask 2.3.3**: Lightweight and flexible Python web framework.
- **AI Models**:
  - **Whisper 1.1.10**: State-of-the-art speech-to-text transcription.
  - **Google Gemini**: Advanced content generation and summarization.
- **Video Processing**:
  - **yt-dlp**: Robust YouTube video downloading.
  - **FFmpeg**: Professional video processing and clip extraction.

### Frontend
- **HTML5 & CSS3**: Modern web standards.
- **JavaScript**: Interactive client-side functionality.
- **Bootstrap 5**: Responsive UI components.
- **Toast Notifications**: User-friendly feedback system.

### Development Tools
- **Python 3.8+**: Core programming language.
- **Virtual Environment**: Isolated dependency management.
- **Git**: Version control system.

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8 or higher**
- **FFmpeg** (for video processing)
- **Google API key** (for Gemini AI)
- **Git** (for version control)

### Installation

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/your-username/youtube-social-media-converter.git](https://github.com/your-username/youtube-social-media-converter.git)
    cd youtube-social-media-converter
    ```

2.  **Create and activate virtual environment**
    ```bash
    # Create virtual environment
    python -m venv venv
    
    # Activate on Windows
    venv\Scripts\activate
    
    # Activate on macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install FFmpeg**

    **Windows**:
    -   Download from [ffmpeg.org](https://ffmpeg.org/download.html)
    -   Add the `bin` folder to your system PATH

    **macOS**:
    ```bash
    brew install ffmpeg
    ```

    **Linux (Ubuntu/Debian)**:
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```

5.  **Configure environment variables**
    ```bash
    # Copy the example environment file
    cp .env.example .env
    
    # Edit .env file and add your Google API key
    GOOGLE_API_KEY=your_google_api_key_here
    ```

6.  **Run the application**
    ```bash
    python app.py
    ```

7.  **Access the application**
    -   Open your web browser
    -   Navigate to `http://127.0.0.1:5000`

## 📖 Usage Guide

### Basic Workflow

1.  **Enter YouTube URL**
    -   Paste any public YouTube video URL in the input field.
    -   Click "Convert Video" to start processing.

2.  **Monitor Progress**
    -   View real-time progress updates on the loading page.
    -   Track each processing step from download to completion.

3.  **Access Results**
    -   **LinkedIn Post**: Professional content optimized for LinkedIn engagement.
    -   **Twitter Thread**: 7-tweet viral thread with emojis and hashtags.
    -   **Instagram Video**: 60-second video clip with download option.
    -   **AI Video Script**: Professional script for AI-generated videos.
    -   **AI Video Prompt**: Detailed prompt for AI video generation tools.

### Advanced Features

#### Content Customization
-   All generated content is platform-optimized.
-   LinkedIn posts include professional tone and relevant hashtags.
-   Twitter threads are structured for maximum engagement.
-   AI video scripts include hooks and calls-to-action.

#### Video Processing
-   Intelligent segment identification for the most engaging content.
-   High-quality video extraction with FFmpeg.
-   Preview videos before downloading.
-   Multiple format support (MP4, WebM, etc.).

#### Export Options
-   One-click copy buttons for all text content.
-   Direct download links for video files.
-   Clean, formatted output ready for immediate use.

## 📁 Project Structure

creatorhelp-ai/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # Project documentation
├── LICENSE               # MIT License
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # Contribution guidelines
├── static/
│   ├── css/
│   │   └── style.css   # Application styles
│   ├── js/
│   │   └── script.js   # Client-side scripts
│   └── videos/          # Generated video clips (not tracked)
└── templates/
    ├── index.html       # Home page
    ├── loading.html     # Progress tracking page
    └── results.html      # Results display page

## 🔑 Configuration

The application requires a few environment variables for proper functioning. These should be set in your `.env` file.

### Required Variables
- `GOOGLE_API_KEY`: Your Google Gemini API key.
- `FLASK_ENV`: Application environment (`development` or `production`).
- `SECRET_KEY`: A random secret string for Flask session security.

### Example `.env` File
```env
GOOGLE_API_KEY=your_google_api_key_here
FLASK_ENV=development
SECRET_KEY=supersecretkey


## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1.  Fork the Project
2.  Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3.  Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4.  Push to the Branch (`git push origin feature/AmazingFeature`)
5.  Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

---

## ✨ Acknowledgments

* [OpenAI Whisper](https://openai.com/research/whisper) for speech-to-text
* [Google Gemini](https://gemini.google.com/) for content generation
* [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube video downloading
* [Flask](https://flask.palletsprojects.com/) for the web framework
* [Bootstrap](https://getbootstrap.com/) for the UI components

