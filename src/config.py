import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()],
)


class Settings:
    # DashScope exposes an OpenAI-compatible endpoint; retain OPENAI_* as fallback.
    openai_api_key: str = os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    openai_api_base: str = os.getenv(
        "OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    model_name: str = os.getenv("MODEL_NAME", "qwen-plus")
    temperature: float = float(os.getenv("TEMPERATURE", "0"))
    port: int = int(os.getenv("PORT", "7860"))
    app_title: str = "SupportPilot 多智能体客服工作台"
    app_description: str = (
        "智能分流产品咨询与工单请求，由专业智能体协作处理。"
    )


settings = Settings()
