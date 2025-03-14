import os
from pathlib import Path

# 尝试导入dotenv，如果安装了的话
try:
    from dotenv import load_dotenv
    # 加载.env文件
    load_dotenv()
    ENV_LOADED = True
except ImportError:
    ENV_LOADED = False
    print("提示: 未找到python-dotenv包。要使用.env文件功能，请安装: pip install python-dotenv")

# 基础路径配置
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.getenv("DEFAULT_OUTPUT_DIR", "./output"))
OUTPUT_DIR.mkdir(exist_ok=True)  # 确保输出目录存在

# SUMO相关配置
SUMO_HOME = os.getenv("SUMO_HOME")
if not SUMO_HOME and os.path.exists("/usr/share/sumo"):
    SUMO_HOME = "/usr/share/sumo"  # Linux默认安装路径

# 大模型配置
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "deepseek").lower()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VALID_LLM_PROVIDERS = ["deepseek", "openai"]

# 可视化配置
DEFAULT_VIZ_METHOD = os.getenv("DEFAULT_VIZ_METHOD", "matplotlib")
VALID_VIZ_METHODS = ["matplotlib", "sumo-gui", "export"]

# 性能配置
MAX_PARALLEL_REQUESTS = int(os.getenv("MAX_PARALLEL_REQUESTS", "4"))

# 运行时检查和警告
def check_configuration():
    """检查配置并输出警告"""
    warnings = []
    
    if not SUMO_HOME:
        warnings.append("SUMO_HOME环境变量未设置，可能影响某些功能")
    
    if LLM_PROVIDER not in VALID_LLM_PROVIDERS:
        warnings.append(f"无效的LLM提供商: {LLM_PROVIDER}。有效选项: {', '.join(VALID_LLM_PROVIDERS)}")
    elif LLM_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
        warnings.append("使用DeepSeek作为LLM提供商，但未设置DEEPSEEK_API_KEY")
    elif LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        warnings.append("使用OpenAI作为LLM提供商，但未设置OPENAI_API_KEY")
    
    if DEFAULT_VIZ_METHOD not in VALID_VIZ_METHODS:
        warnings.append(f"无效的可视化方法: {DEFAULT_VIZ_METHOD}。有效选项: {', '.join(VALID_VIZ_METHODS)}")
    
    return warnings

# 打印配置警告
for warning in check_configuration():
    print(f"警告: {warning}")

# 配置信息字典，方便访问
config = {
    "SUMO_HOME": SUMO_HOME,
    "LLM_PROVIDER": LLM_PROVIDER,
    "DEFAULT_VIZ_METHOD": DEFAULT_VIZ_METHOD,
    "OUTPUT_DIR": str(OUTPUT_DIR),
    "MAX_PARALLEL_REQUESTS": MAX_PARALLEL_REQUESTS,
    "ENV_LOADED": ENV_LOADED,
}

# API配置 - 需要根据实际API服务提供方进行配置
# ==== API服务配置选项 ====
# 以下是常见大模型API服务的配置示例，根据您的API提供商选择合适的配置

# OpenAI兼容API接口（例如Azure OpenAI、国内替代品等）
USE_OPENAI_STYLE = True  # 如果您的API使用OpenAI风格的接口，设为True
API_URL = "https://api.deepseek.com/v1/chat/completions"   # 替换为实际API URL
API_KEY = "sk-e810443c082f44ab876f55f1c8519076"  # 替换为实际API密钥
API_MODEL = "deepseek-chat"  # 模型名称，例如 "gpt-3.5-turbo"、"gpt-4" 等

# 设置环境变量，确保LLM接口能够访问API密钥
os.environ["DEEPSEEK_API_KEY"] = API_KEY 