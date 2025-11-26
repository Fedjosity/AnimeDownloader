import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# grequests removed - causes gevent conflicts with ThreadPoolExecutor
# import grequests
import requests
import re
import os
from tqdm import tqdm
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Lazy initialization handles: Playwright, curl_cffi, cloudscraper ---
USE_PLAYWRIGHT = False
USE_CURL_CFFI = False
playwright_instance = None
browser = None
playwright_context = None
session = None


def initialize_session():
    global USE_PLAYWRIGHT, USE_CURL_CFFI, playwright_instance, browser, playwright_context, session
    if session is not None:
        return
    try:
        from playwright.sync_api import sync_playwright
        USE_PLAYWRIGHT = True
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(headless=True)
        playwright_context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        class PlaywrightSession:
            def __init__(self, context):
                self.context = context
                self.cookies = []
            def get(self, url, **kwargs):
                page = self.context.new_page()
                response_obj = None
                def handle_response(response):
                    nonlocal response_obj
                    if url in response.url:
                        response_obj = response
                page.on("response", handle_response)
                try:
                    page.goto(url, wait_until='load', timeout=30000)
                    page.wait_for_timeout(1000)
                    import time
                    max_wait = 30
                    start_time = time.time()
                    text = ""
                    while time.time() - start_time < max_wait:
                        try:
                            page.wait_for_load_state('domcontentloaded', timeout=2000)
                            text = page.evaluate("() => { try { return document.body ? document.body.textContent : document.documentElement.textContent; } catch(e) { return ''; } }")
                            if text and text.strip():
                                stripped = text.strip()
                                if (stripped.startswith('{') or stripped.startswith('[')) and 'DDoS-Guard' not in text and 'Checking your browser' not in text:
                                    break
                                elif 'DDoS-Guard' in text or 'Checking your browser' in text:
                                    page.wait_for_timeout(500)
                                    continue
                                elif stripped.startswith('{') or stripped.startswith('['):
                                    break
                        except Exception:
                            page.wait_for_timeout(500)
                            continue
                        page.wait_for_timeout(500)
                    if not text or not text.strip() or ('DDoS-Guard' in text or 'Checking your browser' in text):
                        try:
                            page.wait_for_load_state('domcontentloaded', timeout=5000)
                            text = page.evaluate("() => { try { return document.body ? document.body.textContent : document.documentElement.textContent; } catch(e) { return ''; } }")
                        except:
                            pass
                    try:
                        page.wait_for_load_state('networkidle', timeout=5000)
                    except:
                        pass
                    if response_obj:
                        status_code = response_obj.status
                        response_headers = dict(response_obj.headers) if response_obj.headers else {}
                    else:
                        status_code = 200
                        response_headers = {}
                    if text and (text.strip().startswith('{') or text.strip().startswith('[')):
                        status_code = 200
                    elif 'DDoS-Guard' in text or 'Checking your browser' in text:
                        status_code = 403
                    self.cookies = self.context.cookies()
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
        return
    except (ImportError, Exception) as e:
        USE_PLAYWRIGHT = False
        import traceback
        print("\n[Playwright Initialization Error]\n", flush=True)
        traceback.print_exc()
        print("Falling back to curl_cffi", flush=True)
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
        return
    except ImportError:
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

def get_actual_episode_count(session_id: str) -> int:
    initialize_session()
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
            last_page_url = url + "api?m=release&id=" + session_id + "&sort=episode_asc&page=" + str(page_data['last_page'])
            if USE_PLAYWRIGHT:
                last_page_r = session.get(last_page_url)
            elif USE_CURL_CFFI:
                last_page_r = session.get(last_page_url, timeout=10)
            else:
                last_page_r = session.get(last_page_url, timeout=10)
            last_page_data = last_page_r.json()
            return (page_data['last_page'] - 1) * page_data['per_page'] + len(last_page_data.get('data', []))
        else:
            return len(page_data.get('data', []))
    except Exception as e:
        return 0

