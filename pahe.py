import grequests
import requests
import re
import os
from tqdm import tqdm
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to use playwright for DDoS-Guard bypass (handles JavaScript challenges)
# Fallback to curl_cffi, then cloudscraper
USE_PLAYWRIGHT = False
USE_CURL_CFFI = False
playwright_context = None

try:
    from playwright.sync_api import sync_playwright
    USE_PLAYWRIGHT = True
    # Initialize playwright browser context
    try:
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(headless=True)
        playwright_context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
    except Exception as e:
        # If playwright fails to initialize, fall through to curl_cffi
        USE_PLAYWRIGHT = False
        raise ImportError(f"Playwright initialization failed: {e}")
    # Create a requests-like session using playwright
    class PlaywrightSession:
        def __init__(self, context):
            self.context = context
            self.cookies = []
            
        def get(self, url, **kwargs):
            page = self.context.new_page()
            response_obj = None
            
            def handle_response(response):
                nonlocal response_obj
                # Capture the response for the URL we're requesting
                if url in response.url:
                    response_obj = response
            
            page.on("response", handle_response)
            
            try:
                # Visit the page and wait for it to load
                # Use load state to wait for the page to be ready
                page.goto(url, wait_until='load', timeout=30000)
                
                # Wait a moment for any redirects or challenges
                page.wait_for_timeout(1000)
                
                # For API endpoints, wait for JSON content to appear (DDoS-Guard challenge completion)
                # Keep checking until we get valid JSON or timeout
                import time
                max_wait = 30  # Maximum wait time in seconds
                start_time = time.time()
                text = ""
                
                while time.time() - start_time < max_wait:
                    try:
                        # Wait for the page to be stable
                        page.wait_for_load_state('domcontentloaded', timeout=2000)
                        
                        # Get the text content
                        text = page.evaluate("() => { try { return document.body ? document.body.textContent : document.documentElement.textContent; } catch(e) { return ''; } }")
                        
                        # Check if we have valid JSON (starts with { or [)
                        if text and text.strip():
                            stripped = text.strip()
                            if (stripped.startswith('{') or stripped.startswith('[')) and 'DDoS-Guard' not in text and 'Checking your browser' not in text:
                                # We have JSON and it's not the challenge page
                                break
                            elif 'DDoS-Guard' in text or 'Checking your browser' in text:
                                # Still on challenge page, wait a bit more
                                page.wait_for_timeout(500)
                                continue
                            elif stripped.startswith('{') or stripped.startswith('['):
                                # We have JSON
                                break
                    except Exception as e:
                        # If evaluation fails (e.g., navigation), wait and retry
                        page.wait_for_timeout(500)
                        continue
                    
                    # Wait a bit before checking again
                    page.wait_for_timeout(500)
                
                # Final check - if still no valid JSON, try one more time
                if not text or not text.strip() or ('DDoS-Guard' in text or 'Checking your browser' in text):
                    try:
                        page.wait_for_load_state('domcontentloaded', timeout=5000)
                        text = page.evaluate("() => { try { return document.body ? document.body.textContent : document.documentElement.textContent; } catch(e) { return ''; } }")
                    except:
                        pass
                
                # Wait for network to be idle to ensure all requests are done
                try:
                    page.wait_for_load_state('networkidle', timeout=5000)
                except:
                    pass  # Ignore timeout if network never becomes idle
                
                # If we got a response object, use its status and headers
                if response_obj:
                    status_code = response_obj.status
                    response_headers = dict(response_obj.headers) if response_obj.headers else {}
                else:
                    # Default to 200 if no response object
                    status_code = 200
                    response_headers = {}
                
                # If we're still on the challenge page, the status might be 403
                # But if we have JSON, it means the challenge completed
                if text and (text.strip().startswith('{') or text.strip().startswith('[')):
                    # We have valid JSON, so the challenge completed successfully
                    status_code = 200
                elif 'DDoS-Guard' in text or 'Checking your browser' in text:
                    # Still on challenge page
                    status_code = 403
                
                # Get cookies from the page
                self.cookies = self.context.cookies()
                    
                # Create a mock response object
                class MockResponse:
                    def __init__(self, status_code, text, headers):
                        self.status_code = status_code
                        self.text = text
                        self.headers = headers
                        self.content = text.encode('utf-8') if isinstance(text, str) else text
                        
                    def json(self):
                        import json
                        return json.loads(self.text)
                        
                    def raise_for_status(self):
                        if self.status_code >= 400:
                            import requests
                            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")
                            
                return MockResponse(
                    status_code,
                    text,
                    response_headers
                )
            finally:
                page.close()
                
    session = PlaywrightSession(playwright_context)
    print("Using Playwright for DDoS-Guard bypass")
