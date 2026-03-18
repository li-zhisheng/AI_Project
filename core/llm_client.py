# 统一大模型调用
import os
import time
import requests
import json
from dotenv import load_dotenv
from core.logger import logger

load_dotenv()

MODEL_CONFIG = {
    # 大模型相关怕配置
    "doubao": {
        "llm_url": os.getenv("DOUBAO_LLM_API_URL"),
        "model": os.getenv("DOUBAO_MODEL_NAME"),
        "key": os.getenv("DOUBAO_API_KEY"),
        "embedding_url": os.getenv("DOUBAO_EMBEDDING_API_URL"),
        "embedding_name": os.getenv("DOUBAO_EMBEDDING_NAME")
    },
    "qwen": {
        "llm_url": os.getenv("QWEN_LLM_API_URL"),
        "model": os.getenv("QWEN_MODEL_NAME"),
        "key": os.getenv("QWEN_API_KEY"),
        "embedding_url": os.getenv("QWEN_EMBEDDING_API_URL"),
        "embedding_name": os.getenv("QWEN_EMBEDDING_NAME")
    },
    # 邮箱相关配置
    "email": {
        "email_user": os.getenv("EMAIL_USER"),
        "email_pass": os.getenv("EMAIL_PASS"),
        "email_smtp": os.getenv("EMAIL_SMTP"),
        "email_port": os.getenv("EMAIL_PORT")
    }
}

# 调用模型名，方便以后添加模型
MODEL_TYPE = [
    "doubao",
    "qwen"
]
for model_name in MODEL_TYPE:
    if not all(value for value in MODEL_CONFIG[model_name].values()):
       raise ValueError(f"配置错误{model_name},请检查相关配置")
if not all(value for value in MODEL_CONFIG["email"].values()):
    raise ValueError(f"邮箱配置错误,请检查相关配置")

def call_llm(prompt,model_name,temperature=0.5,max_tokens=1500,retry=3):
    # 请求头
    headers = {
        "Authorization": f"Bearer {MODEL_CONFIG[model_name]["key"]}",
        "Content-Type": "application/json"
    }
    # 数据体
    data = {
        "model": MODEL_CONFIG[model_name]["model"],
        "messages": [{"role": "user","content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    # 重试机制
    for i in range(retry):
        try:
            response = requests.post(MODEL_CONFIG[model_name]["llm_url"],headers=headers,json=data,timeout=60)
            response.raise_for_status()
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                logger.info("LLM调用成功")
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"第{i+1}次失败，返回格式异常{json.dumps(result, ensure_ascii=False)}")
                time.sleep(1)
        except requests.exceptions.HTTPError as e:
            logger.error(f"第{i+1}次失败，网络错误{e.response.status_code}:{e.response.text}")
            time.sleep(1)
        except requests.exceptions.Timeout:
            logger.error(f"第{i+1}次失败，请求超时")
            time.sleep(1)
        except Exception as e:
            logger.error(f"第{i+1}次失败，API调用失败{str(e)}")
            time.sleep(1)
    logger.error(f"LLM连续重试后调用失败")
    return None
    


            

