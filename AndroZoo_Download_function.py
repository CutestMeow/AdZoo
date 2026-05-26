import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


def extract_sha256_from_json(json_path, output_dir):
    """
    Extract all SHA256 keys from a JSON file and write them to a TXT file.
    Returns the generated TXT file path and a SHA256-to-category mapping dictionary.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Read JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Extract SHA256-to-category mapping (JSON key = SHA256, value = category name)
    sha_category_map = {}
    if isinstance(data, dict):
        sha_category_map = data
        sha_list = list(data.keys())
    elif isinstance(data, list):
        sha_list = [item for item in data if isinstance(item, str)]
        # If the list contains objects, adjust to: sha_list = [item['sha256'] for item in data]
    else:
        raise ValueError("Unsupported JSON structure for extracting SHA256")

    # Write to TXT
    txt_path = os.path.join(output_dir, 'sha256_list_from_json.txt')
    with open(txt_path, 'w') as f:
        for sha in sha_list:
            f.write(sha + '\n')

    print(f"✅ Extracted {len(sha_list)} SHA256 entries, saved to {txt_path}")
    return txt_path, sha_category_map


def generate_download_links(filtered_file, output_dir, apikey):
    """Generate a TXT file containing download links for each SHA256."""
    links_file = os.path.join(output_dir, 'download_links.txt')
    with open(filtered_file, 'r') as f:
        sha256_list = [line.strip() for line in f if line.strip()]

    with open(links_file, 'w') as f:
        for sha in sha256_list:
            url = f"https://androzoo.uni.lu/api/download?apikey={apikey}&sha256={sha}"
            f.write(url + '\n')

    print(f"✅ Generated {len(sha256_list)} download links, saved to {links_file}")
    return links_file


def download_apk_multithreaded(links_file, output_dir, sha_category_map, num_threads=20):
    """
    Download APK files using multiple threads.
    Files are saved into subdirectories named after their category (from sha_category_map).
    """
    os.makedirs(output_dir, exist_ok=True)

    with open(links_file, 'r') as f:
        url_list = [line.strip() for line in f if line.strip()]

    def download_task(url):
        sha = url.split('sha256=')[-1]
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                # Retrieve category name from the mapping, default to "Uncategorized"
                category = sha_category_map.get(sha, "Uncategorized")
                category_dir = os.path.join(output_dir, category)
                os.makedirs(category_dir, exist_ok=True)

                file_path = os.path.join(category_dir, sha + '.apk')
                with open(file_path, 'wb') as apk:
                    apk.write(resp.content)
                print(f"Download succeeded: {sha} (category: {category})")
            else:
                print(f"Download failed: {sha}, status code {resp.status_code}")
        except Exception as e:
            print(f"Download exception: {sha}, {e}")

    with tqdm(total=len(url_list), desc='Download Progress') as pbar:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for url in url_list:
                executor.submit(lambda u=url: (download_task(u), pbar.update(1)))


# ------------------- Example usage -------------------
if __name__ == "__main__":
    # Example workflow (only need to capture and pass the category mapping)
    json_path = "adware_files.json"
    output_dir = ""
    apikey = ""

    # 1. Extract SHA256 values (receive category mapping)
    txt_path, sha_category_map = extract_sha256_from_json(json_path, output_dir)
    # 2. Generate download links
    links_file = generate_download_links(txt_path, output_dir, apikey)
    # 3. Download using multiple threads (pass category mapping)
    download_apk_multithreaded(links_file, output_dir, sha_category_map, num_threads=15)