except (ImportError, Exception) as e:
    USE_PLAYWRIGHT = False
    if 'Playwright' in str(type(e).__name__) or 'playwright' in str(e).lower():
        print(f"Playwright failed: {e}, falling back to curl_cffi")
    # Try curl_cffi as fallback
    try:
        from curl_cffi import requests as curl_requests
        USE_CURL_CFFI = True
        session = curl_requests.Session(impersonate="chrome110")
        session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://animepahe.si/',
            'Origin': 'https://animepahe.si',
        })
        print("Using curl_cffi for DDoS-Guard bypass")
    except ImportError:
        # Final fallback to cloudscraper
        import cloudscraper
        session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'darwin',
                'desktop': True
            }
        )
        session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://animepahe.si/',
            'Origin': 'https://animepahe.si',
        })
        print("Using cloudscraper for DDoS-Guard bypass")

# Base URL for animepahe.si
url = "https://animepahe.si/"

# Initialize session by visiting main page to get cookies (helps with DDoS-Guard)
def _init_session():
    """Initialize session by visiting main page to establish cookies"""
    try:
        if USE_PLAYWRIGHT:
            # Playwright handles this automatically on first request
            pass
        else:
            session.get(url, timeout=10)
    except:
        pass  # Ignore errors during initialization

# Initialize on import
_init_session()

def get_actual_episode_count(session_id: str) -> int:
    """
    Get the actual total number of episodes from the release API.
    
    Parameters:
        session_id (str): The anime session ID.
    
    Returns:
        int: The actual total number of episodes.
    """
    global url, USE_PLAYWRIGHT, USE_CURL_CFFI
    url2 = url + "api?m=release&id=" + session_id + "&sort=episode_asc&page=1"
    try:
        if USE_PLAYWRIGHT:
            r = session.get(url2)
        elif USE_CURL_CFFI:
            r = session.get(url2, timeout=10)
        else:
            r = session.get(url2, timeout=10)
        
        page_data = r.json()
        if 'total' in page_data:
            return page_data['total']
        elif 'last_page' in page_data and 'per_page' in page_data:
            # Calculate from last_page and per_page
            # Need to get the actual count from the last page
            last_page_url = url + "api?m=release&id=" + session_id + "&sort=episode_asc&page=" + str(page_data['last_page'])
            if USE_PLAYWRIGHT:
                last_page_r = session.get(last_page_url)
            elif USE_CURL_CFFI:
                last_page_r = session.get(last_page_url, timeout=10)
            else:
                last_page_r = session.get(last_page_url, timeout=10)
            last_page_data = last_page_r.json()
            # Calculate: (last_page - 1) * per_page + episodes on last page
            return (page_data['last_page'] - 1) * page_data['per_page'] + len(last_page_data.get('data', []))
        else:
            # Fallback: count episodes in first page
            return len(page_data.get('data', []))
    except Exception as e:
        # Return 0 on error, caller should handle fallback
        return 0

