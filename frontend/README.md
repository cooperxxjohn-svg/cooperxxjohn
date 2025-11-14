# TakeoffAI Frontend

Modern React application for AI-powered BOQ estimation from construction drawings.

## Features

- **Dark Theme UI**: Modern gradient design with cyan/blue accents
- **Drag & Drop Upload**: Easy PDF file upload interface
- **Real-time Processing**: Visual progress tracking with 8-15 minute simulation
- **Interactive Results**: Comprehensive BOQ display with statistics
- **Export Capabilities**: Download BOQ as CSV or Excel
- **Responsive Design**: Optimized for all screen sizes

## Tech Stack

- React 18
- Vite
- Tailwind CSS
- Lucide React (Icons)
- XLSX (Excel export)
- File-saver (Download management)

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The application will start on `http://localhost:3000`

## Build for Production

```bash
npm run build
npm run preview
```

## Usage

1. **Upload Tab**: Drag and drop or click to upload a PDF construction drawing
2. **Processing Tab**: Watch real-time progress as AI analyzes the drawing
3. **Results Tab**: View comprehensive BOQ with:
   - Total value and statistics
   - Line-by-line breakdown
   - Export to CSV/Excel

## API Connection

The frontend connects to the Flask backend at `http://localhost:5000`

Make sure the backend server is running before uploading drawings.

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── index.css        # Tailwind CSS imports
│   └── main.jsx         # React entry point
├── public/              # Static assets
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind configuration
└── package.json         # Dependencies
```
