"""
项目七：AI 自动化工作流引擎
1.设计并实现企业级 AI 自动化工作流引擎，支持可视化流程编排
2.封装数据采集、AI 分析、报告生成、邮件推送等标准化任务节点
3.通过配置文件灵活编排业务流程，实现低代码 AI 自动化
4.可支撑舆情监控、自动日报、智能报表等真实业务场景
5.技术栈：Python、流程引擎、模块化设计、AI 自动化、工程化部署"""
import json
from core.llm_client import call_llm
from projects.ai_crawler.ai_crawler import fetch_webpage, parse_content
from projects.auto_report.auto_report import generate_word_report, send_email_with_report

# 加载流程
def load_workflow(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

# 执行一个节点
def run_node(node, context):
    print(f"\n▶ 执行节点：{node['name']}")
    
    if node["type"] == "crawl":
        html = fetch_webpage(node["url"])
        data = parse_content(html)
        context["title"] = data["title"]
        context["content"] = data["content"]
        
    elif node["type"] == "ai_analyze":
        prompt = f"标题：{context['title']}\n内容：{context['content']}\n生成50字摘要"
        context["summary"] = call_llm(prompt, model_name="doubao")
        
    elif node["type"] == "generate_report":
        stats = {"摘要": context["summary"]}
        generate_word_report(stats, context["summary"], node["filename"])
        context["report_path"] = node["filename"]
        
    elif node["type"] == "send_email":
        send_email_with_report(context["report_path"])

# 执行整个流程
def run_workflow(workflow):
    print(f"🚀 启动工作流：{workflow['name']}")
    context = {}
    for node in workflow["nodes"]:
        run_node(node, context)
    print("\n✅ 工作流全部执行完成！")

if __name__ == "__main__":
    wf = load_workflow("projects/workflow/config.json")
    run_workflow(wf)