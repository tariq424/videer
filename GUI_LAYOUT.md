# Videer GUI Interface Description

## Application Window Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Videer - Video Generator                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─ API Configuration ──────────────────────────────────────────┐  │
│  │  Pexels API Key: [**************************] [Connect]      │  │
│  │  Get your free API key from https://www.pexels.com/api/      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  ┌─ Video Search Parameters ─────────────────────────────────────┐ │
│  │  Search Prompt: [nature landscape                          ]  │  │
│  │                                                                │  │
│  │  Number of Videos:  [5  ▲▼]                                  │  │
│  │                                                                │  │
│  │  Orientation:       [landscape        ▼]                     │  │
│  │                                                                │  │
│  │  Video Quality:     [hd               ▼]                     │  │
│  │                                                                │  │
│  │  Minimum Size:      [medium           ▼]                     │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│         [Search Videos]  [Download Selected]                         │
│                                                                       │
│  ┌─ Search Results ──────────────────────────────────────────────┐ │
│  │ Found 5 videos:                                               │ │
│  │                                                                │ │
│  │ Video 1:                                                      │ │
│  │   ID: 12345678                                                │ │
│  │   Duration: 15 seconds                                        │ │
│  │   Width: 1920px, Height: 1080px                              │ │
│  │   User: John Doe                                              │ │
│  │   URL: https://www.pexels.com/video/12345678                 │ │
│  │   Available qualities: hd, sd                                 │ │
│  │                                                                │ │
│  │ Video 2:                                                      │ │
│  │   ...                                                          │ │
│  │                                                               ▲│ │
│  │                                                               ││ │
│  │                                                               ││ │
│  │                                                               ││ │
│  │                                                               ▼│ │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Status: Connected to Pexels API successfully!                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Interface Elements

### 1. Title Bar
- Application title: "Videer - Video Generator from Pexels"
- Window size: 800x700 pixels (resizable)

### 2. API Configuration Section
- **API Key Input**: Password-masked text field
- **Connect Button**: Establishes connection to Pexels API
- **Info Text**: Link to get free API key
- API key is automatically saved to `.env` file after connection

### 3. Video Search Parameters Section
Contains 5 form fields:

#### Search Prompt (Text Entry)
- Full-width text input
- Accepts natural language queries
- Default: "nature landscape"
- Examples: "sunset beach", "city skyline", "mountain hiking"

#### Number of Videos (Spinbox)
- Range: 1-80 videos
- Default: 5
- Increment/decrement buttons

#### Orientation (Dropdown)
- Options: landscape, portrait, square
- Default: landscape
- Read-only selection

#### Video Quality (Dropdown)
- Options: hd, sd
- Default: hd
- Read-only selection

#### Minimum Size (Dropdown)
- Options: large, medium, small
- Default: medium
- Read-only selection

### 4. Action Buttons
- **Search Videos**: Initiates video search (disabled until API connected)
- **Download Selected**: Downloads found videos (enabled after search)
- Buttons remain responsive during operations (threading)

### 5. Search Results Section
- **Scrollable Text Area**: Displays detailed video information
- **Read-Only**: Prevents accidental editing
- **Auto-scroll**: Supports keyboard and mouse scrolling
- Shows for each video:
  - Video ID
  - Duration in seconds
  - Resolution (width x height)
  - Creator name
  - Pexels URL
  - Available quality options

### 6. Status Bar
- Bottom-aligned
- Shows real-time status:
  - Connection status
  - Search progress
  - Download progress with counts
  - Error messages
- Sunken relief style

## User Workflow

1. **Initial Setup**
   - User enters Pexels API key
   - Clicks "Connect"
   - API key is validated and saved

2. **Search Configuration**
   - User enters search prompt
   - Adjusts parameters as needed
   - Clicks "Search Videos"

3. **View Results**
   - Results display in scrollable area
   - Shows detailed metadata for each video
   - Status bar updates with count

4. **Download Videos**
   - User clicks "Download Selected"
   - Selects download directory
   - Videos download with progress updates
   - Completion notification shown

## Visual Features

- **Clean Layout**: Organized with labeled frames
- **Responsive Design**: Adapts to window resizing
- **Professional Look**: Uses ttk themed widgets
- **User Feedback**: Real-time status updates
- **Non-Blocking**: Threading keeps UI responsive
- **Error Handling**: Clear error messages via dialogs

## Accessibility

- Tab navigation between fields
- Keyboard shortcuts supported
- Clear visual hierarchy
- High contrast labels
- Tooltips via help text
