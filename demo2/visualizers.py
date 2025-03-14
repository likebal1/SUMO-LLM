import os
import sys
import subprocess
import math
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Tuple
from abc import ABC, abstractmethod

# 检查SUMO_HOME环境变量
if "SUMO_HOME" not in os.environ:
    print("Warning: SUMO_HOME environment variable is not set. Visualization with SUMO-GUI may not work correctly.")

# 如果matplotlib可用，则导入
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("警告: matplotlib未安装，部分可视化功能将不可用")


class NetworkVisualizer(ABC):
    """
    网络可视化器的基类
    """
    
    @abstractmethod
    def visualize(self, network_file: str) -> None:
        """
        可视化网络
        
        参数:
            network_file: 网络文件路径
        """
        # 检查文件是否存在
        if not os.path.exists(network_file):
            raise FileNotFoundError(f"找不到网络文件: {network_file}")


class SumoGUIVisualizer(NetworkVisualizer):
    """
    使用SUMO-GUI可视化网络
    """
    
    def visualize(self, network_file: str) -> None:
        """
        使用SUMO-GUI可视化网络
        
        参数:
            network_file: 网络文件路径
        """
        super().visualize(network_file)
        
        # 构建命令
        command = ["sumo-gui", "-n", network_file]
        
        print(f"启动SUMO-GUI查看网络: {network_file}")
        print(f"执行命令: {' '.join(command)}")
        
        try:
            # 使用subprocess启动SUMO-GUI
            subprocess.Popen(command)
        except Exception as e:
            print(f"启动SUMO-GUI时出错: {e}")
            import traceback
            traceback.print_exc()


class MatplotlibVisualizer(NetworkVisualizer):
    """
    使用Matplotlib可视化网络
    """
    
    def visualize(self, network_file: str, output_file: Optional[str] = None) -> None:
        """
        使用Matplotlib可视化网络
        
        参数:
            network_file: 网络文件路径
            output_file: 输出图像文件路径（可选）
        """
        super().visualize(network_file)
        
        # 检查matplotlib是否可用
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError("matplotlib未安装，无法使用此可视化方法")
        
        try:
            # 解析网络文件
            tree = ET.parse(network_file)
            root = tree.getroot()
            
            # 创建图形
            plt.figure(figsize=(12, 10))
            
            # 绘制边
            edges = []
            for edge in root.findall(".//edge"):
                # 跳过内部边
                if "function" in edge.attrib and edge.attrib["function"] == "internal":
                    continue
                
                edge_id = edge.attrib["id"]
                
                # 获取起点和终点
                from_id = edge.attrib.get("from")
                to_id = edge.attrib.get("to")
                
                # 找到对应的节点坐标
                from_node = root.find(f".//junction[@id='{from_id}']")
                to_node = root.find(f".//junction[@id='{to_id}']")
                
                if from_node is not None and to_node is not None:
                    x1, y1 = float(from_node.attrib["x"]), float(from_node.attrib["y"])
                    x2, y2 = float(to_node.attrib["x"]), float(to_node.attrib["y"])
                    
                    # 绘制边
                    plt.plot([x1, x2], [y1, y2], 'b-', linewidth=1.5)
                    
                    # 存储边信息
                    edges.append({
                        "id": edge_id,
                        "from": from_id,
                        "to": to_id,
                        "x1": x1, "y1": y1,
                        "x2": x2, "y2": y2
                    })
            
            # 绘制交叉口
            for junction in root.findall(".//junction"):
                # 跳过内部交叉口
                if "type" in junction.attrib and junction.attrib["type"] == "internal":
                    continue
                
                junction_id = junction.attrib["id"]
                x, y = float(junction.attrib["x"]), float(junction.attrib["y"])
                
                # 不同类型交叉口使用不同颜色
                if "type" in junction.attrib and junction.attrib["type"] == "traffic_light":
                    # 交通信号灯交叉口 - 红色
                    plt.plot(x, y, 'ro', markersize=8)
                else:
                    # 其他交叉口 - 蓝色
                    plt.plot(x, y, 'bo', markersize=6)
                
                # 添加交叉口ID标签
                plt.text(x, y, junction_id, fontsize=9)
            
            # 添加标题和图例
            plt.title(f"SUMO网络: {os.path.basename(network_file)}")
            plt.grid(True)
            plt.axis('equal')
            
            # 保存或显示图像
            if output_file:
                plt.savefig(output_file)
                print(f"网络图像已保存: {output_file}")
            else:
                plt.show()
                
        except Exception as e:
            print(f"使用Matplotlib可视化网络时出错: {e}")
            import traceback
            traceback.print_exc()


def get_visualizer(method: str = "matplotlib") -> NetworkVisualizer:
    """
    获取合适的可视化器
    
    参数:
        method: 可视化方法
        
    返回:
        网络可视化器实例
    """
    if method == "matplotlib":
        return MatplotlibVisualizer()
    elif method == "sumo-gui":
        return SumoGUIVisualizer()
    elif method == "export":
        # export使用matplotlib但输出到文件
        return MatplotlibVisualizer()
    else:
        raise ValueError(f"不支持的可视化方法: {method}")


def visualize_network(network_file: str, method: str = "matplotlib") -> None:
    """
    可视化网络文件
    
    参数:
        network_file: 网络文件路径
        method: 可视化方法，支持'matplotlib'、'sumo-gui'和'export'
    """
    # 获取可视化器
    visualizer = get_visualizer(method)
    
    # 使用可视化器
    if method == "export":
        # 导出为PNG文件
        output_file = f"{os.path.splitext(network_file)[0]}_visualization.png"
        visualizer.visualize(network_file, output_file)
    else:
        # 直接可视化
        visualizer.visualize(network_file) 