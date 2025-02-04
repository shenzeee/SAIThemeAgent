import requests
from bs4 import BeautifulSoup
import os
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image
import io
from urllib.parse import quote

class RecraftSpider:
    def __init__(self, query=None, time_limit=None):
        self.base_url = "https://www.recraft.ai/community"
        self.query = query
        self.save_dir = "recraft_images"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        self.time_limit = time_limit  # 爬虫运行时间限制（秒）
        
    def setup_driver(self):
        # 设置Chrome选项
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--disable-gpu')
        options.add_argument(f'user-agent={self.headers["User-Agent"]}')
        return webdriver.Chrome(options=options)
        
    def create_save_dir(self):
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
            
    def download_image(self, img_url, img_name):
        try:
            response = requests.get(img_url, headers=self.headers)
            if response.status_code == 200:
                # 将图片数据转换为PNG格式
                image = Image.open(io.BytesIO(response.content))
                file_path = os.path.join(self.save_dir, img_name)
                # 保存为PNG格式
                image.save(file_path, 'PNG')
                return True
        except Exception as e:
            print(f"下载图片失败: {str(e)}")
        return False

    def get_image_dimensions(self, img_element):
        """获取图片尺寸"""
        try:
            width = img_element.get_attribute('width')
            height = img_element.get_attribute('height')
            return f"{width}x{height}" if width and height else "未知"
        except:
            return "未知"

    def parse_image_info(self, img):
        """解析图片信息，统一输出格式"""
        try:
            img_url = img.get_attribute('src')
            prompt = img.get_attribute('alt')
            width = img.get_attribute('width')
            height = img.get_attribute('height')
            
            # 从URL中提取唯一标识符
            task_id = img_url.split('/')[-1].split('@')[0]
            
            image_info = {
                'description': prompt,
                'ratio': f"{width}x{height}",
                'img_url': img_url,
                'task_id': task_id,
                'user_name': None  # Recraft不提供用户名
            }
            return image_info
        except Exception as e:
            print(f"解析图片信息失败: {str(e)}")
            return None

    def get_url(self):
        """构建带查询参数的URL"""
        if self.query:
            return f"{self.base_url}?q={quote(self.query)}"
        return self.base_url

    def crawl(self):
        driver = self.setup_driver()
        start_time = time.time()
        try:
            url = self.get_url()
            driver.get(url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "img.c-crbeIZ"))
            )
            
            image_data = []
            while True:
                # 检查是否达到时间限制
                if self.time_limit and (time.time() - start_time) > self.time_limit:
                    print(f"已达到设定的时间限制 {self.time_limit} 秒，停止爬取")
                    break
                
                # 获取当前页面高度
                last_height = driver.execute_script("return document.body.scrollHeight")
                
                # 滚动到页面底部
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # 获取新的页面高度
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                # 获取当前可见的所有图片
                images = driver.find_elements(By.CSS_SELECTOR, "img.c-crbeIZ")
                
                for img in images:
                    try:
                        img_info = self.parse_image_info(img)
                        if img_info:
                            img_name = f"{img_info['task_id']}.png"
                            if not os.path.exists(os.path.join(self.save_dir, img_name)):
                                image_data.append(img_info)
                                
                                if self.download_image(img_info['img_url'], img_name):
                                    print(f"成功下载图片: {img_name}")
                                    self.save_image_info(img_info)
                                time.sleep(1)
                            else:
                                print(f"图片 {img_name} 已存在，跳过下载")
                        
                    except Exception as e:
                        print(f"处理图片失败: {str(e)}")
                        continue
                
                # 检查是否到达页面底部
                if new_height == last_height:
                    print("已到达页面底部")
                    break
                    
            return image_data

        except Exception as e:
            print(f"爬取失败: {str(e)}")
            return []
            
        finally:
            driver.quit()

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
    # 示例：设置30分钟的时间限制
    time_limit = 30 * 60  # 30分钟，单位：秒
    query = "龙年的题材"
    
    # 使用时间限制（可以设置为None来禁用）
    spider = RecraftSpider(query=query, time_limit=time_limit)
    spider.create_save_dir()
    
    start_time = time.time()
    images = spider.crawl()
    end_time = time.time()
    
    print(f"爬取完成，共获取{len(images)}张图片信息")
    print(f"总耗时: {(end_time - start_time):.2f} 秒")

if __name__ == "__main__":
    main()