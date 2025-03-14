#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试修复后的CrossIntersectionGenerator
"""

from network_generators import CrossIntersectionGenerator
import os

def test_cross_intersection():
    """测试十字路口生成器"""
    print("开始测试十字路口生成器...")
    
    # 创建测试参数
    parameters = {
        "edge_specific": {
            "west": {"lanenumber": 4, "length": 200},  # 西边双向8车道
            "east": {"lanenumber": 3, "length": 300},  # 东边双向6车道
            "north": {"lanenumber": 3, "length": 300}, # 北边双向6车道
            "south": {"lanenumber": 3, "length": 200}  # 南边双向6车道
        },
        "default.speed": 13.9,  # 50km/h
        "default.type": "highway.residential",
        "junctions.type": "traffic_light"
    }
    
    # 创建生成器实例
    generator = CrossIntersectionGenerator()
    
    # 调用生成方法
    output_file = "test_fix.net.xml"
    result = generator.generate_network(parameters, output_file)
    
    # 检查结果
    if result is not None and os.path.exists(output_file):
        print(f"测试成功! 网络已生成: {output_file}")
    else:
        print("测试失败! 无法生成网络")

if __name__ == "__main__":
    test_cross_intersection() 