import os
import sys
import subprocess
import math
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Any, Optional, List, Tuple

class NetworkGenerator:
    """
    网络生成器基类，定义所有生成器的通用接口
    """
    
    def __init__(self):
        """初始化网络生成器"""
        # 确保输出目录存在
        self.output_dir = "generated_networks"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate(self, network_type: str, parameters: Dict[str, Any], output_file: str) -> Optional[str]:
        """
        根据网络类型和参数生成网络文件
        
        参数:
            network_type: 网络类型 (grid, spider, random)
            parameters: 网络参数字典
            output_file: 输出文件名
            
        返回:
            生成的网络文件完整路径，如果生成失败则返回None
        """
        # 处理输出文件路径
        if not output_file.endswith(".net.xml"):
            output_file += ".net.xml"
            
        # 完整路径
        output_path = output_file if os.path.isabs(output_file) else os.path.join(os.getcwd(), output_file)
        
        # 检测T字形路口和三岔路口
        description = parameters.get("description", "").lower()
        if "t字" in description or "t型" in description or "t形" in description or "t路口" in description:
            print("检测到T字形路口请求，设置为特殊三岔路口...")
            parameters["arm_number"] = 3
            parameters["multi_junction"] = True
        elif "三岔" in description or "三叉" in description or "y" in description or "y形" in description:
            print("检测到三岔路口请求...")
            parameters["arm_number"] = 3
            parameters["multi_junction"] = True
        
        # 特殊处理路口形状
        if parameters.get("arm_number", 0) == 3:
            print("设置为T字形三岔路口")
            parameters["junction_shape"] = "T"
        
        # 根据类型选择具体的生成器
        if network_type == "grid":
            # 检查是否是单个交叉口
            is_single_intersection = (
                parameters.get("grid.x-number", 5) == 1 and 
                parameters.get("grid.y-number", 5) == 1
            )
            
            # 检查是否是多岔路口
            is_multi_junction = parameters.get("multi_junction", False) or "arm_number" in parameters
            
            # 检查是否有差异化道路设置
            has_custom_edges = "edge_specific" in parameters
            
            if is_multi_junction:
                # 使用多岔路口生成器
                print("检测到多岔路口配置，使用多岔路口生成器...")
                generator = MultiJunctionGenerator()
                return generator.generate_network(parameters, output_path)
            elif is_single_intersection and has_custom_edges:
                # 使用差异化十字路口生成器
                generator = CrossIntersectionGenerator()
                return generator.generate_network(parameters, output_path)
            else:
                # 使用标准网格生成器
                generator = StandardNetworkGenerator()
                return generator.generate_network(network_type, parameters, output_path)
                
        elif network_type == "spider":
            # 使用标准生成器
            generator = StandardNetworkGenerator()
            return generator.generate_network(network_type, parameters, output_path)
            
        elif network_type == "random":
            # 使用标准生成器
            generator = StandardNetworkGenerator()
            return generator.generate_network(network_type, parameters, output_path)
            
        else:
            raise ValueError(f"不支持的网络类型: {network_type}")


