import sys
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
"""
FastAPI server to expose the anime downloader backend functionality.
This server acts as a bridge between the React frontend and the Python CLI backend.
"""

# Import the backend modules
import pahe
import kwik_token

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
from concurrent.futures import ThreadPoolExecutor


app = FastAPI(title="AnimeDownloader API", version="1.0.0")

# CORS middleware to allow frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thread pool for running synchronous functions
executor = ThreadPoolExecutor(max_workers=10)


# Pydantic models for request/response
class SearchRequest(BaseModel):
    query: str


class AnimeInfo(BaseModel):
    title: str
    type: str
    episodes: int
    status: str
    year: int
    score: float
    session_id: str


class EpisodeRangeRequest(BaseModel):
    session_id: str
    episode_range: List[int]  # [start, end]


class DownloadLinksRequest(BaseModel):
    anime_id: str
    episode_ids: List[str]


class ParseLinkRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    destination: str


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "AnimeDownloader API is running"}


@app.post("/api/search", response_model=List[AnimeInfo])
async def search_anime(request: SearchRequest):
    max_retries = 3
    retry_count = 0

    while retry_count < max_retries:
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                executor, pahe.search_apahe, request.query
            )
            if not results:
                return []
            # Convert to AnimeInfo models
            anime_list = []
            for anime in results:
                anime_list.append(AnimeInfo(
                    title=anime[0],
                    type=anime[1],
                    episodes=anime[2],
                    status=anime[3],
                    year=anime[4],
                    score=anime[5],
                    session_id=anime[6]
                ))
            return anime_list
        except Exception as e:
            retry_count += 1
            error_msg = str(e)
            # DDoS-Guard or anti-bot detected
            if '403' in error_msg or 'DDoS-Guard' in error_msg or 'non-JSON' in error_msg:
                if retry_count < max_retries:
                    await asyncio.sleep(1.5)
                    continue
                else:
                    playwright_status = (
                        "active" if getattr(pahe, 'USE_PLAYWRIGHT', False)
                        else (
                            "not active (using curl_cffi)" if getattr(pahe, 'USE_CURL_CFFI', False)
                            else "not installed or not working"
                        )
                    )
                    error_detail = (
                        "Service temporarily unavailable due to website DDoS protection.<br>"
                        f"Playwright status: <b>{playwright_status}</b>.<br>"
                        "To fix: Run <b>pip install playwright && playwright install chromium</b> and restart the backend.<br>"
                        "If you cannot install Playwright or the error persists, try using the CLI: <code>python main.py</code><br>"
                        "If you think you have Playwright but still get this problem, ensure Python and Node.js are up to date."
                    )
                    raise HTTPException(status_code=503, detail=error_detail)
            else:
                # Unexpected error
                raise HTTPException(status_code=500, detail=f"Search failed: {error_msg}")
    # Failsafe
    raise HTTPException(status_code=500, detail="Search failed after retries")


@app.get("/api/anime/{session_id}/episodes")
async def get_episode_count(session_id: str):
    """Get the actual episode count for an anime"""
    try:
        loop = asyncio.get_event_loop()
        count = await loop.run_in_executor(
            executor, pahe.get_actual_episode_count, session_id
        )
        return {"session_id": session_id, "episode_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/episodes")
async def get_episodes(request: EpisodeRangeRequest):
    """Get episode IDs for a given range"""
    try:
        loop = asyncio.get_event_loop()
        episode_data = await loop.run_in_executor(
            executor, pahe.mid_apahe, request.session_id, request.episode_range
        )
        
        # Convert to list of dicts
        episodes = []
        for ep_num, session_id in episode_data:
            episodes.append({
                "episode_number": ep_num,
                "session_id": session_id
            })
        
        return {
            "anime_id": request.session_id,
            "episodes": episodes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download-links")
async def get_download_links(request: DownloadLinksRequest):
    """Get download links for episodes"""
    try:
        loop = asyncio.get_event_loop()
        episodes_data = await loop.run_in_executor(
            executor, pahe.dl_apahe1, request.anime_id, request.episode_ids
        )
        
        # Organize the data
        organized = {}
        for index, links in episodes_data.items():
            organized[index] = links
        
        return {
            "anime_id": request.anime_id,
            "episodes": organized
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/parse-link")
async def parse_download_link(request: ParseLinkRequest):
    """Parse a redirect link to get the final download link"""
    try:
        loop = asyncio.get_event_loop()
        final_link = await loop.run_in_executor(
            executor, pahe.dl_apahe2, request.url
        )
        return {"url": request.url, "final_link": final_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/get-kwik-link")
async def get_kwik_link(request: ParseLinkRequest):
    """Get the final download link from a kwik.cx URL"""
    try:
        loop = asyncio.get_event_loop()
        download_link = await loop.run_in_executor(
            executor, kwik_token.get_dl_link, request.url
        )
        return {"url": request.url, "download_link": download_link}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/download")
async def download_file(request: DownloadRequest):
    """Download a file (this will be handled by the frontend, but we can provide the link)"""
    # For now, we'll just return the download link
    # The actual download will be handled by the frontend or a separate download service
    try:
        loop = asyncio.get_event_loop()
        download_link = await loop.run_in_executor(
            executor, kwik_token.get_dl_link, request.url
        )
        return {
            "url": request.url,
            "download_link": download_link,
            "destination": request.destination
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="0.0.0.0", port=8000)

