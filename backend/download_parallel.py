import os
import sys
import time
import shutil
import requests
from concurrent.futures import ThreadPoolExecutor

def download_chunk(url, start_byte, end_byte, chunk_file):
    headers = {"Range": f"bytes={start_byte}-{end_byte}"}
    for attempt in range(10):
        try:
            r = requests.get(url, headers=headers, stream=True, timeout=20)
            r.raise_for_status()
            with open(chunk_file, "wb") as f:
                for chunk in r.iter_content(chunk_size=512*1024):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            print(f"Error downloading chunk {start_byte}-{end_byte} (attempt {attempt+1}): {e}")
            time.sleep(2)
    return False

def download_parallel(url, dest_path, num_connections=16):
    print(f"Requesting head info for: {url}")
    r = requests.head(url, allow_redirects=True, timeout=20)
    total_size = int(r.headers.get('content-length', 0))
    if total_size == 0 or r.status_code != 200:
        # Fallback to GET for redirect/size checking
        r = requests.get(url, stream=True, allow_redirects=True, timeout=20)
        total_size = int(r.headers.get('content-length', 0))
        r.close()
    
    resolved_url = r.url
    print(f"Resolved URL: {resolved_url}")
    print(f"File size: {total_size / (1024*1024):.2f} MB")
    
    if total_size == 0:
        raise ValueError("Failed to get content-length.")
        
    chunk_size = total_size // num_connections
    futures = []
    chunk_files = []
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=num_connections) as executor:
        for i in range(num_connections):
            start = i * chunk_size
            end = total_size - 1 if i == num_connections - 1 else (i + 1) * chunk_size - 1
            chunk_file = f"{dest_path}.chunk.{i}"
            chunk_files.append(chunk_file)
            futures.append(executor.submit(download_chunk, url, start, end, chunk_file))
            
        # Monitor progress
        while True:
            completed = sum(1 for f in futures if f.done())
            # Calculate current download size
            current_bytes = 0
            for chunk_file in chunk_files:
                if os.path.exists(chunk_file):
                    current_bytes += os.path.getsize(chunk_file)
            
            elapsed = time.time() - start_time
            speed = current_bytes / (1024*1024) / elapsed if elapsed > 0 else 0
            print(f"Chunks: {completed}/{num_connections} completed | Downloaded: {current_bytes / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({current_bytes/total_size*100.0:.1f}%) | Speed: {speed:.2f} MB/s", flush=True)
            
            if completed == num_connections:
                break
            time.sleep(3)
            
    # Verify all threads succeeded
    success = True
    for f in futures:
        if not f.result():
            success = False
            
    if not success:
        print("Some chunks failed to download. Clean up chunks.")
        for chunk_file in chunk_files:
            if os.path.exists(chunk_file):
                os.remove(chunk_file)
        raise RuntimeError("Download failed.")
        
    # Merge files
    print("All chunks downloaded successfully. Merging files...")
    with open(dest_path, "wb") as dest:
        for chunk_file in chunk_files:
            with open(chunk_file, "rb") as src:
                shutil.copyfileobj(src, dest)
            os.remove(chunk_file)
    print(f"Download complete: {dest_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python download_parallel.py <url> <dest_path>")
        sys.exit(1)
    download_parallel(sys.argv[1], sys.argv[2])
