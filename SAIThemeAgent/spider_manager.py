import os
import argparse
from datetime import datetime
from miaohua_spider import MiaohuaSpider
from recraft_spider import RecraftSpider
import time

class SpiderManager:
    def __init__(self, base_dir="spider_data"):
        self.base_dir = base_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_save_dir(self, spider_name):
        """创建保存目录，使用时间戳区分不同批次"""
        save_dir = os.path.join(self.base_dir, spider_name, self.timestamp)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        return save_dir
    
    def run_miaohua_spider(self, query="春节", pages=1):
        """运行妙绘AI爬虫"""
        save_dir = self.create_save_dir("miaohua")
        print(f"开始运行妙绘AI爬虫，保存目录: {save_dir}")
        
        spider = MiaohuaSpider()
        spider.save_dir = save_dir
        spider.create_save_dir()
        
        total_images = 0
        for page in range(1, pages + 1):
            print(f"正在爬取第{page}页...")
            images = spider.crawl(page=page, query=query)
            total_images += len(images)
            print(f"第{page}页爬取完成，获取到{len(images)}张图片信息")
        
        print(f"妙绘AI爬虫运行完成，共获取{total_images}张图片")
        return save_dir
    
    def run_recraft_spider(self, query=None, time_limit=None):
        """运行Recraft爬虫"""
        save_dir = self.create_save_dir("recraft")
        print(f"开始运行Recraft爬虫，保存目录: {save_dir}")
        
        spider = RecraftSpider(query=query, time_limit=time_limit)
        spider.save_dir = save_dir
        spider.create_save_dir()
        
        start_time = time.time()
        images = spider.crawl()
        end_time = time.time()
        
        print(f"Recraft爬虫运行完成，共获取{len(images)}张图片")
        print(f"总耗时: {(end_time - start_time):.2f} 秒")
        return save_dir
    
    def run_all_spiders(self, miaohua_query="春节", recraft_query=None, 
                       miaohua_pages=1, recraft_time_limit=None):
        """运行所有爬虫"""
        results = {}
        
        # 运行妙绘AI爬虫
        results['miaohua'] = self.run_miaohua_spider(
            query=miaohua_query, 
            pages=miaohua_pages
        )
        
        # 运行Recraft爬虫
        results['recraft'] = self.run_recraft_spider(
            query=recraft_query,
            time_limit=recraft_time_limit
        )
        
        return results

def parse_args():
    parser = argparse.ArgumentParser(description='AI图片爬虫管理器')
    parser.add_argument('--spider', type=str, choices=['all', 'miaohua', 'recraft'],
                      default='recraft', help='选择要运行的爬虫')
    parser.add_argument('--miaohua-query', type=str, default='春节',
                      help='妙绘AI搜索关键词')
    parser.add_argument('--recraft-query', type=str, default='春节',
                      help='Recraft搜索关键词')
    parser.add_argument('--miaohua-pages', type=int, default=1,
                      help='妙绘AI爬取页数')
    parser.add_argument('--save-dir', type=str, default='spider_data',
                      help='数据保存根目录')
    parser.add_argument('--recraft-time-limit', type=int, default=100,
                      help='Recraft爬虫运行时间限制（秒），默认无限制')
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 初始化爬虫管理器
    manager = SpiderManager(base_dir=args.save_dir)
    
    if args.spider == 'all':
        results = manager.run_all_spiders(
            miaohua_query=args.miaohua_query,
            recraft_query=args.recraft_query,
            miaohua_pages=args.miaohua_pages,
            recraft_time_limit=args.recraft_time_limit
        )
        print("\n所有爬虫运行完成！")
        for spider_name, save_dir in results.items():
            print(f"{spider_name} 数据保存在: {save_dir}")
            
    elif args.spider == 'miaohua':
        save_dir = manager.run_miaohua_spider(
            query=args.miaohua_query,
            pages=args.miaohua_pages
        )
        print(f"\n妙绘AI爬虫运行完成！数据保存在: {save_dir}")
        
    elif args.spider == 'recraft':
        save_dir = manager.run_recraft_spider(
            query=args.recraft_query,
            time_limit=args.recraft_time_limit
        )
        print(f"\nRecraft爬虫运行完成！数据保存在: {save_dir}")

if __name__ == "__main__":
    main()