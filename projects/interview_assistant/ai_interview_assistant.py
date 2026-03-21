"""
AI项目一：AI面试助手
功能：
1.使用 Python + 大模型 API 开发模拟面试系统
2.支持岗位定制化题目生成、AI 自动评分与点评
3.实现上下文管理、历史记录保存、异常处理等工程能力
4.可直接用于面试训练、岗位刷题，提升面试通过率
2026-03-19 优化内容：
1.提供长文回答机制
2.完善异常处理，避免程序报错
3.添加姓名和时间戳以及最终综合得分，精确记录每一位考生的成绩
"""
import json
from datetime import datetime
import re
from core.llm_client import MODEL_TYPE,call_llm
from core.logger import logger

# 定义高质量面试题函数
def generate_interview_questions(model_name,job_name,num = 5):
    prompt = f"""
    角色：你是专业AI面试官
    任务：为【{job_name}】生成{num}到高频面试题。
    要求：
        1.涵盖基础理论、实战技能、项目经验、场景应变四个维度。
        2.输出格式必须纯题目的文本列表，每行一道题，不要编号，不要多余解释。
        3.题目简练清晰，表达明确。
    示例输出：
    请解释Transformer架构中的Self-Attention机制。
    如何处理大模型幻觉问题？
    ...
    """
    return call_llm(prompt,model_name,temperature=0.7)

# 定义回答评估机制函数
def score_answer(model_name,question,user_answer,job_name):
    prompt = f"""
    角色：你是【{job_name}】的资深面试官。
    任务：请对候选人的回答进行专业评估并打分（1-100分）。
    题目：{question}。
    候选人回答：{user_answer}。
    重要评分规则：
    1.若候选人未作答、回答为空、或仅包含无意义字符（如标点、空格）。必须直接给出0-5分
    2.若回答内容严重偏题或完全错误，分数不得超过30分
    3.只有回答逻辑清晰、覆盖关键点，才能给予高分
    要求：请严格按照以下三部分内容输出：
    1. 分数：xx分
    2. 优点：xxx（若无则填“无”）
    3. 不足与改进：xxx（针对空回答需明确指出“未提供有效回答”）
    语言简洁专业
    """
    return call_llm(prompt,model_name,temperature=0.4)

# 优化部分：定义实现长文回答函数
def get_multiline_input():
    print("输入回车换行，输入'END'后回车代表回答完毕并提交")
    lines = []
    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        lines.append(line)
    return "\n".join(lines)

# 持久化到json文件
def save_interview_history(user_name,job_name,qas,total):
    time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(f"interview_{user_name}.json","w",encoding="utf-8") as f:
        json.dump({
            "time": time,
            "name": user_name,
            "job": job_name,
            "records": qas,
            "total": total
        },f,ensure_ascii=False,indent=2)
        return "文件保存成功"

# 主程序
def main():
    """AI面试助手主函数"""
    logger.info("启动AI面试助手")
    SUPPORTED_JOBS = ["AI大模型应用工程师","Prompt工程师","AI数据分析工程师"]
    try:
        print("=" * 60)
        print("AI面试助手 - 专业面试训练平台")
        print("=" * 60)
        # 获取候选人信息
        name = input("请输入你的姓名：").strip()
        if not name:
            print("姓名不能为空")
            return
        # 选定可用大模型
        print("请选择模型")
        for i,m in enumerate(MODEL_TYPE):
            print(f"{i+1}.{m}")
        while True:
            try:
                choice = int(input("请输入有效序号,输入其他内容均无效：\n").strip())
                if choice not in [1,len(MODEL_TYPE)]:
                    print("序号不存在，请重新输入")
                    continue
                model_name = MODEL_TYPE[choice - 1]
                logger.info(f"已选择模型：{model_name}")
                break
            except Exception:
                logger.error("输入无效内容，请重新输入")
                continue
        print("\n可选岗位：")
        for i ,job in enumerate(SUPPORTED_JOBS,1):
            print(f"{i}.{job}")
        while True:
            try:
                choice = int(input("\n请选择岗位编号："))
                if 1 <= choice <= len(SUPPORTED_JOBS):
                    job = SUPPORTED_JOBS[choice-1]
                    break
                else:
                    print("请输入正确的职位编号")
            except ValueError:
                print("请输入数字")
        print(f"\n你选择的岗位：{job},正在生成当前岗位的面试题...\n")
    # 生成题目
        questions_text = generate_interview_questions(model_name,job)
        print("面试题目：")
        print(questions_text)
        print("-" * 60)
    # 输入回答
        qas =[]
        total = 0
        for i,q in enumerate(questions_text.strip().split("\n"),1):
            if not q:
                print("未能提取到有效题目，请检查大模型调用情况和输出格式\n")
                continue
            else:
                print(f"\n【第{i}题】：{q}")
                ans = get_multiline_input()
                # 【核心修复逻辑】前置判断回答是否为空
                if not ans:
                    print("\n检测到未作答，系统将直接判定为零分")
                    score = """1.分数：0分\n2.优点：无\n3.不足与改进：候选人未提供任何回答。建议至少尝试阐述相关思路或承认暂时不知道但给出推导过程。"""
                    print(f"\n AI点评：\n{score}")
                else:
                    score = score_answer(model_name,q,ans,job)
                    print(f"\n AI点评：\n{score}")
                    try:
                        # 通过正则表达式获取分数
                        small_score = re.search(r"分数[:：]\s*(\d+)",score).group(1)
                        total += int(small_score)
                    except Exception :
                        print("AI点评未按照要求输出，请稍后检查，继续作答")
                    qas.append({"question": q,"answer": ans,"score": score})

        save_interview_history(name,job,qas,total)
        print("\n面试完成,记录已保存")
    except KeyboardInterrupt:
        print("\n面试中断")
        logger.info("面试被用户中断")
    except Exception as e:
        logger.error(f"面试助手运行出错：{e}")
        print(f"程序出错：{e}")


if __name__ == "__main__":
    main()



        


