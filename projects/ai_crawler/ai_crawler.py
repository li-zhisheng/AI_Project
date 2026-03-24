"""
项目六：AI 自动化信息聚合机器人
1.基于 Python + 爬虫 + 大模型 API 开发自动化信息采集系统
2.实现网页抓取、内容解析、AI 智能提取、结构化输出全流程
3.支持批量抓取、关键词提取、内容分类、自动保存
4.适用于舆情监控、竞品分析、招聘信息收集等企业场景
5.技术栈：Python、requests、BeautifulSoup、大模型、数据处理"""
import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# 加载配置
load_dotenv()
API_KEY = os.getenv("DOUBAO_API_KEY")
API_URL = os.getenv("DOUBAO_API_URL")
MODEL_NAME = os.getenv("MODEL_NAME")

# ===================== 1. 抓取网页 =====================
def fetch_webpage(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"抓取失败：{e}")
        return None

# ===================== 2. 解析网页 =====================
def parse_content(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.string if soup.title else "无标题"
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]
    content = "\n".join(paragraphs)[:3000]  # 限制长度
    return {"title": title, "content": content}

# ===================== 3. AI 提取信息 =====================
def ai_extract_info(title, content):
    prompt = f"""
    你是信息提取专家，从文章中提取：
    1. 核心摘要（50字内）
    2. 3个关键词
    3. 文章类型（新闻/技术/招聘/其他）
    
    标题：{title}
    内容：{content}
    
    输出JSON格式：
    {{
        "summary": "",
        "keywords": [],
        "type": ""
    }}
    """
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    try:
        res = requests.post(API_URL, headers=headers, json=data, timeout=30)
        return json.loads(res.json()["choices"][0]["message"]["content"])
    except:
        return {"summary": "提取失败", "keywords": [], "type": "未知"}

# ===================== 4. 保存数据 =====================
def save_to_excel(data_list, filename="crawl_result.xlsx"):
    df = pd.DataFrame(data_list)
    df.to_excel(filename, index=False)
    print(f"✅ 数据已保存：{filename}")

# ===================== 主流程 =====================
def crawl_and_analyze(url = "https://news.baidu.com/"):
    print(f"🔍 正在抓取：{url}")
    html = fetch_webpage(url)
    if not html:
        return None
    
    data = parse_content(html)
    print(f"📄 标题：{data['title']}")
    
    print("🧠 AI 提取信息中...")
    ai_result = ai_extract_info(data["title"], data["content"])
    
    result = {
        "url": url,
        "title": data["title"],
        "summary": ai_result["summary"],
        "keywords": ", ".join(ai_result["keywords"]),
        "type": ai_result["type"],
        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    save_to_excel([result])
    return result

# ===================== 批量抓取 =====================
def batch_crawl(url_list):
    results = []
    for url in url_list:
        res = crawl_and_analyze(url)
        if res:
            results.append(res)
    save_to_excel(results)
    return results

if __name__ == "__main__":

    test_urls = [
        "https://baike.baidu.com/item/Python",
        "https://baike.baidu.com/item/人工智能",
        "https://news.baidu.com/"
    ]
    batch_crawl(test_urls)