def search_apahe(query: str) -> list:
    """
    Search animepahe.si for anime matching the given query.
    
    Parameters:
        query (str): The search query.
    
    Returns:
        A list of lists, where each inner list contains the following information
        about a search result:
            - Title
            - Type (e.g. TV, movie)
            - Number of episodes
            - Status (e.g. completed, airing)
            - Year
            - Score
            - Session ID
    """
    global url, USE_PLAYWRIGHT, USE_CURL_CFFI
    search_url = url + "api?m=search&q=" + quote(query)
    data = None
    try:
        # Use appropriate session based on what's available
        if USE_PLAYWRIGHT:
            response = session.get(search_url)
        elif USE_CURL_CFFI:
            response = session.get(search_url, timeout=10)
        else:
            response = session.get(search_url, timeout=10)
        
        # Try to parse JSON even if status code is not 200 (sometimes 403 still returns JSON)
        content_type = response.headers.get('Content-Type', '').lower()
        
        # Check if response is valid JSON (even if status is not 200)
        try:
            data = response.json()
            # If we got valid JSON with data field, proceed even if status code was not 200
            if data and "data" in data:
                # Successfully got data, continue processing (ignore status code)
                pass
            else:
                # Got JSON but no data field - might be an error response
                if response.status_code != 200:
                    print(f"Warning: Got status {response.status_code} but response is JSON without 'data' field.")
                    print(f"Response: {data}")
                return []
        except ValueError:
            # Not valid JSON - only raise error if status is not 200
            if response.status_code != 200:
                # Try to get more info before raising
                print(f"Error: API returned status {response.status_code} with non-JSON response.")
                print(f"Content-Type: {content_type}")
                print(f"Response preview: {response.text[:300]}...")
                response.raise_for_status()  # This will raise the actual error
            else:
                print(f"Error: API returned invalid JSON. Status code: {response.status_code}")
                print(f"Content-Type: {content_type}")
                print(f"Response preview: {response.text[:300]}...")
            return []
        
        # Check if response is HTML (error page) instead of JSON
        if 'html' in content_type and response.status_code != 200:
            print(f"Error: API returned HTML instead of JSON. The API endpoint might have changed.")
            print(f"URL: {search_url}")
            print(f"Response preview: {response.text[:300]}...")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to connect to API. {str(e)}")
        print(f"URL: {search_url}")
        return []
    
    # Check if we got valid data
    if data is None:
        return []
    
    # if data is empty, return an empty list. i.e. no anime found
    if "data" not in data:
        return []
    
    # Check if data array exists and has items
    anime_list = data.get("data", [])
    if not anime_list or len(anime_list) == 0:
        return []

    clean_data = []
    try:
        print("Fetching actual episode counts for search results...")
        for idx, i in enumerate(anime_list, 1):
            hmm = []
            hmm.append(i['title'])
            hmm.append(i['type'])
            # Get actual episode count from release API for each anime
            print(f"  [{idx}/{len(anime_list)}] Fetching episode count for {i['title']}...", end='\r')
            actual_episodes = get_actual_episode_count(session_id=i['session'])
            if actual_episodes > 0:
                hmm.append(actual_episodes)
            else:
                # Fallback to search API value
                hmm.append(i['episodes'])
            hmm.append(i['status'])
            hmm.append(i['year'])
            hmm.append(i['score'])
            hmm.append(i['session'])
            clean_data.append(hmm)
        print()  # New line after progress
    except (KeyError, TypeError) as e:
        print(f"Error processing anime data: {str(e)}")
        print(f"Sample data item: {anime_list[0] if anime_list else 'No items'}")
        return []
    
    return clean_data

# print(search_apahe("horimiya"))