def search_apahe(query: str) -> list:
    initialize_session()
    global url, USE_PLAYWRIGHT, USE_CURL_CFFI
    search_url = url + "api?m=search&q=" + quote(query)
    data = None
    try:
        if USE_PLAYWRIGHT:
            response = session.get(search_url)
        elif USE_CURL_CFFI:
            response = session.get(search_url, timeout=10)
        else:
            response = session.get(search_url, timeout=10)
        content_type = response.headers.get('Content-Type', '').lower()
        try:
            data = response.json()
            if data and "data" in data:
                pass
            else:
                if response.status_code != 200:
                    print(f"Warning: Got status {response.status_code} but response is JSON without 'data' field.")
                    print(f"Response: {data}")
                return []
        except ValueError:
            if response.status_code != 200:
                print(f"Error: API returned status {response.status_code} with non-JSON response.")
                print(f"Content-Type: {content_type}")
                print(f"Response preview: {response.text[:300]}...")
                response.raise_for_status()
            else:
                print(f"Error: API returned invalid JSON. Status code: {response.status_code}")
                print(f"Content-Type: {content_type}")
                print(f"Response preview: {response.text[:300]}...")
            return []
        if 'html' in content_type and response.status_code != 200:
            print(f"Error: API returned HTML instead of JSON. The API endpoint might have changed.")
            print(f"URL: {search_url}")
            print(f"Response preview: {response.text[:300]}...")
            return []
    except requests.exceptions.RequestException as e:
        print(f"URL: {search_url}")
        return []
    if data is None:
        return []
    if "data" not in data:
        return []
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
            print(f"  [{idx}/{len(anime_list)}] Fetching episode count for {i['title']}...", end='\r')
            actual_episodes = get_actual_episode_count(session_id=i['session'])
            if actual_episodes > 0:
                hmm.append(actual_episodes)
            else:
                hmm.append(i['episodes'])
            hmm.append(i['status'])
            hmm.append(i['year'])
            hmm.append(i['score'])
            hmm.append(i['session'])
            clean_data.append(hmm)
        print()
    except (KeyError, TypeError) as e:
        print(f"Error processing anime data: {str(e)}")
        print(f"Sample data item: {anime_list[0] if anime_list else 'No items'}")
        return []
    return clean_data

def mid_apahe(session_id: str , episode_range: list) -> list:
    initialize_session()
    # Calculate which pages we need to fetch
    # API returns 30 episodes per page, pages start at 1
    start_episode = episode_range[0]
    end_episode = episode_range[1]
    
    # Calculate page numbers (pages are 1-indexed)
    start_page = ((start_episode - 1) // 30) + 1
    end_page = ((end_episode - 1) // 30) + 1
    
    # Store episodes as dict: {episode_number: session_id}
    # This ensures we get the correct episodes even if there are gaps
    episodes_dict = {}
    
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
                        # Get the actual episode number from the API response
                        episode_num = i.get('episode', None)
                        if episode_num is not None:
                            session_id_ep = str(i['session'])
                            episodes_dict[episode_num] = session_id_ep
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
    
    # Now extract episodes in the requested range based on actual episode numbers
    # Return a list of tuples: (episode_number, session_id)
    # This allows the caller to know which episode number each session ID corresponds to
    result = []
    missing_episodes = []
    for ep_num in range(start_episode, end_episode + 1):
        if ep_num in episodes_dict:
            result.append((ep_num, episodes_dict[ep_num]))
        else:
            # Episode not found - this might indicate a gap in the series
            missing_episodes.append(ep_num)
    
    if missing_episodes:
        print(f"Warning: {len(missing_episodes)} episode(s) not found in API response: {missing_episodes}")
    else:
        print(f"Successfully fetched {len(result)} episode(s) from API")
    
    return result

def dl_apahe1(anime_id: str, episode_ids: list) -> dict:
    initialize_session()
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
    # Reduce max_workers to avoid overwhelming the server and reduce gevent conflicts
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_url, index, url): index for index, url in enumerate(urls)}
        for future in as_completed(futures):
            try:
                index, data = future.result()
                if data is not None:
                    data_dict[index] = data
            except Exception as e:
                # Handle any exceptions from the future
                print(f"Error processing future: {str(e)}")
                continue

    # Retry failed episodes sequentially (to avoid gevent conflicts)
    failed_indices = []
    for index, url in enumerate(urls):
        if index not in data_dict:
            failed_indices.append((index, url))
    
    if failed_indices:
        print(f"Retrying {len(failed_indices)} failed episode(s) sequentially...")
        for index, url in failed_indices:
            try:
                if USE_PLAYWRIGHT:
                    response = req_session.get(url, timeout=30)
                elif USE_CURL_CFFI:
                    response = req_session.get(url, timeout=30)
                else:
                    response = req_session.get(url, timeout=30)
                if response.status_code == 200 or (response.status_code != 200 and len(response.text) > 0):
                    text = response.text
                    data = re.findall(r'href="(?:([^\"]+)" target="_blank" class="dropdown-item">(?:[^\&]+)&middot; ([^\<]+))(?:<span class="badge badge-primary">(?:[^\&]+)</span> <span class="badge badge-warning text-capitalize">([^\<]+))?', text)
                    if data:
                        data_dict[index] = data
                        print(f"Successfully retried episode {index + 1}")
            except Exception as e:
                print(f"Retry failed for episode {index + 1}: {str(e)}")

    return data_dict

