# Videer Application Features

## Main Features

### 1. API Configuration
- Enter your Pexels API key
- Secure key storage in `.env` file
- One-time setup with automatic reconnection
- Free API access from https://www.pexels.com/api/

### 2. Search Parameters Form
The application provides a comprehensive form with the following fields:

#### Text Prompt
- Natural language search (e.g., "sunset over ocean", "urban cityscape")
- Powered by Pexels' intelligent search engine
- Supports multi-word queries and descriptive phrases

#### Number of Videos
- Select 1-80 videos per search
- Adjustable spinner control
- Default: 5 videos

#### Orientation
- **Landscape**: Traditional widescreen format (16:9)
- **Portrait**: Mobile/vertical format (9:16)
- **Square**: Social media format (1:1)

#### Video Quality
- **HD**: High definition (1080p and above)
- **SD**: Standard definition (720p and below)

#### Minimum Size
- **Large**: Best quality, larger file sizes
- **Medium**: Balanced quality and file size (recommended)
- **Small**: Faster downloads, smaller storage

### 3. Search Results Display
- Detailed metadata for each video:
  - Video ID
  - Duration in seconds
  - Resolution (width × height)
  - Creator/user information
  - Direct link to Pexels page
  - Available quality options
- Scrollable results area
- Easy-to-read formatted output

### 4. Video Download
- Batch download all search results
- Choose custom download directory
- Progress tracking in status bar
- Creates organized `downloads/` folder
- Automatic file naming with video IDs
- Thread-based downloads (non-blocking UI)

### 5. Status Bar
- Real-time connection status
- Search progress updates
- Download progress with counts
- Error messages and notifications

## Technical Features

### User Interface
- Built with Python tkinter
- Clean, intuitive layout
- Responsive design
- Cross-platform compatibility (Windows, macOS, Linux)

### API Integration
- RESTful API client
- Robust error handling
- Configurable request parameters
- Timeout protection

### Threading
- Asynchronous search operations
- Non-blocking downloads
- Responsive UI during long operations

### File Management
- Automatic directory creation
- Unique file naming (video_ID_index.mp4)
- Organized downloads folder structure

## Usage Scenarios

### Content Creation
- Source stock footage for video projects
- Find B-roll for documentaries
- Gather reference material

### Social Media
- Discover trending video content
- Find videos in specific formats (portrait for Stories)
- Quick access to shareable content

### Design & Development
- Prototype video applications
- Test video players
- Demonstrate video handling

### Education & Research
- Collect visual examples
- Study cinematography
- Analyze video trends

## Keyboard Shortcuts

- `Tab`: Navigate between fields
- `Enter`: Activate focused button
- `Space`: Toggle checkboxes/activate buttons

## File Output

Downloaded videos are saved as:
```
downloads/
├── video_12345678_1.mp4
├── video_87654321_2.mp4
└── video_11223344_3.mp4
```

## API Credits

All videos are provided by Pexels.com:
- Free for personal and commercial use
- No attribution required
- Licensed under Pexels License
- Photographer credit appreciated

## Performance

- Fast API response times
- Efficient video streaming
- Minimal memory footprint
- Optimized for large result sets
