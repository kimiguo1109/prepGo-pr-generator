# PrepGo Practice Generator

A web-based tool that generates customizable AP practice question sets using AI. Users can select multiple units, specify the number of MCQ and FRQ questions, and choose difficulty levels to create personalized practice materials.

## Features

- 📚 **Multi-Unit Selection**: Choose one or multiple units to include in practice sets
- 📝 **Customizable Questions**: Specify exact number of MCQ (1-50) and FRQ (0-10) questions
- 🎯 **Difficulty Levels**: Choose from Easier, AP Level, or Harder difficulty
- 🤖 **AI-Powered Generation**: Uses Google Gemini 2.5 Pro for question generation
- 🧮 **LaTeX Support**: Properly rendered math and science notation
- 🖨️ **Print Ready**: Optimized for printing with clean formatting

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Pydantic
- **Frontend**: React 18, TypeScript, Vite
- **AI**: Google Gemini 2.5 Pro API
- **Styling**: CSS with warm amber/cream theme

## Project Structure

```
prepGo_pr_generator/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── api/                 # API endpoints
│   │   ├── models/              # Pydantic models
│   │   ├── services/            # Business logic
│   │   └── prompts/             # AI prompt templates
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Main component
│   │   ├── api/                 # API client
│   │   ├── components/          # UI components
│   │   ├── hooks/               # Custom React hooks
│   │   └── types/               # TypeScript types
│   └── package.json
├── start.sh                     # Startup script
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+ or 22+
- Gemini API Key

### Using the Start Script

```bash
# Set API key
export GEMINI_API_KEY=your_api_key_here

# Start both services
./start.sh start

# Stop services
./start.sh stop

# Check status
./start.sh status

# View logs
./start.sh logs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment (optional)
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_api_key_here

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 18301 --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access the Application

- Frontend: http://localhost:18300
- Backend API: http://localhost:18301
- API Docs: http://localhost:18301/docs

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/courses` | List available courses |
| GET | `/api/v1/courses/{id}/units` | Get units for a course |
| POST | `/api/v1/practice/generate` | Generate practice set (streaming) |
| POST | `/api/v1/practice/generate-sync` | Generate practice set (non-streaming) |
| GET | `/api/v1/practice/queue-status` | Get queue status |

## Request Body for Generate

```json
{
  "course_id": "biology",
  "unit_numbers": [1, 2, 3],
  "mcq_count": 15,
  "frq_count": 2,
  "difficulty": "ap_level"
}
```

### Difficulty Options

- `easier`: Easier than AP exam (foundational concepts)
- `ap_level`: AP Exam level (default)
- `harder`: Harder than AP exam (advanced analysis)

## Supported Courses

| Course ID | Course Name |
|-----------|-------------|
| `biology` | AP Biology |
| `us-history` | AP U.S. History |
| `world-history` | AP World History: Modern |
| `european-history` | AP European History |
| `computer-science-a` | AP Computer Science A |
| `computer-science-principles` | AP Computer Science Principles |
| `microeconomics` | AP Microeconomics |
| `macroeconomics` | AP Macroeconomics |

## Usage

1. Open the web app at http://localhost:18300
2. Select an AP subject from the dropdown
3. Select one or more units (or "Select All")
4. Adjust MCQ and FRQ question counts
5. Choose difficulty level
6. Click "Generate Practice Set"
7. Wait for AI to generate questions
8. Use Edit, Copy, or Print buttons as needed

## License

MIT License - PrepGo © 2025

