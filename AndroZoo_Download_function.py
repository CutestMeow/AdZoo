import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


def extract_sha256_from_json(json_path, output_dir):
    """
    从 JSON 文件中提取所有 SHA256 键，并将其写入 TXT 文件。
    返回生成的 TXT 文件路径 + SHA256-类别名映射字典（新增）。
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 读取 JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    # 新增：提取 SHA256-类别名映射（JSON键=SHA256，值=类别名）
    sha_category_map = {}
    if isinstance(data, dict):
        sha_category_map = data  # 直接获取键值对（SHA256: 类别名）
        sha_list = list(data.keys())
    elif isinstance(data, list):
        sha_list = [item for item in data if isinstance(item, str)]
        # 如果列表中是对象，则调整为：sha_list = [item['sha256'] for item in data]
    else:
        raise ValueError("Unsupported JSON structure for extracting SHA256")

    # 写入 TXT
    txt_path = os.path.join(output_dir, 'sha256_list_from_json.txt')
    with open(txt_path, 'w') as f:
        for sha in sha_list:
            f.write(sha + '\n')

    print(f"✅ 提取到 {len(sha_list)} 条 SHA256，已保存至 {txt_path}")
    # 新增：返回txt路径 + 类别映射字典
    return txt_path, sha_category_map

# 生成下载链接列表 TXT 文件
def generate_download_link(filtered_file, output_dir, apikey):
    links_file = os.path.join(output_dir, f'download_links.txt')
    with open(filtered_file, 'r') as f:
        sha256_list = [line.strip() for line in f if line.strip()]

    with open(links_file, 'w') as f:
        for sha in sha256_list:
            url = f"https://androzoo.uni.lu/api/download?apikey={apikey}&sha256={sha}"
            f.write(url + '\n')

    print(f"✅ 下载链接已生成，共 {len(sha256_list)} 条，保存在 {links_file}")
    return links_file

# 多线程下载 APK 文件
def download_apk_multithreaded(links_file, output_dir, sha_category_map, num_threads=20):
    # 新增：接收 SHA256-类别映射字典
    os.makedirs(output_dir, exist_ok=True)

    with open(links_file, 'r') as f:
        url_list = [line.strip() for line in f if line.strip()]

    def download_task(url):
        sha = url.split('sha256=')[-1]
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                # 新增：根据SHA256获取类别名，创建对应文件夹
                category = sha_category_map.get(sha, "未分类")  # 无类别则归为"未分类"
                category_dir = os.path.join(output_dir, category)
                os.makedirs(category_dir, exist_ok=True)  # 确保类别文件夹存在
                
                # 新增：文件保存到对应类别文件夹
                path = os.path.join(category_dir, sha + '.apk')
                with open(path, 'wb') as apk:
                    apk.write(resp.content)
                print(f"下载成功: {sha} (类别：{category})")
            else:
                print(f"下载失败: {sha}, 状态码 {resp.status_code}")
        except Exception as e:
            print(f"下载异常: {sha}, {e}")

    with tqdm(total=len(url_list), desc='下载进度') as pbar:
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            for url in url_list:
                executor.submit(lambda u=url: (download_task(u), pbar.update(1)))

# ------------------- 调用示例（仅新增传递类别映射的逻辑） -------------------
if __name__ == "__main__":
    # 示例调用步骤（仅需新增接收类别映射、传递给下载函数）
    json_path = "adware.json"
    output_dir = "F:\Studies\dataset/adware/apks"
    apikey = ""
    
    # 1. 提取SHA256（新增接收类别映射）
    txt_path, sha_category_map = extract_sha256_from_json(json_path, output_dir)
    # 2. 生成下载链接
    links_file = generate_download_link(txt_path, output_dir, apikey)
    # 3. 下载（新增传递类别映射）
    download_apk_multithreaded(links_file, output_dir, sha_category_map, num_threads=15)