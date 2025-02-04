import requests
from bs4 import BeautifulSoup
import os
import json
from urllib.parse import urljoin, quote
import time
from PIL import Image
import io

class MiaohuaSpider:
    def __init__(self):
        self.base_url = "https://miaohua.sensetime.com/api/v2/public/gallery"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.save_dir = "miaohua_images"
        
    def create_save_dir(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
    def download_image(self, img_url, img_name):
        try:
            response = requests.get(img_url, headers=self.headers)
            if response.status_code == 200:
                # 将图片数据转换为PNG格式
                image = Image.open(io.BytesIO(response.content))
                # 修改文件名后缀为.png
                img_name = os.path.splitext(img_name)[0] + '.png'
                file_path = os.path.join(self.save_dir, img_name)
                # 保存为PNG格式
                image.save(file_path, 'PNG')
                return True
        except Exception as e:
            print(f"下载图片失败: {str(e)}")
        return False

    def parse_image_info(self, item):
        try:
            img_data = {
                'description': item.get('prompt', ''),
                'ratio': item.get('ratio', ''),
                'img_url': item.get('large', ''),
                'task_id': item.get('task_id', ''),
                'user_name': item.get('user_name', '')
            }
            return img_data
        except Exception as e:
            print(f"解析图片信息失败: {str(e)}")
            return None

    def crawl(self, page=1, per_page=30, query="春节"):
        try:
            params = {
                'page': page,
                'per_page': per_page,
                'query': query
            }
            
            response = requests.get(self.base_url, params=params, headers=self.headers)
            if response.status_code != 200:
                print(f"请求失败: {response.status_code}")
                return []

            data = response.json()
            if data.get('code') != 0:
                print("获取数据失败")
                return []

            image_list = []
            for item in data.get('info', {}).get('list', []):
                img_info = self.parse_image_info(item)
                if img_info:
                    # 检查图片是否已下载
                    img_name = f"{img_info['task_id']}.png"
                    if not os.path.exists(os.path.join(self.save_dir, img_name)):
                        image_list.append(img_info)
                        
                        if self.download_image(img_info['img_url'], img_name):
                            print(f"成功下载图片: {img_name}")
                            self.save_image_info(img_info)
                        time.sleep(1)
                    else:
                        print(f"图片 {img_name} 已存在，跳过下载")

            return image_list

        except Exception as e:
            print(f"爬取失败: {str(e)}")
            return []

    def save_image_info(self, img_info):
        json_file = os.path.join(self.save_dir, 'image_info.json')
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = []
            
            # 检查是否已存在相同的task_id
            if not any(item.get('task_id') == img_info['task_id'] for item in data):
                data.append(img_info)
                
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            else:
                print(f"图片 {img_info['task_id']} 信息已存在，跳过保存")
                
        except Exception as e:
            print(f"保存图片信息失败: {str(e)}")

def main():
    spider = MiaohuaSpider()
    spider.create_save_dir()
    
    for page in range(1, 2):
        print(f"正在爬取第{page}页...")
        images = spider.crawl(page=page)
        print(f"第{page}页爬取完成，获取到{len(images)}张图片信息")
        time.sleep(2)

if __name__ == "__main__":
    main()