import os
import json
import requests
import re
from typing import Dict, List, Any, Optional, Tuple
import time
import random

# 导入配置文件
try:
    from config import USE_OPENAI_STYLE, API_URL, API_KEY, API_MODEL
except ImportError:
    # 如果未找到配置文件，使用默认配置
    USE_OPENAI_STYLE = True  # DeepSeek使用OpenAI风格的接口
    DEFAULT_API_URL = "https://api.deepseek.com/v1/chat/completions"   # API URL
    DEFAULT_API_KEY = "sk-e810443c082f44ab876f55f1c8519076"  # 替换为实际API密钥
    DEFAULT_API_MODEL = "deepseek-chat"  # 模型名称

class BaseLLMInterface:
    """
    LLM接口的基类，定义与LLM交互的通用接口
    """
    
    def extract_parameters(self, description: str) -> Tuple[str, Dict[str, Any]]:
        """
        从描述中提取网络参数
        
        参数:
            description: 网络描述
            
        返回:
            网络类型和参数字典的元组
        """
        raise NotImplementedError("子类必须实现此方法")
    
    def _clean_parameters(self, network_type: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理参数，移除不相关的参数
        
        参数:
            network_type: 网络类型
            parameters: 原始参数字典
            
        返回:
            清理后的参数字典
        """
        # 创建一个新的字典来存储清理后的参数
        cleaned = {}
        
        # 修正参数名以匹配SUMO的实际参数
        if "default.length" in parameters:
            parameters["default.street-length"] = parameters.pop("default.length")
            
        if "default.junctions.type" in parameters:
            parameters["junctions.type"] = parameters.pop("default.junctions.type")
        
        # 保留所有default参数
        for key, value in parameters.items():
            if key.startswith("default.") or key.startswith("default-"):
                cleaned[key] = value
            
            # 根据网络类型保留相关参数
            if network_type == "grid" and key.startswith("grid."):
                cleaned[key] = value
            elif network_type == "spider" and key.startswith("spider."):
                cleaned[key] = value
            elif network_type == "random" and key.startswith("rand."):
                cleaned[key] = value
        
        # 保留差异化道路设置
        if "edge_specific" in parameters:
            cleaned["edge_specific"] = parameters["edge_specific"]
            
        # 检查是否设置了junction类型
        if "junctions.type" in parameters:
            cleaned["junctions.type"] = parameters["junctions.type"]
        elif "junction-type" in parameters:
            cleaned["junctions.type"] = parameters["junction-type"]
        
        # 保留多岔路口相关参数
        if "multi_junction" in parameters:
            cleaned["multi_junction"] = parameters["multi_junction"]
        if "arm_number" in parameters:
            cleaned["arm_number"] = parameters["arm_number"]
        
        return cleaned

class DeepSeekLLMInterface(BaseLLMInterface):
    """
    DeepSeek大型语言模型接口
    """
    
    def __init__(self, api_key: str = None, api_url: str = None, model: str = "deepseek-chat"):
        """
        初始化DeepSeek LLM接口
        
        参数:
            api_key: DeepSeek API密钥（如果为None，则尝试从环境变量获取）
            api_url: DeepSeek API地址（如果为None，则使用默认地址）
            model: 使用的模型名称
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API密钥未提供且环境变量DEEPSEEK_API_KEY未设置")
            
        self.api_url = api_url or "https://api.deepseek.com/v1/chat/completions"
        self.model = model
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示信息
        
        返回:
            系统提示字符串
        """
        return """你是一个SUMO（交通模拟工具）的网络生成助手。你的任务是从用户的自然语言描述中提取参数，用于生成交通网络。
        
请仔细分析以下描述，提取相关参数，并以JSON格式返回。
        
支持的网络类型有：
1. grid(网格): 适用于常规城市道路网格
2. spider(蜘蛛/放射状): 适用于环形或放射状路网
3. random(随机): 适用于随机生成的路网
        
参数格式要求：
1. 必须返回network_type(网络类型)和parameters(参数)两个字段
2. network_type必须是以下之一：grid, spider, random
3. parameters包含具体的网络参数
        
每种网络类型支持的参数：
- grid:
  - grid.x-number: 水平方向交叉口数量，默认为5
  - grid.y-number: 垂直方向交叉口数量，默认为5
  - grid.x-length: 水平道路长度，默认为100
  - grid.y-length: 垂直道路长度，默认为100
        
- spider:
  - spider.arm-number: 臂数，默认为13
  - spider.circle-number: 环数，默认为5
  - spider.space-radius: 环间距，默认为100
        
- random:
  - rand.iterations: 迭代次数，默认为200
  - rand.bidi-probability: 双向道路概率，默认为0.5
  - rand.max-distance: 最大连接距离，默认为250
  - rand.min-distance: 最小连接距离，默认为100
  - rand.min-angle: 最小连接角度，默认为45°
  - rand.connectivity: 连接度，默认为0.95
        
所有类型通用参数：
- default.lanenumber: 每个方向的车道数，默认为1
- default.speed: 道路速度限制(m/s)，默认为13.9 (50km/h)
- default.street-length: 道路长度，默认为100
- junctions.type: 交叉口类型(traffic_light, priority, right_before_left等)，默认为priority

特殊处理情况：
1. 如果描述是"十字路口"或"四岔路口"且没有提及网格大小，则设置grid.x-number=1和grid.y-number=1。
2. 对于"三岔路口"、"五岔路口"等多岔路口，设置network_type为"grid"，并在parameters中添加额外字段"junction_type"="multi_junction"和"arm_number"=岔路数量。
3. 如果描述中提到不同方向的差异化属性（如"西边路段双向6车道，东边路段双向4车道"），则创建一个"edge_specific"对象，包含各个方向的具体设置。例如：
   "edge_specific": {
     "west": {"lanenumber": 3, "length": 200},
     "east": {"lanenumber": 2, "length": 300},
     "north": {"lanenumber": 3},
     "south": {"lanenumber": 2}
   }
   注意：这里的lanenumber表示每个方向的车道数（单向车道数），如"双向6车道"表示lanenumber=3。
        
对于车道数的解释：
- "双向N车道"表示每个方向N/2车道，例如"双向4车道"表示每个方向2车道
- 如果明确说明"每方向N车道"，则直接使用此值
- 如果只说"N车道"，则假设为每个方向N车道

注意：只返回JSON格式的响应，不要有任何多余的文字。确保所有参数名称与上面列出的完全一致。"""
    
    def extract_parameters(self, description: str) -> Tuple[str, Dict[str, Any]]:
        """
        使用DeepSeek API从描述中提取网络参数
        
        参数:
            description: 网络描述
            
        返回:
            网络类型和参数字典的元组
        """
        # 构建请求
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": description}
        ]
        
        try:
            # 最多尝试3次
            for attempt in range(3):
                try:
                    # 发送API请求
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                    data = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.01,  # 低温度以获得确定性输出
                        "max_tokens": 1000,
                    }
                    
                    response = requests.post(
                        self.api_url,
                        headers=headers,
                        json=data,
                        timeout=30  # 30秒超时
                    )
                    
                    response.raise_for_status()  # 抛出HTTP错误
                    result = response.json()
                    
                    # 提取回复内容
                    reply = result["choices"][0]["message"]["content"]
                    
                    # 从回复中提取JSON
                    try:
                        # 尝试解析整个回复作为JSON
                        extracted = json.loads(reply)
                    except json.JSONDecodeError:
                        # 如果整个回复不是有效的JSON，尝试从文本中提取JSON部分
                        json_match = re.search(r'```json\s*(.*?)\s*```', reply, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                        else:
                            # 尝试查找任何看起来像JSON的部分
                            json_match = re.search(r'\{\s*".*"\s*:.*\}', reply, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(0)
                            else:
                                raise ValueError("无法从回复中提取JSON格式的参数")
                        
                        extracted = json.loads(json_str)
                    
                    # 检查提取的数据包含必要的字段
                    if "network_type" not in extracted or "parameters" not in extracted:
                        raise ValueError("提取的数据缺少network_type或parameters字段")
                    
                    network_type = extracted["network_type"]
                    parameters = extracted["parameters"]
                    
                    # 处理五岔路口等特殊情况
                    if "五岔路口" in description or "5岔路口" in description:
                        print("检测到五岔路口的描述，设置为多岔路口...")
                        network_type = "grid"
                        parameters["multi_junction"] = True
                        parameters["arm_number"] = 5
                        parameters["grid.x-number"] = 1
                        parameters["grid.y-number"] = 1
                    elif "三岔路口" in description or "3岔路口" in description:
                        print("检测到三岔路口的描述，设置为多岔路口...")
                        network_type = "grid"
                        parameters["multi_junction"] = True
                        parameters["arm_number"] = 3
                        parameters["grid.x-number"] = 1
                        parameters["grid.y-number"] = 1
                    
                    # 清理参数
                    parameters = self._clean_parameters(network_type, parameters)
                    
                    # 转换多岔路口参数
                    if parameters.get("junction_type") == "multi_junction" and "arm_number" in parameters:
                        parameters["multi_junction"] = True
                    
                    # 处理单个交叉口的情况
                    if network_type == "grid":
                        if parameters.get("grid.x-number", 5) == 1 and parameters.get("grid.y-number", 5) == 1:
                            # 确保设置默认值
                            if "default.lanenumber" not in parameters:
                                parameters["default.lanenumber"] = 1
                            if "default.street-length" not in parameters:
                                parameters["default.street-length"] = 100
                            if "grid.x-length" not in parameters:
                                parameters["grid.x-length"] = 100
                            if "grid.y-length" not in parameters:
                                parameters["grid.y-length"] = 100
                    
                    return network_type, parameters
                    
                except requests.exceptions.RequestException as e:
                    if attempt == 2:  # 最后一次尝试
                        raise ValueError(f"API请求失败: {str(e)}")
                    # 随机退避，等待1-5秒后重试
                    time.sleep(random.uniform(1, 5))
                    continue
                    
        except Exception as e:
            # 捕获并重新抛出异常，提供更多上下文
            raise ValueError(f"从描述中提取参数时出错: {str(e)}")

class OpenAILLMInterface(BaseLLMInterface):
    """
    OpenAI大型语言模型接口
    """
    
    def __init__(self, api_key: str = None, api_url: str = None, model: str = "gpt-3.5-turbo"):
        """
        初始化OpenAI LLM接口
        
        参数:
            api_key: OpenAI API密钥（如果为None，则尝试从环境变量获取）
            api_url: OpenAI API地址（如果为None，则使用默认地址）
            model: 使用的模型名称
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API密钥未提供且环境变量OPENAI_API_KEY未设置")
            
        self.api_url = api_url or "https://api.openai.com/v1/chat/completions"
        self.model = model
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """
        获取系统提示信息
        
        返回:
            系统提示字符串
        """
        return """你是一个SUMO（交通模拟工具）的网络生成助手。你的任务是从用户的自然语言描述中提取参数，用于生成交通网络。
        
请仔细分析以下描述，提取相关参数，并以JSON格式返回。
        
支持的网络类型有：
1. grid(网格): 适用于常规城市道路网格
2. spider(蜘蛛/放射状): 适用于环形或放射状路网
3. random(随机): 适用于随机生成的路网
        
参数格式要求：
1. 必须返回network_type(网络类型)和parameters(参数)两个字段
2. network_type必须是以下之一：grid, spider, random
3. parameters包含具体的网络参数
        
每种网络类型支持的参数：
- grid:
  - grid.x-number: 水平方向交叉口数量，默认为5
  - grid.y-number: 垂直方向交叉口数量，默认为5
  - grid.x-length: 水平道路长度，默认为100
  - grid.y-length: 垂直道路长度，默认为100
        
- spider:
  - spider.arm-number: 臂数，默认为13
  - spider.circle-number: 环数，默认为5
  - spider.space-radius: 环间距，默认为100
        
- random:
  - rand.iterations: 迭代次数，默认为200
  - rand.bidi-probability: 双向道路概率，默认为0.5
  - rand.max-distance: 最大连接距离，默认为250
  - rand.min-distance: 最小连接距离，默认为100
  - rand.min-angle: 最小连接角度，默认为45°
  - rand.connectivity: 连接度，默认为0.95
        
所有类型通用参数：
- default.lanenumber: 每个方向的车道数，默认为1
- default.speed: 道路速度限制(m/s)，默认为13.9 (50km/h)
- default.street-length: 道路长度，默认为100
- junctions.type: 交叉口类型(traffic_light, priority, right_before_left等)，默认为priority

特殊处理情况：
1. 如果描述是"十字路口"或"四岔路口"且没有提及网格大小，则设置grid.x-number=1和grid.y-number=1。
2. 对于"三岔路口"、"五岔路口"等多岔路口，设置network_type为"grid"，并在parameters中添加额外字段"junction_type"="multi_junction"和"arm_number"=岔路数量。
3. 如果描述中提到不同方向的差异化属性（如"西边路段双向6车道，东边路段双向4车道"），则创建一个"edge_specific"对象，包含各个方向的具体设置。例如：
   "edge_specific": {
     "west": {"lanenumber": 3, "length": 200},
     "east": {"lanenumber": 2, "length": 300},
     "north": {"lanenumber": 3},
     "south": {"lanenumber": 2}
   }
   注意：这里的lanenumber表示每个方向的车道数（单向车道数），如"双向6车道"表示lanenumber=3。
        
对于车道数的解释：
- "双向N车道"表示每个方向N/2车道，例如"双向4车道"表示每个方向2车道
- 如果明确说明"每方向N车道"，则直接使用此值
- 如果只说"N车道"，则假设为每个方向N车道

注意：只返回JSON格式的响应，不要有任何多余的文字。确保所有参数名称与上面列出的完全一致。"""
    
    def extract_parameters(self, description: str) -> Tuple[str, Dict[str, Any]]:
        """
        使用OpenAI API从描述中提取网络参数
        
        参数:
            description: 网络描述
            
        返回:
            网络类型和参数字典的元组
        """
        # 构建请求
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": description}
        ]
        
        try:
            # 最多尝试3次
            for attempt in range(3):
                try:
                    # 发送API请求
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}"
                    }
                    data = {
                        "model": self.model,
                        "messages": messages,
                        "temperature": 0.01,  # 低温度以获得确定性输出
                        "max_tokens": 1000,
                    }
                    
                    response = requests.post(
                        self.api_url,
                        headers=headers,
                        json=data,
                        timeout=30  # 30秒超时
                    )
                    
                    response.raise_for_status()  # 抛出HTTP错误
                    result = response.json()
                    
                    # 提取回复内容
                    reply = result["choices"][0]["message"]["content"]
                    
                    # 从回复中提取JSON
                    try:
                        # 尝试解析整个回复作为JSON
                        extracted = json.loads(reply)
                    except json.JSONDecodeError:
                        # 如果整个回复不是有效的JSON，尝试从文本中提取JSON部分
                        json_match = re.search(r'```json\s*(.*?)\s*```', reply, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(1)
                        else:
                            # 尝试查找任何看起来像JSON的部分
                            json_match = re.search(r'\{\s*".*"\s*:.*\}', reply, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(0)
                            else:
                                raise ValueError("无法从回复中提取JSON格式的参数")
                        
                        extracted = json.loads(json_str)
                    
                    # 检查提取的数据包含必要的字段
                    if "network_type" not in extracted or "parameters" not in extracted:
                        raise ValueError("提取的数据缺少network_type或parameters字段")
                    
                    network_type = extracted["network_type"]
                    parameters = extracted["parameters"]
                    
                    # 处理五岔路口等特殊情况
                    if "五岔路口" in description or "5岔路口" in description:
                        print("检测到五岔路口的描述，设置为多岔路口...")
                        network_type = "grid"
                        parameters["multi_junction"] = True
                        parameters["arm_number"] = 5
                        parameters["grid.x-number"] = 1
                        parameters["grid.y-number"] = 1
                    elif "三岔路口" in description or "3岔路口" in description:
                        print("检测到三岔路口的描述，设置为多岔路口...")
                        network_type = "grid"
                        parameters["multi_junction"] = True
                        parameters["arm_number"] = 3
                        parameters["grid.x-number"] = 1
                        parameters["grid.y-number"] = 1
                    
                    # 清理参数
                    parameters = self._clean_parameters(network_type, parameters)
                    
                    # 转换多岔路口参数
                    if parameters.get("junction_type") == "multi_junction" and "arm_number" in parameters:
                        parameters["multi_junction"] = True
                    
                    # 处理单个交叉口的情况
                    if network_type == "grid":
                        if parameters.get("grid.x-number", 5) == 1 and parameters.get("grid.y-number", 5) == 1:
                            # 确保设置默认值
                            if "default.lanenumber" not in parameters:
                                parameters["default.lanenumber"] = 1
                            if "default.street-length" not in parameters:
                                parameters["default.street-length"] = 100
                            if "grid.x-length" not in parameters:
                                parameters["grid.x-length"] = 100
                            if "grid.y-length" not in parameters:
                                parameters["grid.y-length"] = 100
                    
                    return network_type, parameters
                    
                except requests.exceptions.RequestException as e:
                    if attempt == 2:  # 最后一次尝试
                        raise ValueError(f"API请求失败: {str(e)}")
                    # 随机退避，等待1-5秒后重试
                    time.sleep(random.uniform(1, 5))
                    continue
                    
        except Exception as e:
            # 捕获并重新抛出异常，提供更多上下文
            raise ValueError(f"从描述中提取参数时出错: {str(e)}")


def get_llm_interface(provider: str = "deepseek", **kwargs) -> BaseLLMInterface:
    """
    获取LLM接口实例
    
    参数:
        provider: LLM提供商名称，支持'deepseek'和'openai'
        **kwargs: 传递给LLM接口构造函数的关键字参数
        
    返回:
        LLM接口实例
    
    抛出:
        ValueError: 如果提供商不受支持
    """
    if provider.lower() == "deepseek":
        return DeepSeekLLMInterface(**kwargs)
    elif provider.lower() == "openai":
        return OpenAILLMInterface(**kwargs)
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}, 当前支持: deepseek, openai") 