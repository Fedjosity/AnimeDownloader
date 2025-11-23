# Frontend Setup Guide

This guide will help you set up and run the AnimeDownloader frontend.

## Quick Start

### 1. Install Dependencies

Navigate to the `frontend` directory and install npm packages:

```bash
cd frontend
npm install
```

### 2. Start the Backend API Server

In the root directory, start the FastAPI server:

```bash
# Make sure you're in the root directory (not frontend/)
python api_server.py
```

The API server will run on `http://localhost:8000`

### 3. Start the Frontend Development Server

In a new terminal, navigate to the frontend directory and start the dev server:

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Usage

1. Open your browser to `http://localhost:3000`
2. Click "View Setup Instructions" if you need help setting up
3. Search for an anime
4. Select an anime from the results
5. Choose episode range
6. Select language and quality
7. Process and download episodes

## Troubleshooting

### Frontend won't connect to backend

- Make sure the backend API server is running on port 8000
- Check that CORS is enabled in the backend (it should be by default)
- Verify the API URL in the browser console

### Build errors

- Make sure you have Node.js 18+ installed
- Delete `node_modules` and `package-lock.json`, then run `npm install` again
- Check that all dependencies in `package.json` are compatible

### Type errors

- Run `npm run build` to check for TypeScript errors
- Make sure all imports are correct
- Verify that the API types match the backend response format

## Production Build

To build for production:

```bash
npm run build
```

The built files will be in the `dist` directory. You can serve these files with any static file server.

## Environment Variables

You can configure the API URL by creating a `.env` file in the frontend directory:

```
VITE_API_URL=http://localhost:8000
```
