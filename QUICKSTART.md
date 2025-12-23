# Quick Start Guide

## Getting Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Your API Key
1. Visit [https://www.pexels.com/api/](https://www.pexels.com/api/)
2. Click "Get Started"
3. Sign up for a free account
4. Copy your API key from your account page

### 3. Launch the Application
```bash
python3 videer.py
```
or
```bash
python3 videer_gui.py
```

### 4. Connect and Search
1. Paste your API key in the "Pexels API Key" field
2. Click "Connect"
3. Enter a search prompt (e.g., "sunset beach", "mountain hiking")
4. Adjust parameters as needed
5. Click "Search Videos"
6. Click "Download Selected" to save videos

## Example Searches

Try these search prompts:
- `nature landscape`
- `city skyline night`
- `ocean waves sunset`
- `forest trail`
- `technology coding`
- `food cooking`
- `fitness workout`
- `travel adventure`

## Parameters Explained

- **Number of Videos**: How many results to fetch (1-80)
- **Orientation**: 
  - `landscape` - Wide horizontal videos (16:9)
  - `portrait` - Vertical videos (9:16, for mobile)
  - `square` - Square videos (1:1)
- **Video Quality**:
  - `hd` - High definition (1080p or higher)
  - `sd` - Standard definition
- **Minimum Size**:
  - `large` - Large file sizes, best quality
  - `medium` - Balanced quality and size
  - `small` - Smaller files, faster downloads

## Troubleshooting

### "No module named 'tkinter'"
Install tkinter:
- Ubuntu/Debian: `sudo apt-get install python3-tk`
- Fedora: `sudo dnf install python3-tkinter`
- macOS: Included with Python

### API Connection Error
- Verify your API key is correct
- Check your internet connection
- Ensure you haven't exceeded API rate limits

### Download Fails
- Check disk space
- Verify write permissions to download directory
- Try a different video quality setting

## Programmatic Usage

For using the API without the GUI, see `example_usage.py`:
```bash
python3 example_usage.py
```

## Testing

Run the test suite:
```bash
python3 test_videer.py
```

## Need Help?

- Check the full README.md for detailed documentation
- Visit [Pexels API Documentation](https://www.pexels.com/api/documentation/)
- Review the example_usage.py file for code examples