def mid_apahe(session_id: str , episode_range: list) -> list:
    """
    Retrieve a list of episode IDs for the specified session ID within a given range.
    
    Parameters:
        session_id (str): The unique session ID.
        episode_range (list): A list containing the start and end episode IDs within the range.
    
    Returns:
        list: A list of episode IDs.
    """
    # Calculate which pages we need to fetch
    # API returns 30 episodes per page, pages start at 1
    start_episode = episode_range[0]
    end_episode = episode_range[1]
    
    # Calculate page numbers (pages are 1-indexed)
    start_page = ((start_episode - 1) // 30) + 1
    end_page = ((end_episode - 1) // 30) + 1
    
    global url, USE_PLAYWRIGHT, USE_CURL_CFFI
    all_episodes = []  # Store all episodes in order
    
    # Fetch all needed pages
    for page in range(start_page, end_page + 1):
        url2 = url + "api?m=release&id=" + session_id + "&sort=episode_asc&page="+ str(page)
        try:
            if USE_PLAYWRIGHT:
                r = session.get(url2)
            elif USE_CURL_CFFI:
                r = session.get(url2, timeout=10)
            else:
                r = session.get(url2, timeout=10)
            
            # Try to parse JSON first, even if status code is not 200
            try:
                page_data = r.json()
                # If we got valid JSON with data field, proceed even if status code was not 200
                if 'data' in page_data:
                    for i in page_data['data']:
                        session_id_ep = str(i['session'])
                        all_episodes.append(session_id_ep)
                else:
                    # Got JSON but no data field
                    if r.status_code != 200:
                        print(f"Warning: Got status {r.status_code} for page {page} but response is JSON without 'data' field.")
                    continue
            except ValueError:
                # Not valid JSON - only raise error if status is not 200
                if r.status_code != 200:
                    print(f"Error: API returned status {r.status_code} with non-JSON response for page {page}.")
                    print(f"URL: {url2}")
                    print(f"Response preview: {r.text[:300]}...")
                    r.raise_for_status()  # This will raise the actual error
                else:
                    print(f"Error: Invalid JSON response for page {page}")
                    continue
        except requests.exceptions.RequestException as e:
            print(f"Error: Failed to fetch page {page}. {str(e)}")
            print(f"URL: {url2}")
            continue
    
    # Calculate the correct slice
    # Episodes are sorted by episode_asc, so when we fetch pages:
    # - Page 1 has episodes 1-30 (indices 0-29 in page 1's data)
    # - Page 2 has episodes 31-60 (indices 0-29 in page 2's data)
    # - etc.
    
    # We've collected all episodes from the needed pages in order
    # all_episodes[0] to all_episodes[29] = episodes from start_page
    # all_episodes[30] to all_episodes[59] = episodes from start_page + 1 (if fetched)
    # etc.
    
    # Calculate offset: position of start_episode within the fetched pages
    # Example: if start_page=2, start_episode=33:
    # - Page 2 starts at episode 31
    # - Episode 33 is at position (33-31) = 2 in page 2
    # - But since we're concatenating pages, we need: (start_page - start_page) * 30 + position_in_page
    # - Which simplifies to just: position_in_page = (start_episode - 1) % 30
    
    # However, if we fetch multiple pages, we need to account for all previous pages
    # Actually, since we only fetch from start_page to end_page, the offset is:
    offset = (start_episode - 1) % 30
    
    # But wait - if start_page > 1, we're only fetching from start_page onwards
    # So the offset should be relative to the first page we fetched
    # If start_page = 2 and start_episode = 33:
    # - We fetch page 2, which has episodes 31-60
    # - Episode 33 is at index (33-31) = 2 in the fetched data
    # - So offset = (start_episode - ((start_page - 1) * 30 + 1)) = (33 - 31) = 2
    
    # Calculate the first episode number in start_page
    first_episode_in_start_page = ((start_page - 1) * 30) + 1
    offset = start_episode - first_episode_in_start_page
    
    # Calculate how many episodes we need
    count = end_episode - start_episode + 1
    
    # Extract the correct slice
    result = all_episodes[offset:offset + count]
    
    return result

#print(mid_apahe("e8e5a274-b2a0-ae45-de26-803004f3299b",[29,31]))


def dl_apahe1(anime_id: str, episode_ids: list) -> dict:
    """
    Get a list of download links for the given episode IDs asynchronously.
    
    Parameters:
        anime_id (str): The anime ID.
        episode_ids (list): List of episode IDs.
    
    Returns:
        A dictionary where keys are episode indices and values are lists of download link information.
    """
    global url, USE_PLAYWRIGHT, USE_CURL_CFFI, playwright_context
    urls = [f'{url}/play/{anime_id}/{episode_id}' for episode_id in episode_ids]
    
    # For episode pages (HTML), use regular requests instead of Playwright
    # Playwright can't be used from ThreadPoolExecutor threads
    # Create a regular requests session with cookies from Playwright if available
    import requests as req_lib
    req_session = req_lib.Session()
    
    # Copy headers and cookies from the main session
    if USE_PLAYWRIGHT and playwright_context:
        # Get cookies from Playwright context
        cookies = playwright_context.cookies()
        for cookie in cookies:
            req_session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', ''))
        # Copy headers
        req_session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://animepahe.si/',
        })
    elif USE_CURL_CFFI:
        # Use curl_cffi session directly (it should work with threads)
        req_session = session
    else:
        # Use cloudscraper session
        req_session = session
    
    # Use ThreadPoolExecutor for concurrent requests
    data_dict = {}
    
    def fetch_url(index, url):
        try:
            if USE_PLAYWRIGHT:
                # Use regular requests for Playwright (can't use Playwright from threads)
                response = req_session.get(url, timeout=10)
            elif USE_CURL_CFFI:
                response = req_session.get(url, timeout=10)
            else:
                response = req_session.get(url, timeout=10)
            # Try to parse even if status is not 200 (some sites return content with error codes)
            if response.status_code == 200 or (response.status_code != 200 and len(response.text) > 0):
                text = response.text
                data = re.findall(r'href="(?:([^\"]+)" target="_blank" class="dropdown-item">(?:[^\&]+)&middot; ([^\<]+))(?:<span class="badge badge-primary">(?:[^\&]+)</span> <span class="badge badge-warning text-capitalize">([^\<]+))?', text)
                if data:
                    return (index, data)
                elif response.status_code != 200:
                    print(f"Warning: Episode {episode_ids[index]} returned status {response.status_code}")
            else:
                print(f"Episode {episode_ids[index]} could not be fetched (status: {response.status_code}).")
        except Exception as e:
            print(f"Episode {episode_ids[index]} could not be fetched: {str(e)}")
        return (index, None)
    
    # Use ThreadPoolExecutor for concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_url, index, url): index for index, url in enumerate(urls)}
        for future in as_completed(futures):
            index, data = future.result()
            if data is not None:
                data_dict[index] = data

    return data_dict

