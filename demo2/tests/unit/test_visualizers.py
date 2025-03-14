import os
import sys
import pytest
import tempfile
from pathlib import Path

# 确保能导入项目模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# 导入要测试的模块
from visualizers import get_visualizer, MatplotlibVisualizer, SumoGUIVisualizer, NetworkVisualizer

# 使用fixture提供测试数据
@pytest.fixture
def sample_network_path():
    """提供示例网络文件路径"""
    return os.path.join(os.path.dirname(__file__), '../fixtures/sample_network.net.xml')

# 测试可视化器工厂函数
def test_get_visualizer():
    """测试获取不同类型的可视化器"""
    # 测试获取matplotlib可视化器
    visualizer = get_visualizer("matplotlib")
    assert isinstance(visualizer, MatplotlibVisualizer)
    
    # 测试获取sumo-gui可视化器
    visualizer = get_visualizer("sumo-gui")
    assert isinstance(visualizer, SumoGUIVisualizer)
    
    # 测试export方法返回MatplotlibVisualizer
    visualizer = get_visualizer("export")
    assert isinstance(visualizer, MatplotlibVisualizer)
    
    # 测试无效方法
    with pytest.raises(ValueError):
        get_visualizer("invalid_method")

# 测试抽象基类
def test_network_visualizer_is_abstract():
    """测试NetworkVisualizer是抽象类且不能直接实例化"""
    with pytest.raises(TypeError):
        NetworkVisualizer()

# 测试Matplotlib可视化器
def test_matplotlib_visualizer(monkeypatch, sample_network_path):
    """测试Matplotlib可视化器功能"""
    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = os.path.join(tmp_dir, "test_output.png")
        
        # 模拟matplotlib环境(防止在CI环境中运行时需要显示)
        monkeypatch.setattr('matplotlib.pyplot.savefig', lambda path: Path(path).touch())
        monkeypatch.setattr('matplotlib.pyplot.show', lambda: None)
        
        # 创建可视化器并测试
        visualizer = MatplotlibVisualizer()
        
        # 测试导出功能
        visualizer.visualize(sample_network_path, output_path)
        
        # 验证输出文件是否创建
        assert os.path.exists(output_path)

# 测试SUMO-GUI可视化器
def test_sumo_gui_visualizer(monkeypatch):
    """测试SUMO-GUI可视化器功能"""
    # 模拟subprocess.Popen以避免实际启动SUMO-GUI
    class MockPopen:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
    
    monkeypatch.setattr('subprocess.Popen', MockPopen)
    
    # 创建可视化器
    visualizer = SumoGUIVisualizer()
    
    # 确保不会抛出异常
    visualizer.visualize("dummy_path.net.xml") 