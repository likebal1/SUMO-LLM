import os
import re
import argparse
from typing import Dict, Any, Optional, Tuple, List

class CLIHandler:
    """
    命令行界面处理类，负责用户交互和参数解析
    """
    
    def __init__(self, integration):
        """
        初始化CLI处理器
        
        参数:
            integration: SumoLLMIntegration实例
        """
        self.integration = integration
    
    def parse_arguments(self) -> argparse.Namespace:
        """
        解析命令行参数
        
        返回:
            解析后的参数命名空间
        """
        parser = argparse.ArgumentParser(description="SUMO网络生成器与LLM集成")
        
        mode_group = parser.add_mutually_exclusive_group(required=True)
        mode_group.add_argument("--interactive", action="store_true", help="启动交互式网络生成")
        mode_group.add_argument("--description", type=str, help="通过自然语言描述生成网络")
        mode_group.add_argument("--visualize", type=str, help="可视化已存在的网络文件")
        
        parser.add_argument("--output", default="network.net.xml", help="输出文件路径（仅当使用--description时生效）")
        parser.add_argument("--viz-method", default="matplotlib", 
                            choices=["matplotlib", "sumo-gui", "export"], 
                            help="可视化方法（仅当使用--visualize时生效）")
        
        return parser.parse_args()
    
    def interactive_mode(self) -> None:
        """
        交互式网络生成模式
        """
        print("\n=======================================================")
        print("       SUMO路网生成器与大语言模型集成")
        print("=======================================================")
        print("用自然语言描述你想要创建的道路网络。")
        print("\n支持的网络类型:")
        print("1. 单个十字路口 - 例如：\"生成一个十字交叉口，双向4车道(每方向2车道)，车道长度200米\"")
        print("   - 可以指定不同方向的差异化属性，例如：\"西边路段双向6车道，东边路段双向4车道，长度200米\"")
        print("2. 单个多岔路口 - 例如：\"生成一个五岔路口，双向4车道，道路长度250米\"")
        print("   - 支持3岔路口、4岔路口、5岔路口等多种形式")
        print("   - 多岔路口只有中心点向外辐射的道路，没有环状连接")
        print("3. 网格路网 - 例如：\"生成3x3的网格路网，双向2车道(每方向1车道)，道路长度150米\"")
        print("4. 放射状/环形路网 - 例如：\"生成6臂的环形路网，每臂2车道，半径100米，2层环\"")
        print("5. 随机路网 - 例如：\"生成一个随机路网，车道数为2，连接度为0.8\"")
        print("\n你可以指定以下参数:")
        print("- 道路类型(十字路口、三岔路口、五岔路口、网格、环形等)")
        print("- 网络尺寸(交叉口数量、环形臂数等)")
        print("- 车道数量(例如: 双向4车道=每个方向2车道)")
        print("- 道路长度(例如: 道路长200米)")
        print("- 交叉口类型(信号灯控制、优先权等)")
        print("- 不同方向的差异化属性(例如: 西边路段双向6车道，东边路段双向4车道)")
        print("\n输入'quit'或'exit'退出程序。")
        
        while True:
            print("\n" + "="*50)
            description = input("\n请描述你想要的路网: ")
            if description.lower() in ['quit', 'exit', '退出']:
                print("感谢使用，再见！")
                break
            
            if not description.strip():
                print("描述为空，请重新输入。")
                continue
                
            try:
                print("\n正在分析您的描述...")
                self._process_description(description)
                
            except Exception as e:
                print(f"错误: {e}")
                import traceback
                traceback.print_exc()
    
    def _process_description(self, description: str) -> None:
        """
        处理用户描述并生成网络
        
        参数:
            description: 网络描述
        """
        network_type, parameters = self.integration.extract_parameters_from_description(description)
        
        # 检查是否有差异化道路设置
        has_custom_edges = "edge_specific" in parameters
        
        # 检查是否是十字路口
        is_single_intersection = (network_type == "grid" and 
                                parameters.get("grid.x-number") == 1 and 
                                parameters.get("grid.y-number") == 1)
        
        if is_single_intersection:
            print("\n识别到网络类型: 单个十字路口")
        else:
            print(f"\n识别到网络类型: {network_type}")
        
        # 获取车道数，提供更清晰的解释
        lane_number = parameters.get("default.lanenumber", 0)
        
        # 分类展示参数
        self._display_parameters(network_type, parameters)
        
        # 显示差异化道路设置
        if has_custom_edges:
            self._display_edge_specific_settings(parameters.get("edge_specific", {}))
        
        # 检查是否需要确认车道数
        self._check_lane_number_confirmation(description, parameters, lane_number)
        
        print("\n您可以:")
        print("1. 使用这些参数生成网络(输入'yes')")
        print("2. 修改参数后生成(输入'modify')")
        print("3. 重新描述网络(输入'retry')")
        print("4. 取消操作(输入'cancel')")
        
        # 提供差异化道路设置警告
        if has_custom_edges:
            print("\n注意: 差异化道路设置将使用SUMO的基本生成功能，但由于netgenerate工具的限制，")
            print("某些方向特定的参数可能需要在生成后使用SUMO-netedit手动调整。")
        
        confirm = input("\n您的选择: ").lower()
        
        if confirm == 'yes' or confirm == 'y':
            self._generate_network(network_type, parameters)
        elif confirm == 'modify' or confirm == 'm':
            self._modify_parameters_and_generate(network_type, parameters)
        elif confirm == 'retry' or confirm == 'r':
            print("请重新描述网络。")
        elif confirm == 'cancel' or confirm == 'c':
            print("已取消操作。")
        else:
            print(f"未识别的选项: {confirm}。已取消操作。")
    
    def _display_parameters(self, network_type: str, parameters: Dict[str, Any]) -> None:
        """
        显示网络参数
        
        参数:
            network_type: 网络类型
            parameters: 参数字典
        """
        print("全局参数:")
        if network_type == "grid":
            print("  网格参数:")
            for param, value in parameters.items():
                if param.startswith("grid.") and param != "edge_specific":
                    print(f"    - {param}: {value}")
        elif network_type == "spider":
            print("  环形/放射状参数:")
            for param, value in parameters.items():
                if param.startswith("spider.") and param != "edge_specific":
                    print(f"    - {param}: {value}")
        elif network_type == "random":
            print("  随机网络参数:")
            for param, value in parameters.items():
                if param.startswith("rand.") and param != "edge_specific":
                    print(f"    - {param}: {value}")
        
        print("  通用参数:")
        for param, value in parameters.items():
            if param == "default.lanenumber" and param != "edge_specific":
                print(f"    - {param}: {value} (每个方向的车道数，双向共{value*2}车道)")
            elif (param.startswith("default.") or param.startswith("default-")) and param != "edge_specific":
                print(f"    - {param}: {value}")
    
    def _display_edge_specific_settings(self, edge_specific: Dict[str, Dict[str, Any]]) -> None:
        """
        显示差异化道路设置
        
        参数:
            edge_specific: 差异化设置字典
        """
        print("\n差异化道路设置:")
        direction_names = {
            "west": "西边",
            "east": "东边",
            "north": "北边",
            "south": "南边"
        }
        
        for direction, settings in edge_specific.items():
            direction_name = direction_names.get(direction, direction)
            print(f"  {direction_name}路段:")
            if "lanenumber" in settings:
                lane_num = settings["lanenumber"]
                print(f"    - 车道数: 每个方向{lane_num}车道 (双向共{lane_num*2}车道)")
            if "length" in settings:
                print(f"    - 长度: {settings['length']}米")
    
    def _check_lane_number_confirmation(self, description: str, parameters: Dict[str, Any], lane_number: int) -> None:
        """
        检查是否需要确认车道数
        
        参数:
            description: 用户描述
            parameters: 参数字典
            lane_number: 车道数
        """
        # 仅在特殊情况下才确认车道数
        odd_lane_query = False
        if "双向" in description and "车道" in description:
            lane_desc = re.search(r'双向(\d+)车道', description)
            if lane_desc:
                total_lanes = int(lane_desc.group(1))
                # 仅当是奇数车道且用户描述有歧义时才询问
                if total_lanes % 2 != 0 and total_lanes > 1 and "每方向" not in description and "每个方向" not in description:
                    odd_lane_query = True
        
        # 只有在奇数车道且描述模糊时才询问用户
        if odd_lane_query:
            per_side = lane_number
            print(f"\n注意: 您描述了双向{total_lanes}车道(奇数)，系统将其解释为每个方向{per_side}车道。")
            confirm_lanes = input(f"您是否有特殊的车道分配需求？如果有，请输入新的每方向车道数；如果没有，直接按回车继续: ")
            if confirm_lanes.strip():
                try:
                    new_value = int(confirm_lanes.strip())
                    parameters["default.lanenumber"] = new_value
                    print(f"已将车道数调整为每个方向{new_value}车道 (双向共{new_value*2}车道)")
                except ValueError:
                    print("输入无效，保持原车道数设置。")
    
    def _generate_network(self, network_type: str, parameters: Dict[str, Any]) -> None:
        """
        生成网络
        
        参数:
            network_type: 网络类型
            parameters: 参数字典
        """
        output_file = input("输入输出文件名（默认：network.net.xml）: ") or "network.net.xml"
        network_path = self.integration.generate_network(network_type, parameters, output_file)
        
        if network_path:
            print(f"\n网络生成成功: {network_path}")
            
            # 询问是否可视化
            viz = input("\n是否要可视化网络？(yes/no): ").lower()
            if viz in ['yes', 'y']:
                print("\n可视化方法:")
                print("1. 使用matplotlib显示(matplotlib)")
                print("2. 使用SUMO-GUI打开(sumo-gui)")
                print("3. 导出为PNG图像(export)")
                viz_method = input("请选择可视化方法 [matplotlib]: ").lower() or "matplotlib"
                
                # 调用可视化方法
                self.integration.visualize_network(network_path, viz_method)
    
    def _modify_parameters_and_generate(self, network_type: str, parameters: Dict[str, Any]) -> None:
        """
        修改参数并生成网络
        
        参数:
            network_type: 网络类型
            parameters: 参数字典
        """
        print("\n您可以修改参数。格式：'参数名=值'，例如：'default.lanenumber=4'")
        print("输入'done'完成修改。")
        
        # 创建参数副本进行修改
        modified_params = parameters.copy()
        
        while True:
            param_input = input("> ")
            if param_input.lower() in ['done', '完成']:
                break
            
            try:
                param, value = param_input.split('=')
                param = param.strip()
                value = value.strip()
                
                # 尝试将值转换为适当的类型
                try:
                    if '.' in value:
                        modified_params[param] = float(value)
                    else:
                        modified_params[param] = int(value)
                except ValueError:
                    modified_params[param] = value
                
                # 提供清晰的车道数反馈
                if param == "default.lanenumber":
                    lane_value = modified_params[param]
                    print(f"设置 {param} = {lane_value} (每个方向的车道数，双向共{lane_value*2}车道)")
                else:
                    print(f"设置 {param} = {value}")
            except ValueError:
                print("格式无效。请使用'参数名=值'格式，例如：'default.lanenumber=4'")
        
        self._generate_network(network_type, modified_params)
    
    def description_mode(self, description: str, output_file: str) -> None:
        """
        处理描述模式
        
        参数:
            description: 网络描述
            output_file: 输出文件路径
        """
        network_type, parameters = self.integration.extract_parameters_from_description(description)
        
        # 检查是否有差异化道路设置
        has_custom_edges = "edge_specific" in parameters
        
        # 检查是否是十字路口
        is_single_intersection = (network_type == "grid" and 
                                 parameters.get("grid.x-number") == 1 and 
                                 parameters.get("grid.y-number") == 1)
        if is_single_intersection:
            print("识别到单个十字路口配置")
        else:
            print(f"识别到网络类型: {network_type}")
            
        # 显示参数
        self._display_parameters(network_type, parameters)
        
        # 显示差异化道路设置
        if has_custom_edges:
            self._display_edge_specific_settings(parameters.get("edge_specific", {}))
        
        # 检查是否需要确认车道数
        self._check_lane_number_confirmation(description, parameters, parameters.get("default.lanenumber", 0))
        
        # 提供差异化道路设置警告
        if has_custom_edges:
            print("\n注意: 差异化道路设置将使用SUMO的基本生成功能，但由于netgenerate工具的限制，")
            print("某些方向特定的参数可能需要在生成后使用SUMO-netedit手动调整。")
        
        # 询问是否要生成网络
        confirm = input("\n是否要使用这些参数生成网络？(yes/no): ").lower()
        if confirm in ['yes', 'y', '是']:
            network_path = self.integration.generate_network(network_type, parameters, output_file)
            
            if network_path:
                print(f"\n网络已生成: {network_path}")
                # 询问是否要可视化
                viz = input("是否要可视化生成的网络？(yes/no): ").lower()
                if viz in ['yes', 'y']:
                    viz_method = input("可视化方法(matplotlib/sumo-gui/export) [matplotlib]: ").lower() or "matplotlib"
                    self.integration.visualize_network(network_path, viz_method)
        else:
            print("已取消网络生成。")
    
    def visualize_mode(self, network_file: str, viz_method: str) -> None:
        """
        处理可视化模式
        
        参数:
            network_file: 网络文件路径
            viz_method: 可视化方法
        """
        if not os.path.exists(network_file):
            print(f"错误: 找不到网络文件 '{network_file}'")
            return
            
        print(f"可视化网络文件: {network_file}")
        self.integration.visualize_network(network_file, viz_method)
    
    def run(self) -> None:
        """
        运行命令行界面
        """
        args = self.parse_arguments()
        
        if args.interactive:
            self.interactive_mode()
        elif args.description:
            self.description_mode(args.description, args.output)
        elif args.visualize:
            self.visualize_mode(args.visualize, args.viz_method)
        else:
            print("未提供描述。使用--description或--interactive") 