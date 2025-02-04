import json
import os
from datetime import datetime
from typing import Union, List, Dict, Optional
import argparse
import pandas as pd
import requests

class LLMClient:
    def __init__(self, request_timeout: int, model: str):
        """初始化LLM客户端"""
        self.model = model
        self.request_timeout = request_timeout
        self._setup_url_and_token()
        
    def _setup_url_and_token(self):
        """设置URL和访问令牌"""
        model_urls = {
            "deucalion": "https://edge.microsoft.com/taggrouptitlegeneration/api/actionai/proxyv3?modelName=deucalionv1",
            "gpt4turbo": "https://edge.microsoft.com/taggrouptitlegeneration/api/actionai/proxyv3?modelName=gpt4turbo",
            "gpt4o": "https://edge.microsoft.com/taggrouptitlegeneration/api/actionai/proxyv3?modelName=gpt4o"
        }
        self.url = model_urls.get(self.model)
        self.access_token = ""  # 需要设置访问令牌
        
    def get_response_text(self, prompt: str) -> str:
        """获取LLM响应"""
        if not self.access_token:
            raise ValueError("access_token is empty")
            
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.access_token
        }
        
        data = {
            "prompt": prompt,
            "temperature": 0.8,
            "max_tokens": 1024 * 8,
            "top_p": 1,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "stop": ["```", "<|im_end|>"]
        }
        
        for _ in range(3):
            try:
                response = requests.post(
                    self.url,
                    headers=headers,
                    json=data,
                    timeout=self.request_timeout
                )
                if response.status_code == 200:
                    return response.text
            except Exception as e:
                print(f"Request error: {e}")
                continue
        return ""

class PromptGenerator:
    def __init__(self, system_prompt_file: str, llm_client: LLMClient):
        """初始化提示生成器"""
        self.system_prompt = self._read_system_prompt(system_prompt_file)
        self.llm_client = llm_client
        
    def _read_system_prompt(self, file_path: str) -> str:
        """读取系统提示文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
            
    def _format_input_prompt(self, description: str) -> str:
        """格式化输入提示"""
        return f"{description}"
        
    def generate_from_json(self, json_file: str) -> List[Dict]:
        """从JSON文件生成提示"""
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        results = []
        for item in data:
            # 从prompt字段获取描述
            if 'prompt' in item and item['prompt']:
                result = self.generate_single_prompt(item['prompt'])
                results.append(result)
                print(f"处理描述: {item['prompt'][:50]}...")
            else:
                print(f"跳过无效描述项: {item}")
        return results
        
    def generate_from_input(self, description: str) -> Dict:
        """从用户输入生成提示"""
        return self.generate_single_prompt(description)
        
    def generate_single_prompt(self, description: str) -> Dict:
        """生成单个提示的实现"""
        try:
            # 构建完整的提示
            format_description = self._format_input_prompt(description)
            full_prompt = self.system_prompt.replace("MESSAGE", format_description)
            
            # 调用LLM获取响应
            response = self.llm_client.get_response_text(full_prompt)
            if not response:
                raise Exception("LLM返回空响应")
            
            # 解析JSON响应
            result = json.loads(response)
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return self._get_error_result(description)
        except Exception as e:
            print(f"处理错误: {e}")
            return self._get_error_result(description)
            
    def _get_error_result(self, description: str) -> Dict:
        """返回错误结果的统一格式"""
        return {
            "original_prompt": description,
            "inspired_prompt": "处理失败",
            "analysis": {
                "main_elements": [],
                "scene_type": "未知",
                "art_style": "未知",
                "mood": "未知",
                "composition": "未知",
                "color_scheme": "未知"
            }
        }

    def extract_valid_prompts(self, json_file: str, output_file: str = "valid_prompts.txt"):
        """
        Extract and save valid inspired prompts from generated results
        
        Args:
            json_file: Path to the generated prompts JSON file
            output_file: Path to save the extracted prompts (default: valid_prompts.txt)
        """
        try:
            # Read the JSON file
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
                
            # Extract valid prompts
            valid_prompts = []
            for result in results:
                if (result.get('inspired_prompt') and 
                    result['inspired_prompt'] != "处理失败" and 
                    result['inspired_prompt'] != "Processing failed"):
                    valid_prompts.append(result['inspired_prompt'])
            
            # Save to file
            with open(output_file, 'w', encoding='utf-8') as f:
                for prompt in valid_prompts:
                    f.write(f"{prompt}\n")
                    
            print(f"Successfully extracted {len(valid_prompts)} valid prompts to {output_file}")
            return valid_prompts
            
        except Exception as e:
            print(f"Error extracting valid prompts: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description='AI Image Description Generator')
    parser.add_argument('--input_type', type=str, choices=['json', 'manual'], 
                      default='manual', help='输入类型：json文件或手动输入')
    parser.add_argument('--json_file', type=str, default='recraft_images/image_info.json',
                      help='输入的JSON文件路径')
    parser.add_argument('--output_file', type=str, default='generated_prompts.json',
                      help='输出文件路径')
    parser.add_argument('--system_prompt', type=str, default='prompt_inspiration.md',
                      help='系统提示文件路径')
    parser.add_argument('--timeout', type=int, default=420, help='请求超时时间')
    parser.add_argument('--model', type=str, default='gpt4o', 
                      choices=['deucalion', 'gpt4turbo', 'gpt4o'],
                      help='使用的模型')
    parser.add_argument('--extract_prompts', action='store_true',
                      help='Extract valid prompts from generated results')
    parser.add_argument('--valid_prompts_file', type=str, default='valid_prompts.tsv',
                      help='Output file for valid prompts')
    
    args = parser.parse_args()
    
    # Initialize LLM client
    llm_client = LLMClient(args.timeout, args.model)
    
    # Initialize generator
    generator = PromptGenerator(args.system_prompt, llm_client)
    
    if args.extract_prompts:
        generator.extract_valid_prompts(args.output_file, args.valid_prompts_file)
    elif args.input_type == 'json':
        # 从JSON文件生成
        results = generator.generate_from_json(args.json_file)
        
        # 保存结果
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"已生成 {len(results)} 个提示并保存到 {args.output_file}")
    else:
        # 手动输入模式
        while True:
            description = input("\n请输入图片描述 (输入 'q' 退出):\n")
            if description.lower() == 'q':
                break
            result = generator.generate_from_input(description)
            print("\n生成的提示:")
            print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()