class StandardNetworkGenerator:
    """
    标准网络生成器，使用SUMO的netgenerate工具生成网络
    """
    
    def generate_network(self, network_type: str, parameters: Dict[str, Any], output_path: str) -> Optional[str]:
        """
        使用netgenerate工具生成标准网络
        
        参数:
            network_type: 网络类型
            parameters: 参数字典
            output_path: 输出文件路径
            
        返回:
            生成的网络文件完整路径，如果生成失败则返回None
        """
        # 构建命令
        command = ["netgenerate"]
        
        # 添加网络类型
        if network_type == "grid":
            command.append("--grid")
        elif network_type == "spider":
            command.append("--spider")
        elif network_type == "random":
            command.append("--rand")
        else:
            raise ValueError(f"不支持的网络类型: {network_type}")
        
        # 提取交叉口类型，netgenerate可能以不同方式处理
        junction_type = parameters.get("junctions.type", "traffic_light")
        print(f"[DEBUG] 交叉口类型: {junction_type}")
        
        # 添加其他参数
        for param, value in parameters.items():
            # 跳过专用参数
            if param in ["edge_specific", "multi_junction", "arm_number", "junctions.type"]:
                continue
                
            # 修正参数名以匹配SUMO的实际参数名
            if param == "default.street-length":
                param = "default-length"  # 正确的SUMO参数名
            
            # 添加命令行选项
            command.append(f"--{param}={value}")
        
        # 尝试使用正确的方式添加交叉口类型（如果netgenerate支持）
        # netgenerate处理交叉口的方式可能与netconvert不同
        if junction_type and network_type == "grid":
            # 对于网格类型，可以设置交叉口类型
            command.append(f"--grid.junction-type={junction_type}")
        
        # 添加输出文件
        command.append(f"--output-file={output_path}")
        
        # 记录命令
        print(f"执行命令: {' '.join(command)}")
        
        try:
            # 执行命令
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # 检查命令是否成功执行
            if process.returncode == 0:
                print(f"网络已成功生成: {output_path}")
                return output_path
            else:
                print(f"网络生成失败，返回代码: {process.returncode}")
                print(f"命令输出: {process.stdout}")
                print(f"错误信息: {process.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"执行网络生成命令时出错: {str(e)}")
            print(f"命令输出: {e.stdout}")
            print(f"错误信息: {e.stderr}")
            return None
        except Exception as e:
            print(f"网络生成时出现未知错误: {str(e)}")
            return None


class CrossIntersectionGenerator:
    """
    交叉口生成器，使用netconvert工具生成带有差异化属性的十字路口
    """
    
    def generate_network(self, parameters: Dict[str, Any], output_path: str) -> Optional[str]:
        """生成十字路口网络"""
        try:
            # 从参数中获取各个方向的配置
            directions = ["west", "east", "north", "south"]
            lanes = {}
            lengths = {}
            for direction in directions:
                lanes[direction] = parameters.get(f"lanes.{direction}", 1)
                lengths[direction] = parameters.get(f"length.{direction}", 100)
            
            # 获取默认参数
            default_speed = parameters.get("default.speed", 13.9)  # 默认50km/h
            road_type = parameters.get("default.type", "highway.secondary")
            
            # 创建临时文件
            nodes_file = "nodes.xml"
            edges_file = "edges.xml"
            connections_file = "connections.xml"
            
            # 获取交叉口类型 - 在nodes.xml中设置
            junction_type = parameters.get("junctions.type", "traffic_light")
            print(f"[DEBUG] 交叉口类型: {junction_type} - 已在nodes.xml中设置")
            
            # 获取边特定参数
            edge_specific = parameters.get("edge_specific", {})
            
            # 生成nodes.xml
            self._generate_nodes_file(nodes_file, lengths, parameters)
            
            # 生成edges.xml - 传递edge_specific参数
            self._generate_edges_file(edges_file, lengths, lanes, default_speed, road_type, edge_specific)
            
            # 生成connections.xml
            self._generate_connections_file(connections_file, lanes)
            
            # 构建netconvert命令 - 移除不支持的参数
            command = [
                "netconvert",
                f"--node-files={nodes_file}",
                f"--edge-files={edges_file}",
                f"--connection-files={connections_file}",
                f"--output-file={output_path}"
            ]
            
            # 输出完整命令用于调试
            print(f"执行命令: {' '.join(command)}")
            
            # 执行命令
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # 检查命令是否成功执行
            if process.returncode == 0:
                print(f"十字路口已成功生成: {output_path}")
                return output_path
            else:
                print(f"十字路口生成失败，返回代码: {process.returncode}")
                print(f"错误信息: {process.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"执行netconvert命令时出错: {str(e)}")
            print(f"错误信息: {e.stderr}")
            return None
        except Exception as e:
            print(f"十字路口生成时出现未知错误: {str(e)}")
            return None
    
    def _generate_nodes_file(self, file_path: str, lengths: Dict[str, int], parameters: Dict[str, Any]) -> None:
        """
        生成nodes.xml文件
        
        参数:
            file_path: 文件路径
            lengths: 边长度字典
            parameters: 参数字典
        """
        root = ET.Element("nodes")
        
        # 添加中心节点
        center_node = ET.SubElement(root, "node")
        center_node.set("id", "C")
        center_node.set("x", "0")
        center_node.set("y", "0")
        
        # 获取交叉口类型
        junction_type = parameters.get("junctions.type", "traffic_light")
        center_node.set("type", junction_type)
        
        # 添加四个方向节点
        directions = [
            ("E", "east", 1, 0),  # 东
            ("W", "west", -1, 0),  # 西
            ("N", "north", 0, 1),  # 北
            ("S", "south", 0, -1)  # 南
        ]
        
        # 获取边特定参数
        edge_specific = parameters.get("edge_specific", {})
        
        # 默认长度
        default_street_length = parameters.get("default.street-length", 100)
        
        for node_id, direction, dx, dy in directions:
            # 获取此方向的长度（如果有）
            length = edge_specific.get(direction, {}).get("length", default_street_length)
            
            # 创建节点
            node = ET.SubElement(root, "node")
            node.set("id", node_id)
            node.set("x", str(dx * length))
            node.set("y", str(dy * length))
            node.set("type", "priority")
        
        # 写入XML文件
        tree = ET.ElementTree(root)
        with open(file_path, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
    
    def _generate_edges_file(self, file_path: str, lengths: Dict[str, int], lanes: Dict[str, int], 
                           speed: float, road_type: str, edge_specific: Dict[str, Dict[str, Any]] = None) -> None:
        """
        生成edges.xml文件
        
        参数:
            file_path: 文件路径
            lengths: 边长度字典
            lanes: 车道数字典
            speed: 速度限制
            road_type: 道路类型
            edge_specific: 边特定参数字典
        """
        root = ET.Element("edges")
        
        # 确保edge_specific存在
        if edge_specific is None:
            edge_specific = {}
        
        # 添加四个方向的边
        directions = [
            ("CE", "C", "E", "east"),  # C到E（东）
            ("EC", "E", "C", "east"),  # E到C（西）
            ("CW", "C", "W", "west"),  # C到W（西）
            ("WC", "W", "C", "west"),  # W到C（东）
            ("CN", "C", "N", "north"),  # C到N（北）
            ("NC", "N", "C", "north"),  # N到C（南）
            ("CS", "C", "S", "south"),  # C到S（南）
            ("SC", "S", "C", "south")   # S到C（北）
        ]
        
        for edge_id, from_node, to_node, direction in directions:
            # 获取此方向的特定参数
            direction_params = edge_specific.get(direction, {})
            
            # 获取车道数，优先使用方向特定值，如果不存在则使用默认值
            lane_number = direction_params.get("lanenumber", lanes.get(direction, 1))
            
            # 创建边
            edge = ET.SubElement(root, "edge")
            edge.set("id", edge_id)
            edge.set("from", from_node)
            edge.set("to", to_node)
            edge.set("numLanes", str(lane_number))
            edge.set("speed", str(speed))
            edge.set("type", road_type)
        
        # 写入XML文件
        tree = ET.ElementTree(root)
        with open(file_path, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
    
    def _generate_connections_file(self, file_path: str, lanes: Dict[str, int]) -> None:
        """
        生成connections.xml文件
        
        参数:
            file_path: 文件路径
            lanes: 车道数字典
        """
        root = ET.Element("connections")
        
        # 添加连接
        directions = [
            ("EC", "CN", "east", "north"),  # 东到北
            ("EC", "CS", "east", "south"),  # 东到南
            ("EC", "CW", "east", "west"),   # 东到西
            
            ("WC", "CN", "west", "north"),  # 西到北
            ("WC", "CS", "west", "south"),  # 西到南
            ("WC", "CE", "west", "east"),   # 西到东
            
            ("NC", "CE", "north", "east"),  # 北到东
            ("NC", "CW", "north", "west"),  # 北到西
            ("NC", "CS", "north", "south"), # 北到南
            
            ("SC", "CE", "south", "east"),  # 南到东
            ("SC", "CW", "south", "west"),  # 南到西
            ("SC", "CN", "south", "north")  # 南到北
        ]
        
        for from_edge, to_edge, from_dir, to_dir in directions:
            # 获取源边和目标边的车道数
            from_lanes = lanes.get(from_dir, 1)
            to_lanes = lanes.get(to_dir, 1)
            
            # 为每个车道创建连接
            for i in range(from_lanes):
                for j in range(to_lanes):
                    connection = ET.SubElement(root, "connection")
                    connection.set("from", from_edge)
                    connection.set("to", to_edge)
                    connection.set("fromLane", str(i))
                    connection.set("toLane", str(j))
        
        # 写入XML文件
        tree = ET.ElementTree(root)
        with open(file_path, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)


class MultiJunctionGenerator:
    """
    多岔路口生成器，生成具有多条辐射道路的单个交叉口
    """
    
    def generate_network(self, parameters: Dict[str, Any], output_path: str) -> Optional[str]:
        """
        生成多岔路口网络
        
        参数:
            parameters: 参数字典
            output_path: 输出文件路径
            
        返回:
            生成的网络文件完整路径，如果生成失败则返回None
        """
        # 获取岔路数量
        arm_number = parameters.get("arm_number", 5)
        
        # 获取默认参数
        default_lane_number = parameters.get("default.lanenumber", 1)
        default_street_length = parameters.get("default.street-length", 100)
        default_speed = parameters.get("default.speed", 13.9)  # 默认50km/h
        road_type = parameters.get("default.type", "highway.secondary")
        
        # 创建临时XML文件
        nodes_file = "nodes.xml"
        edges_file = "edges.xml"
        connections_file = "connections.xml"
        
        # 生成nodes.xml - 交叉口类型在此XML中的节点type属性设置
        junction_type = parameters.get("junctions.type", "traffic_light")
        print(f"[DEBUG] 交叉口类型: {junction_type} - 已在nodes.xml中设置")
        self._generate_nodes_file(nodes_file, arm_number, default_street_length, parameters)
        
        # 生成edges.xml
        self._generate_edges_file(edges_file, arm_number, default_lane_number, default_speed, road_type)
        
        # 生成connections.xml
        self._generate_connections_file(connections_file, arm_number, default_lane_number)
        
        # 构建netconvert命令 - 移除不支持的参数
        command = [
            "netconvert",
            f"--node-files={nodes_file}",
            f"--edge-files={edges_file}",
            f"--connection-files={connections_file}",
            f"--output-file={output_path}"
        ]
        
        # 输出完整命令用于调试
        print(f"执行命令: {' '.join(command)}")
        
        try:
            # 执行命令
            process = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # 检查命令是否成功执行
            if process.returncode == 0:
                print(f"多岔路口已成功生成: {output_path}")
                return output_path
            else:
                print(f"多岔路口生成失败，返回代码: {process.returncode}")
                print(f"命令输出: {process.stdout}")
                print(f"错误信息: {process.stderr}")
                return None
                
        except subprocess.CalledProcessError as e:
            print(f"执行netconvert命令时出错: {str(e)}")
            print(f"命令输出: {e.stdout}")
            print(f"错误信息: {e.stderr}")
            return None
        except Exception as e:
            print(f"多岔路口生成时出现未知错误: {str(e)}")
            return None
    
    def _generate_nodes_file(self, file_path: str, arm_number: int, default_street_length: int, 
                           parameters: Dict[str, Any]) -> None:
        """
        生成nodes.xml文件
        
        参数:
            file_path: 文件路径
            arm_number: 岔路数量
            default_street_length: 默认道路长度
            parameters: 参数字典
        """
        root = ET.Element("nodes")
        
        # 添加中心节点
        center_node = ET.SubElement(root, "node")
        center_node.set("id", "C")
        center_node.set("x", "0")
        center_node.set("y", "0")
        
        # 获取交叉口类型 - 但注意在XML节点属性中仍使用"type"属性
        junction_type = parameters.get("junctions.type", "traffic_light")
        print(f"[DEBUG] 在nodes.xml中设置中心节点类型为: {junction_type}")
        center_node.set("type", junction_type)
        
        # 检查是否为特殊的路口形态
        junction_shape = parameters.get("junction_shape", "")
        
        # 三岔路口全部默认使用T字形布局
        if arm_number == 3:
            print("生成T字形路口，两条道路在一条直线上，第三条垂直于该直线")
            # T字形三岔路口的节点位置
            node_positions = [
                (default_street_length, 0),  # 右边
                (-default_street_length, 0), # 左边
                (0, default_street_length)   # 上边(垂直于水平线)
            ]
            
            for i, (x, y) in enumerate(node_positions):
                node = ET.SubElement(root, "node")
                node.set("id", f"N{i}")
                node.set("x", str(x))
                node.set("y", str(y))
                node.set("type", "priority")
        else:
            # 其他多岔路口处理 - 均匀分布角度
            angle_step = 360 / arm_number
            
            for i in range(arm_number):
                # 计算角度（从正右方向，逆时针）
                angle_deg = i * angle_step
                angle_rad = math.radians(angle_deg)
                
                # 计算坐标
                x = default_street_length * math.cos(angle_rad)
                y = default_street_length * math.sin(angle_rad)
                
                # 创建节点
                node = ET.SubElement(root, "node")
                node.set("id", f"N{i}")
                node.set("x", str(x))
                node.set("y", str(y))
                node.set("type", "priority")
        
        # 写入XML文件
        tree = ET.ElementTree(root)
        with open(file_path, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
    
    def _generate_edges_file(self, file_path: str, arm_number: int, lane_number: int, 
                           speed: float, road_type: str) -> None:
        """
        生成edges.xml文件
        
        参数:
            file_path: 文件路径
            arm_number: 岔路数量
            lane_number: 车道数
            speed: 速度限制
            road_type: 道路类型
        """
        root = ET.Element("edges")
        
        # 添加各个方向的边
        for i in range(arm_number):
            # 向外的边
            out_edge = ET.SubElement(root, "edge")
            out_edge.set("id", f"C_N{i}")
            out_edge.set("from", "C")
            out_edge.set("to", f"N{i}")
            out_edge.set("numLanes", str(lane_number))
            out_edge.set("speed", str(speed))
            out_edge.set("type", road_type)
            
            # 向内的边
            in_edge = ET.SubElement(root, "edge")
            in_edge.set("id", f"N{i}_C")
            in_edge.set("from", f"N{i}")
            in_edge.set("to", "C")
            in_edge.set("numLanes", str(lane_number))
            in_edge.set("speed", str(speed))
            in_edge.set("type", road_type)
        
        # 写入XML文件
        tree = ET.ElementTree(root)
        with open(file_path, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True)
    
    def _generate_connections_file(self, file_path: str, arm_number: int, lane_number: int) -> None:
        """
        生成connections.xml文件
        
        参数:
            file_path: 文件路径
            arm_number: 岔路数量
            lane_number: 车道数
        """
        root = ET.Element("connections")
        
        # 添加各个方向之间的连接
        for i in range(arm_number):
            for j in range(arm_number):
                # 跳过掉头
                if i == j:
                    continue
                
                # 为每个车道创建连接
                for from_lane in range(lane_number):
                    for to_lane in range(lane_number):
                        connection = ET.SubElement(root, "connection")
                        connection.set("from", f"N{i}_C")
                        connection.set("to", f"C_N{j}")
                        connection.set("fromLane", str(from_lane))
                        connection.set("toLane", str(to_lane))
        
        # 写入XML文件
        tree = ET.ElementTree(root)
        with open(file_path, 'wb') as f:
            tree.write(f, encoding='utf-8', xml_declaration=True) 