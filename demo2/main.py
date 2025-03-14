#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SUMO网络生成器与大语言模型集成主程序

此程序将自然语言描述转换为SUMO网络参数并生成网络
支持交互式模式、命令行描述模式和直接可视化现有网络
"""

import os
import argparse
import sys

# 导入配置文件中的环境变量
try:
    from config import *
    # 确保环境变量设置正确
    if 'API_KEY' in globals() and 'DEEPSEEK_API_KEY' not in os.environ:
        os.environ['DEEPSEEK_API_KEY'] = API_KEY
        print(f"已设置DEEPSEEK_API_KEY环境变量")
except ImportError:
    # 如果找不到配置文件，仍然可以继续执行，但可能需要手动设置环境变量
    print("Warning: config.py not found. Environment variables may need to be set manually.")

# 导入本地模块
from sumo_llm_integration import SumoLLMIntegration
from cli_handler import CLIHandler
from visualizers import visualize_network

def main():
    """主函数，程序入口点"""
    # 创建集成类实例
    try:
        # 如果有配置文件中的API设置，直接传递给集成类
        llm_kwargs = {}
        if 'API_KEY' in globals():
            llm_kwargs['api_key'] = API_KEY
        if 'API_URL' in globals():
            llm_kwargs['api_url'] = API_URL
        if 'API_MODEL' in globals():
            llm_kwargs['model'] = API_MODEL
            
        # 使用正确的参数格式初始化SumoLLMIntegration
        integration = SumoLLMIntegration(llm_provider="deepseek", **llm_kwargs)
        
        # 创建CLI处理器
        cli = CLIHandler(integration)
        
        # 运行命令行界面
        cli.run()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序运行时出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 