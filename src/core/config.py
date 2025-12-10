"""配置加载"""

import json
import os
from typing import Dict, Any, Optional

from .constants import MODELS_CONFIG_FILE, CONFIG_FILE


def build_model_maps() -> Dict[str, Dict[str, Any]]:
    """解析models.json，创建模型映射"""
    model_to_backend_map = {}
    try:
        with open(MODELS_CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            models = config.get('models', [])
            for model_name in models:
                base_name = model_name
                resolution = None
                thinking = None

                if model_name.endswith("-1k"):
                    base_name = model_name[:-3]
                    resolution = "1k"
                elif model_name.endswith("-2k"):
                    base_name = model_name[:-3]
                    resolution = "2k"
                elif model_name.endswith("-4k"):
                    base_name = model_name[:-3]
                    resolution = "4k"
                
                if base_name.endswith("-low"):
                    base_name = base_name[:-4]
                    thinking = "low"
                elif base_name.endswith("-high"):
                    base_name = base_name[:-5]
                    thinking = "high"

                model_to_backend_map[model_name] = {
                    "backend_model": base_name,
                    "resolution": resolution,
                    "thinking": thinking
                }
    except Exception as e:
        print(f"⚠️ 构建模型映射失败: {e}")
    return model_to_backend_map


def load_config() -> Dict[str, Any]:
    """加载配置"""
    default_config = {
        "enable_sd_api": True,
        "enable_gui": True,
        "credential_mode": "headful",
        "headless": {
            "browser": "playwright",
            "auto_refresh_interval": 180,
            "show_browser": False,
            "idle_timeout": 600,  # 默认 10 分钟无请求自动关闭
            "restart_interval": 0   # 设为 0 禁用定时重启，由 idle_timeout 接管
        }
    }

    # 处理环境变量覆盖 idle_timeout
    idle_timeout = os.getenv("BROWSER_IDLE_TIMEOUT")
    if idle_timeout:
        try:
            default_config["headless"]["idle_timeout"] = int(idle_timeout)
        except ValueError:
            print(f"⚠️ 环境变量 BROWSER_IDLE_TIMEOUT 格式错误，使用默认值")

    # 处理环境变量覆盖 restart_interval (保持向后兼容)
    restart_interval = os.getenv("BROWSER_RESTART_INTERVAL")
    if restart_interval:
        try:
            default_config["headless"]["restart_interval"] = int(restart_interval)
        except ValueError:
            print(f"⚠️ 环境变量 BROWSER_RESTART_INTERVAL 格式错误，使用默认值")

    # 处理环境变量覆盖 enable_gui
    enable_gui_env = os.getenv("ENABLE_GUI")
    if enable_gui_env is not None:
        default_config["enable_gui"] = enable_gui_env.lower() in ('true', '1', 't')

    # 优先读取环境变量中的 API_KEY
    api_key = os.getenv("API_KEY")
    if api_key:
        default_config["api_key"] = api_key

    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if "headless" in config:
                default_config["headless"].update(config["headless"])
                del config["headless"]
            default_config.update(config)
            
            # 再次确保环境变量优先级最高
            if api_key:
                default_config["api_key"] = api_key
            
            if enable_gui_env is not None:
                default_config["enable_gui"] = enable_gui_env.lower() in ('true', '1', 't')
                
            return default_config
    except Exception as e:
        print(f"⚠️ 加载配置失败: {e}")
        return default_config