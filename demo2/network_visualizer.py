import os
import sys
import matplotlib.pyplot as plt
import numpy as np
import subprocess
from PIL import Image
import tempfile

# 检查是否定义了SUMO_HOME环境变量
if 'SUMO_HOME' in os.environ:
    # 将SUMO工具路径添加到系统路径
    tools_path = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools_path)
else:
    sys.exit("请定义环境变量'SUMO_HOME'")

import sumolib


class NetworkVisualizer:
    """
    一个用于使用各种方法可视化SUMO网络文件的类。
    """
    
    def __init__(self):
        """初始化NetworkVisualizer."""
        # 验证SUMO工具可用性
        self.sumo_tools_path = os.path.join(os.environ.get('SUMO_HOME', ''), 'tools')
        if not os.path.exists(self.sumo_tools_path):
            print(f"警告: SUMO工具路径未找到: {self.sumo_tools_path}")
    
    def visualize_with_matplotlib(self, network_file: str, output_file: str = None, show: bool = True) -> None:
        """
        使用matplotlib可视化SUMO网络。
        
        参数:
            network_file: SUMO .net.xml文件的路径
            output_file: 保存可视化的路径（可选）
            show: 是否显示可视化
        """
        try:
            # 使用sumolib加载网络
            net = sumolib.net.readNet(network_file)
            
            # 创建图形
            plt.figure(figsize=(12, 8))
            
            # 绘制边
            for edge in net.getEdges():
                # 获取边的形状，作为x,y点的列表
                shape = edge.getShape()
                x_values = [p[0] for p in shape]
                y_values = [p[1] for p in shape]
                
                # 绘制边
                plt.plot(x_values, y_values, 'b-', linewidth=1.5)
                
                # 为多车道边绘制车道标记
                if edge.getLaneNumber() > 1:
                    # 为每个车道绘制平行线
                    for lane_idx in range(edge.getLaneNumber()):
                        lane = edge.getLane(lane_idx)
                        lane_shape = lane.getShape()
                        lane_x = [p[0] for p in lane_shape]
                        lane_y = [p[1] for p in lane_shape]
                        plt.plot(lane_x, lane_y, 'b-', linewidth=0.5, alpha=0.3)
            
            # 绘制路口
            for junction in net.getNodes():
                x, y = junction.getCoord()
                
                # 根据路口类型使用不同的颜色
                if junction.getType() == 'traffic_light':
                    color = 'red'
                    size = 80
                elif junction.getType() == 'priority':
                    color = 'orange'
                    size = 60
                else:
                    color = 'green'
                    size = 40
                
                plt.scatter(x, y, c=color, s=size, zorder=2)
            
            # 添加标题和标签
            plt.title(f"SUMO网络: {os.path.basename(network_file)}")
            plt.xlabel("X位置（米）")
            plt.ylabel("Y位置（米）")
            
            # 设置相等的纵横比
            plt.axis('equal')
            plt.grid(True, linestyle='--', alpha=0.6)
            
            # 如果指定了输出文件，则保存图形
            if output_file:
                plt.savefig(output_file, dpi=300, bbox_inches='tight')
                print(f"可视化已保存到 {output_file}")
            
            # 如果请求，则显示图形
            if show:
                plt.show()
            else:
                plt.close()
            
        except Exception as e:
            print(f"可视化网络时出错: {e}")
    
    def visualize_with_sumo_gui(self, network_file: str, wait: bool = True) -> None:
        """
        在SUMO GUI中打开网络进行交互式可视化。
        
        参数:
            network_file: SUMO .net.xml文件的路径
            wait: 是否等待SUMO-GUI关闭后再继续
        """
        try:
            # 构建打开SUMO-GUI的命令
            sumo_gui_cmd = ["sumo-gui", "-n", network_file, "--no-warnings"]
            
            print(f"在SUMO-GUI中打开网络: {network_file}")
            
            if wait:
                # 运行并等待完成
                subprocess.run(sumo_gui_cmd, check=True)
            else:
                # 在后台运行
                subprocess.Popen(sumo_gui_cmd)
                
        except subprocess.SubprocessError as e:
            print(f"打开SUMO-GUI时出错: {e}")
            
    def export_network_image(self, network_file: str, output_file: str, width: int = 1920, height: int = 1080) -> None:
        """
        使用SUMO的内置截图功能导出网络的高质量图像。
        
        参数:
            network_file: SUMO .net.xml文件的路径
            output_file: 保存图像的路径
            width: 图像宽度（像素）
            height: 图像高度（像素）
        """
        try:
            # 为SUMO创建一个临时设置文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sumocfg', delete=False) as cfg_file:
                cfg_file.write(f"""
                <configuration>
                    <input>
                        <net-file value="{network_file}"/>
                    </input>
                    <gui_only>
                        <gui-settings-file value=""/>
                    </gui_only>
                </configuration>
                """)
                cfg_path = cfg_file.name
            
            # 临时截图的路径
            temp_screenshot = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
            
            # 构建截图命令
            screenshot_cmd = [
                "sumo-gui", 
                "-c", cfg_path,
                "--no-warnings",
                "--window-size", f"{width},{height}",
                "--screenshot", 
                "--screenshot-file", temp_screenshot,
                "--quit-on-end"
            ]
            
            print(f"正在生成网络图像...")
            subprocess.run(screenshot_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 处理图像（添加边框、标签等）
            try:
                img = Image.open(temp_screenshot)
                
                # 保存最终图像
                img.save(output_file)
                print(f"网络图像已保存到 {output_file}")
                
            except Exception as img_e:
                print(f"处理图像时出错: {img_e}")
                # 回退到复制原始截图
                import shutil
                shutil.copy(temp_screenshot, output_file)
                print(f"原始截图已保存到 {output_file}")
                
            # 清理临时文件
            os.unlink(cfg_path)
            os.unlink(temp_screenshot)
            
        except Exception as e:
            print(f"导出网络图像时出错: {e}")


def main():
    """网络可视化器的命令行界面。"""
    import argparse
    
    parser = argparse.ArgumentParser(description="SUMO网络可视化器")
    parser.add_argument("network_file", help="SUMO .net.xml文件的路径")
    parser.add_argument("--output", "-o", help="保存可视化图像的路径")
    parser.add_argument("--method", "-m", choices=["matplotlib", "sumo-gui", "export"], 
                      default="matplotlib", help="可视化方法")
    parser.add_argument("--width", type=int, default=1920, help="图像宽度（用于export方法）")
    parser.add_argument("--height", type=int, default=1080, help="图像高度（用于export方法）")
    
    args = parser.parse_args()
    
    # 初始化可视化器
    visualizer = NetworkVisualizer()
    
    # 应用请求的可视化方法
    if args.method == "matplotlib":
        visualizer.visualize_with_matplotlib(args.network_file, args.output)
    elif args.method == "sumo-gui":
        visualizer.visualize_with_sumo_gui(args.network_file)
    elif args.method == "export":
        if not args.output:
            args.output = f"{os.path.splitext(args.network_file)[0]}_image.png"
        visualizer.export_network_image(args.network_file, args.output, args.width, args.height)


if __name__ == "__main__":
    main()