# print(dl_apahe1("13e4f8aa-169f-41cc-b7a1-218c88e3b8d2",["9ea4686f8cd114f3d9c065ab113b49a637f8b23dda5bebcf3c7a1aca20e8e371","d8c696836ba4bbdaff7ad3ca5450b410bbf7eec81832f167c3f7d8231eeaa5e1"]))
# print(dl_apahe1("13e4f8aa-169f-41cc-b7a1-218c88e3b8d2","d8c696836ba4bbdaff7ad3ca5450b410bbf7eec81832f167c3f7d8231eeaa5e1"))


def dl_apahe2(url: str) -> str:
    """
    Follow a redirect link to get the final download link.
    
    Parameters:
        url (str): The redirect link.
    
    Returns:
        The final download link.
    """
    try:
        if USE_PLAYWRIGHT:
            # Use Playwright to wait for the redirect page to load
            page = playwright_context.new_page()
            try:
                # Visit the page and wait for it to load
                page.goto(url, wait_until='load', timeout=30000)
                
                # Wait a bit for any redirects or JavaScript to execute
                page.wait_for_timeout(2000)
                
                # Try to find the kwik.cx link in the page
                # First check if we've been redirected to kwik.cx
                current_url = page.url
                if 'kwik.cx' in current_url:
                    page.close()
                    return current_url
                
                # Otherwise, look for the link in the page content
                text = page.evaluate("() => document.body ? document.body.textContent : document.documentElement.textContent")
                redirect_links = re.findall(r'(https://kwik\.cx/[^\s"\'<>]+)', text)
                if redirect_links:
                    page.close()
                    return redirect_links[0]
                
                # Also check the HTML content
                html = page.content()
                redirect_links = re.findall(r'(https://kwik\.cx/[^\s"\'<>]+)', html)
                if redirect_links:
                    page.close()
                    return redirect_links[0]
                
                page.close()
                raise ValueError(f"No kwik.cx link found in response from {url}")
            except Exception as e:
                page.close()
                raise
        else:
            # Use regular requests with redirect following
            if USE_CURL_CFFI:
                r = session.get(url, timeout=10, allow_redirects=True)
            else:
                r = session.get(url, timeout=10, allow_redirects=True)
            
            # Check if we were redirected to kwik.cx
            if 'kwik.cx' in r.url:
                return r.url
            
            # Try to get the redirect link from the response text
            redirect_links = re.findall(r'(https://kwik\.cx/[^\s"\'<>]+)', r.text)
            if redirect_links:
                return redirect_links[0]
            
            # If no link found and status is not 200, raise error
            if r.status_code != 200:
                print(f"Warning: Got status {r.status_code} from {url}")
                # Don't raise for 302/301 redirects
                if r.status_code not in [301, 302, 303, 307, 308]:
                    r.raise_for_status()
            
            raise ValueError(f"No kwik.cx link found in response from {url}")
    except requests.exceptions.RequestException as e:
        print(f"Error: Failed to fetch redirect link from {url}. {str(e)}")
        raise

# print(dl_apahe2("https://pahe.win/HVLTy"))

def download_file(url, destination):
    if os.path.exists(destination):
        file_size = os.path.getsize(destination)
    else:
        file_size = 0

    global USE_PLAYWRIGHT, USE_CURL_CFFI, playwright_context
    headers = {'Range': f'bytes={file_size}-'} if file_size else None
    # For downloads, use regular requests (playwright not ideal for streaming)
    if USE_PLAYWRIGHT:
        # Use requests for downloads even if playwright is available
        import requests as req_lib
        # Convert Playwright cookies to requests format
        cookies_dict = {}
        if playwright_context:
            playwright_cookies = playwright_context.cookies()
            for cookie in playwright_cookies:
                cookies_dict[cookie['name']] = cookie['value']
        response = req_lib.get(url, headers=headers, stream=True, cookies=cookies_dict)
    elif USE_CURL_CFFI:
        response = session.get(url, headers=headers, stream=True, timeout=10)
    else:
        response = session.get(url, headers=headers, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    if response.status_code == 206:
        print("Downloading resumed successfully.")
    elif response.status_code == 200:
        print("Downloading")

    with open(destination, 'ab') as file, tqdm(
        desc=destination,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as bar:
        for data in response.iter_content(chunk_size=69420):
            bar.update(len(data))
            file.write(data)

