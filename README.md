# TalkToWeb: Natural Language Browser Automation

TalkToWeb is a Python-based automation tool that lets you control your browser using natural language commands. Simply describe what you want to do (either by typing or speaking), and the agent will convert your request into browser actions using AI and execute them.

## Features

- 🗣️ Voice or text input for commands
- 🤖 AI-powered command understanding using Google's Gemini model
- 🌐 Automated web navigation, form filling, and clicking
- ✈️ Specialized support for flight booking on Google flights
- 📸 Screenshot capability (coming soon)

## Setup

1. Clone this repository and install dependencies:
```bash
git clone <repo-url>
cd TalkToWeb
python -m pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
python -m playwright install
```

3. Create a `.env` file with required credentials:
```bash
# Copy the example env file
cp .env.example .env
# Edit .env and add your credentials
```

Required environment variables:
- `GOOGLE_API_KEY`: Your Google API key for the Gemini model
- `MMT_EMAIL`: Your MakeMyTrip account email (for flight booking)
- `MMT_PASSWORD`: Your MakeMyTrip account password
- `BROWSER_USER_DATA_DIR`: (Optional) Path to Chrome user profile directory

## Usage

Run the script with a command as arguments or interactively:

```bash
# Run with command as arguments
python run_task.py "search for python documentation"

# Run interactively (will prompt for voice/text input)
python run_task.py
```

### Example Commands

1. Google Search:
```bash
python run_task.py "search for Playwright documentation"
```

2. YouTube Search:
```bash
python run_task.py "find Python tutorials on YouTube"
```

3. Book Flight:
```bash
python run_task.py "book flight from Mumbai to Delhi on 2025-10-28"
```

Note: Flight booking requires valid MMT_EMAIL and MMT_PASSWORD in your .env file.

## Troubleshooting

1. Voice Input Issues
   - Ensure you have a working microphone
   - On Windows, if PyAudio fails to install, try: `pip install pipwin && pipwin install pyaudio`

2. Browser Issues
   - If Chrome launch fails, ensure Chrome is installed
   - Try setting BROWSER_USER_DATA_DIR in .env to your Chrome profile path
   - Or leave it unset to use a fresh profile

## Contributing

Feel free to open issues or submit pull requests. Please include tests for new features.