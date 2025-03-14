import os
import sys
import pytest
import subprocess
import tempfile
from pathlib import Path

# 确保能导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 集成测试：测试命令行接口是否正常工作
@pytest.mark.integration
def test_cli_description_to_network():
    """测试通过命令行从文本描述生成网络"""
    # 创建临时文件用于输出
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = os.path.join(tmp_dir, "test_output.net.xml")
        
        # 运行命令行工具生成网络
        result = subprocess.run([
            sys.executable, # 使用当前Python解释器
            os.path.join(os.path.dirname(__file__), "../../main.py"),
            "--description", "生成一个十字交叉口，双向4车道，车道长度200米",
            "--output", output_file
        ], capture_output=True, text=True)
        
        # 检查命令是否成功
        assert result.returncode == 0, f"命令失败: {result.stderr}"
        
        # 检查输出文件是否生成
        assert os.path.exists(output_file), "输出文件未生成"
        
        # 检查生成的文件是否包含正确的内容
        with open(output_file, 'r') as f:
            content = f.read()
            assert "<net " in content, "生成的文件不是有效的SUMO网络文件"
            assert "function=\"traffic_light\"" in content, "未找到预期的交通信号灯"

@pytest.mark.integration
def test_visualization_methods():
    """测试可视化方法是否正常工作"""
    # 此测试需要有一个已存在的网络文件
    network_file = os.path.join(os.path.dirname(__file__), "../fixtures/sample_network.net.xml")
    
    # 跳过测试如果文件不存在
    if not os.path.exists(network_file):
        pytest.skip(f"跳过测试: 需要的文件不存在: {network_file}")
    
    # 导入visualizers模块
    from visualizers import visualize_network
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_file = os.path.join(tmp_dir, "test_output.png")
        
        # 使用export方法测试，这样不需要打开GUI
        visualize_network(network_file, method="export", output_file=output_file)
        
        # 检查是否生成了输出文件
        assert os.path.exists(output_file), "可视化输出文件未生成" 