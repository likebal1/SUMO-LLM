import os
import sys
import subprocess
from typing import Dict, Any, Tuple, Optional, Union, List

from llm_interface import get_llm_interface
from network_generators import NetworkGenerator
from visualizers import visualize_network

class SumoLLMIntegration:
    """
    SUMO与LLM集成的核心类，负责协调各个组件
    """
    
    def __init__(self, llm_provider: str = "deepseek", **llm_kwargs):
        """
        初始化SUMO-LLM集成
        
        参数:
            llm_provider: LLM提供商，支持'deepseek'和'openai'
            **llm_kwargs: 传递给LLM接口的参数
        """
        # 初始化LLM接口
        try:
            self.llm = get_llm_interface(provider=llm_provider, **llm_kwargs)
        except Exception as e:
            print(f"初始化LLM接口时出错: {e}")
            print("将使用默认参数...")
            self.llm = get_llm_interface(provider=llm_provider)
    
    def extract_parameters_from_description(self, description: str) -> Tuple[str, Dict[str, Any]]:
        """
        从描述中提取网络参数
        
        参数:
            description: 网络描述
            
        返回:
            网络类型和参数字典
        """
        return self.llm.extract_parameters(description)
    
    def generate_network(self, network_type: str, parameters: Dict[str, Any], output_file: str) -> Optional[str]:
        """
        生成网络
        
        参数:
            network_type: 网络类型
            parameters: 参数字典
            output_file: 输出文件名
            
        返回:
            生成的网络文件路径，如果生成失败则返回None
        """
        try:
            # 创建网络生成器
            generator = NetworkGenerator()
            
            # 使用生成器生成网络
            network_path = generator.generate(network_type, parameters, output_file)
            
            return network_path
        except Exception as e:
            print(f"生成网络时出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def visualize_network(self, network_file: str, method: str = "matplotlib") -> None:
        """
        可视化网络
        
        参数:
            network_file: 网络文件路径
            method: 可视化方法，支持'matplotlib'、'sumo-gui'和'export'
        """
        try:
            # 调用可视化函数
            visualize_network(network_file, method)
        except Exception as e:
            print(f"可视化网络时出错: {e}")
            import traceback
            traceback.print_exc()