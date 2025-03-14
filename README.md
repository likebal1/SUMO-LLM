# SUMO-LLM 交通网络生成与可视化工具

![SUMO Logo](https://www.eclipse.org/sumo/images/sumo-logo.svg) + LLM

## 项目概述

SUMO-LLM 是一个创新的工具，它将 SUMO（Simulation of Urban MObility）交通模拟软件与先进的大语言模型（LLM）技术相结合。该工具允许交通工程师、城市规划师和研究人员使用自然语言描述来生成复杂的交通网络，并提供多种方式对网络进行可视化，无需掌握 SUMO 的复杂参数和 XML 格式。

项目特点：
- **自然语言交互**：使用中文自然语言描述生成交通网络，无需掌握复杂参数
- **多种网络类型支持**：单个交叉口、多岔路口、网格状路网、放射状/环形路网等
- **多种可视化方法**：
  - SUMO-GUI直接可视化
  - 基于Matplotlib的静态可视化
  - 网络导出功能到PNG文件
- **模块化设计**：基于抽象工厂模式的可扩展架构
- **健壮的错误处理**：用户友好的反馈机制
- **为大模型集成预留接口**：便于未来功能扩展

## 系统需求

- **Python 环境**：Python 3.6+
- **SUMO 交通模拟软件**：SUMO 1.8.0+
- **Python 依赖包**：
  - matplotlib (用于静态可视化)
  - requests (用于API通信)
  - python-dotenv (用于配置管理，可选)
  - 其他依赖项（详见requirements.txt）

## 安装指南

### 1. 安装 SUMO

首先需要安装 SUMO 交通模拟软件，并确保将其添加到系统环境变量中：

- **Windows**：从 [SUMO 官网](https://sumo.dlr.de/docs/Downloads.php) 下载安装包，安装后设置 `SUMO_HOME` 环境变量
- **Linux**：使用包管理器安装，例如 `sudo apt-get install sumo sumo-tools sumo-doc`
- **macOS**：使用 Homebrew 安装，`brew install sumo`

### 2. 克隆项目并安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/sumo-llm.git
cd sumo-llm

# 安装基本依赖
pip install -r requirements.txt

# 安装开发依赖（如需进行开发或运行测试）
pip install -r requirements-dev.txt
```

### 3. 配置环境

创建一个`.env`文件来配置环境变量：

```bash
# 复制示例配置文件
cp .env.example .env

# 编辑配置文件
# Windows
notepad .env

# Linux/Mac
nano .env
```

## 配置管理

### 配置选项

项目使用`.env`文件和环境变量管理配置。主要配置选项包括：

| 配置项 | 描述 | 默认值 | 可选值 |
|-------|------|-------|-------|
| SUMO_HOME | SUMO安装路径 | 无 | 系统中SUMO的安装路径 |
| LLM_PROVIDER | 大语言模型提供商 | deepseek | deepseek, openai |
| DEEPSEEK_API_KEY | DeepSeek API密钥 | 无 | 有效的API密钥 |
| OPENAI_API_KEY | OpenAI API密钥 | 无 | 有效的API密钥 |
| DEFAULT_VIZ_METHOD | 默认可视化方法 | matplotlib | matplotlib, sumo-gui, export |
| DEFAULT_OUTPUT_DIR | 默认输出目录 | ./output | 任何有效路径 |
| MAX_PARALLEL_REQUESTS | 最大并行请求数 | 4 | 1-10之间的整数 |

### 配置优先级

配置项会按照以下优先级加载：

1. 命令行参数（最高优先级）
2. 环境变量
3. `.env`文件中的设置
4. 代码中的默认值（最低优先级）

## 使用方法

### 交互式模式

交互式模式提供了引导式的界面，适合探索系统功能：

```bash
python main.py --interactive
```

系统会引导您描述所需的交通网络，分析您的描述，提取参数，并让您确认或修改这些参数，然后生成网络并提供可视化选项。

### 直接描述模式

如果您已经知道所需的网络类型，可以直接使用描述参数：

```bash
python main.py --description "生成一个十字交叉口，双向4车道，每个方向2车道，车道长度200米" --output crossroad.net.xml
```

### 网络可视化

对于已经生成的网络文件，可以使用以下方法进行可视化：

#### 基本用法

```python
from visualizers import visualize_network

# 使用SUMO-GUI可视化
visualize_network("path/to/network.net.xml", method="sumo-gui")

# 使用Matplotlib可视化
visualize_network("path/to/network.net.xml", method="matplotlib")

# 导出为PNG图像
visualize_network("path/to/network.net.xml", method="export")
```

#### 高级用法

```python
from visualizers import get_visualizer

# 获取特定的可视化器
visualizer = get_visualizer("matplotlib")

# 自定义可视化
visualizer.visualize("path/to/network.net.xml", output_file="custom_output.png")
```

## 项目架构

项目采用模块化设计，主要组件包括：

- `main.py` - 主程序入口点，处理命令行调用
- `sumo_llm_integration.py` - 核心集成类，协调各组件工作
- `llm_interface.py` - 大语言模型接口，处理自然语言解析
- `network_generators.py` - 网络生成器模块，负责生成各种类型的交通网络
- `visualizers.py` - 可视化模块，提供多种网络显示方式
  - `NetworkVisualizer`：抽象基类，定义可视化接口
  - `SumoGUIVisualizer`：SUMO-GUI可视化实现
  - `MatplotlibVisualizer`：基于Matplotlib的可视化实现
- `cli_handler.py` - 命令行界面处理，管理用户交互
- `config.py` - 配置管理模块，处理环境变量和配置选项

## 网络描述示例

系统能够理解多种类型的网络描述。以下是一些示例：

### 基本十字路口

```
生成一个十字交叉口，双向4车道，车道长度200米
```

### 差异化属性十字路口

```
生成一个十字路口，西边路段双向6车道，东边路段双向4车道，南北方向双向4车道，长度200米
```

### 多岔路口

```
生成一个五岔路口，双向4车道，道路长度250米
```

### 网格路网

```
生成3x3的网格路网，双向2车道，道路长度150米
```

## 测试框架

项目包含完整的测试套件，包括单元测试和集成测试。

### 测试目录结构

```
tests/
├── unit/            # 单元测试
│   ├── test_visualizers.py
│   ├── test_network_generators.py
│   └── test_llm_interface.py
├── integration/     # 集成测试
│   └── test_end_to_end.py
└── fixtures/        # 测试固定数据
    ├── sample_network.net.xml
    └── test_descriptions.json
```

### 运行测试

运行所有测试：
```bash
pytest
```

运行单元测试并生成覆盖率报告：
```bash
pytest tests/unit --cov=.
```

运行特定测试文件：
```bash
pytest tests/unit/test_visualizers.py
```

### 添加新测试

添加新功能时，建议同时添加相应的测试用例。测试文件命名应遵循`test_*.py`格式，测试函数命名应以`test_`开头。

## 大模型与交通仿真结合的发展愿景

随着大模型技术的发展，我们计划将大模型与交通仿真进一步结合，打造更加智能、高效的交通仿真与决策支持系统。

### 大模型的核心价值

- **自动化与智能化**：自动处理交通数据，生成仿真参数和场景，减少人工操作
- **决策支持**：基于仿真结果给交通管理者实时建议，优化流量、应急策略
- **用户友好性**：通过自然语言交互降低使用门槛，让非专业人士也能使用

### 重点发展方向

1. **复杂场景生成与优化**  
   - 大模型根据文本描述生成完整交通场景（流量、信号灯、车辆行为等）
   - 利用强化学习优化仿真参数，提高场景实用性

2. **实时数据集成与动态仿真**  
   - 利用SUMO的TraCI接口接入实时交通数据
   - 大模型动态调整仿真参数，构建"实时数字孪生"系统

3. **多模态融合与多网协同**  
   - 融合图像、文本、传感器数据，构建多维交通模型
   - 模拟交通网络与充电桩、5G基站等基础设施的交互，优化整体效率

### 发展路线图

- **短期目标（6个月内）**：开发自然语言驱动的仿真平台，提升用户体验，重点实现交互和参数自动化
- **中期目标（1-2年）**：将工具从"描述工具"升级为"决策沙盒"，提供实时建议和策略优化
- **长期目标（2年以上）**：构建完整的交通认知增强系统，具备认知、推理、自学习能力，革新交通治理方式

## 常见问题与提示

### 车道数解释

系统按照以下规则解释车道数：

- "双向N车道" 指每个方向N/2车道，共N车道。例如："双向4车道"表示每个方向2车道
- "每方向N车道" 直接表示单向N车道。例如："每方向2车道"表示单向2车道，双向共4车道

### 可视化需求

- matplotlib可视化需要安装matplotlib包（`pip install matplotlib`）
- SUMO-GUI可视化需要SUMO正确安装并添加到系统路径

### 配置问题

- 如果遇到"SUMO_HOME not found"错误，请确保正确设置了SUMO_HOME环境变量
- API密钥问题：请确保在.env文件或环境变量中设置了正确的API密钥

## 如何参与贡献

我们欢迎各种形式的贡献，包括但不限于：

1. 报告Bug或提出新特性建议
2. 提交代码改进
3. 改进文档
4. 分享使用经验和案例
5. 添加测试用例

### 贡献步骤

1. Fork项目仓库
2. 创建您的特性分支: `git checkout -b feature/amazing-feature`
3. 提交您的更改: `git commit -m '添加一些很棒的功能'`
4. 推送到分支: `git push origin feature/amazing-feature`
5. 提交Pull Request

### 代码规范

- 遵循PEP 8代码风格
- 所有新代码应包含适当的文档字符串
- 新功能应包含相应的测试

## 许可证

本项目采用MIT许可证。详情请参阅LICENSE文件。

## 联系方式

如有任何问题或建议，请通过以下方式联系我们：

- 邮箱：fangrenziliu@gamil.com
- GitHub Issues：https://github.com/likebal1/SUMO-LLM

---

通过结合大模型技术，我们致力于将交通仿真从工具升级为智能助手，为交通决策提供更加智能化的支持，加速智慧交通的发展进程。