def dl_apahe2(url: str) -> str:
    initialize_session()
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

def download_file(url, destination, max_retries=5):
    initialize_session()
    import time
    import requests.exceptions
    
    retry_count = 0
    while retry_count < max_retries:
        try:
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
                response = req_lib.get(url, headers=headers, stream=True, cookies=cookies_dict, timeout=(30, 300))
            elif USE_CURL_CFFI:
                response = session.get(url, headers=headers, stream=True, timeout=(30, 300))
            else:
                response = session.get(url, headers=headers, stream=True, timeout=(30, 300))
            
            total_size = int(response.headers.get('content-length', 0))
            if file_size > 0:
                total_size = file_size + total_size  # Adjust total size for resume
            
            if response.status_code == 206:
                print(f"Resuming download from byte {file_size}...")
            elif response.status_code == 200:
                if file_size > 0:
                    print(f"Server doesn't support resume. Starting fresh download...")
                    os.remove(destination)
                    file_size = 0
                    # Retry without Range header
                    if USE_PLAYWRIGHT:
                        response = req_lib.get(url, stream=True, cookies=cookies_dict, timeout=(30, 300))
                    elif USE_CURL_CFFI:
                        response = session.get(url, stream=True, timeout=(30, 300))
                    else:
                        response = session.get(url, stream=True, timeout=(30, 300))
                    total_size = int(response.headers.get('content-length', 0))
                print("Downloading...")
            else:
                response.raise_for_status()

            with open(destination, 'ab') as file, tqdm(
                desc=os.path.basename(destination),
                total=total_size,
                initial=file_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=69420):
                    if not data:
                        break
                    bar.update(len(data))
                    file.write(data)
                    file.flush()  # Ensure data is written immediately
            
            # Download completed successfully
            return
            
        except (requests.exceptions.ChunkedEncodingError, 
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.RequestException) as e:
            retry_count += 1
            if retry_count < max_retries:
                wait_time = min(2 ** retry_count, 60)  # Exponential backoff, max 60 seconds
                print(f"\nConnection error: {str(e)}")
                print(f"Retrying in {wait_time} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"\nFailed to download after {max_retries} attempts.")
                raise
        except KeyboardInterrupt:
            print("\nDownload interrupted by user.")
            raise
        except Exception as e:
            print(f"\nUnexpected error during download: {str(e)}")
            raise

