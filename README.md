# Videer - Video Generator from Pexels

Videer is a Python-based GUI application that allows you to search and download open source videos from Pexels.com based on text prompts. The application provides an intuitive interface with customizable parameters for video generation.

## Features

- **GUI Form Interface**: Easy-to-use tkinter-based graphical interface
- **Text Prompt Search**: Search for videos using natural language prompts
- **Customizable Parameters**:
  - Number of videos to fetch (1-80)
  - Video orientation (landscape, portrait, square)
  - Video quality (HD, SD)
  - Minimum video size (large, medium, small)
- **Pexels Integration**: Direct integration with Pexels.com API for accessing free, high-quality stock videos
- **Batch Download**: Download multiple videos at once
- **Video Metadata**: View detailed information about each video including duration, resolution, and creator

## Prerequisites

- Python 3.6 or higher
- Pexels API key (free at https://www.pexels.com/api/)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/tariq424/videer.git
cd videer
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Get your free Pexels API key:
   - Visit https://www.pexels.com/api/
   - Sign up for a free account
   - Copy your API key

## Usage

1. Run the application:
```bash
python videer_gui.py
```

2. Enter your Pexels API key in the "API Configuration" section and click "Connect"

3. Configure your search parameters:
   - **Search Prompt**: Enter keywords describing the videos you want (e.g., "nature landscape", "city skyline", "ocean waves")
   - **Number of Videos**: Select how many videos to retrieve (1-80)
   - **Orientation**: Choose between landscape, portrait, or square
   - **Video Quality**: Select HD or SD quality
   - **Minimum Size**: Choose large, medium, or small

4. Click "Search Videos" to fetch results from Pexels

5. Review the search results displayed in the results section

6. Click "Download Selected" and choose a directory to save the videos

## Configuration

The application will save your API key in a `.env` file for convenience. You can also manually create this file:

```bash
cp .env.example .env
# Edit .env and add your API key
```

## Project Structure

```
videer/
├── videer_gui.py         # Main GUI application
├── pexels_client.py      # Pexels API client
├── requirements.txt      # Python dependencies
├── .env.example         # Example environment file
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

## About Pexels

All videos are sourced from Pexels.com, which provides free stock photos and videos. The videos are:
- Free to use for personal and commercial purposes
- No attribution required (but appreciated)
- Distributed under the Pexels License

Learn more at: https://www.pexels.com/license/

## License

This project is open source and available for free use.

## Troubleshooting

- **API Connection Error**: Ensure your API key is valid and you have an internet connection
- **No Results Found**: Try different search terms or adjust the parameters
- **Download Fails**: Check your internet connection and ensure you have write permissions to the selected directory

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.
