# AnimeDownloader Frontend

A modern React frontend for the AnimeDownloader application, built with TypeScript, Tailwind CSS, and shadcn/ui components.

## Features

- 🎨 Beautiful black and white theme
- 🔍 Anime search functionality
- 📺 Episode selection with range picker
- 🌐 Language and quality selection
- 📥 Download management with progress tracking
- 💻 OS-specific setup instructions
- 📱 Responsive design

## Prerequisites

- Node.js 18+ and npm
- Python 3.8+ (for the backend API server)

## Installation

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

## Development

1. Make sure the backend API server is running on `http://localhost:8000` (see main README for backend setup)

2. Start the development server:

```bash
npm run dev
```

3. Open your browser to `http://localhost:3000`

## Building for Production

```bash
npm run build
```

The built files will be in the `dist` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── ui/             # shadcn/ui components
│   │   ├── SearchBar.tsx
│   │   ├── AnimeCard.tsx
│   │   ├── EpisodeSelector.tsx
│   │   ├── LanguageQualitySelector.tsx
│   │   ├── DownloadManager.tsx
│   │   └── OSInstructions.tsx
│   ├── lib/                # Utilities and API client
│   │   ├── api.ts         # API client functions
│   │   ├── utils.ts       # Utility functions
│   │   └── os-utils.ts    # OS detection and instructions
│   ├── App.tsx            # Main application component
│   ├── main.tsx           # Application entry point
│   └── index.css          # Global styles
├── package.json
├── tsconfig.json
├── tailwind.config.js
└── vite.config.ts
```

## Technologies Used

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI component library
- **Radix UI** - Accessible component primitives
- **Lucide React** - Icons
- **Axios** - HTTP client

## API Integration

The frontend communicates with the FastAPI backend server. Make sure the backend is running before using the frontend.

The API base URL can be configured via the `VITE_API_URL` environment variable (defaults to `http://localhost:8000`).

## License

Same as the main project (GNU License)
