import os
import requests
import json
from dotenv import load_dotenv
from docx import Document
from openpyxl import Workbook,load_workbook
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 加载环境变量
load_dotenv()
API_KEY = os.getenv("DOUBAO_API_KEY")
API_URL = os.getenv("DOUBAO_LLM_API_URL")
MODEL_NAME = os.getenv("DOUBAO_MODEL_NAME")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_SMTP = os.getenv("EMAIL_SMTP")
EMAIL_PORT = os.getenv("EMAIL_PORT")

if not all([API_KEY,API_URL,MODEL_NAME,EMAIL_USER,EMAIL_PASS,EMAIL_SMTP,EMAIL_PORT]):
    raise ValueError("配置文件错误，请检查")

# 工具函数：调用大模型
def call_llm(prompt,temperature = 0.5):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [{
            "role": "user","content": prompt
        }],
        "temperature": temperature,
        "max_tokens": 2000
    }
    try:
        response = requests.post(API_URL,headers=headers,json=data,timeout=60)
        response.raise_for_status()
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            return f"返回格式异常{json.dumps(result, ensure_ascii=False)}"
    except Exception as e:
        return f"LLM调用失败{str(e)}"
    
# 功能一：AI生成Word文档
def ai_generate_word(content_topic,save_path="ai_generate.docx"):
    print(f"正在生成文档：{content_topic}")
    prompt = f"""
    你是专业的办公文档写手，根据主题生成完整的文档内容。
    主题{content_topic}
    要求：
    1.包含标题、副标题、正文（至少3级）
    2.格式规范，语言专业
    3.仅输出文档内容，不要多余解释
    """
    doc_content = call_llm(prompt,temperature=0.7)
    if doc_content.startswith(("LLM调用失败","返回格式异常")):
        print(f"{doc_content}")
        return None
    # 创建Word文档
    doc = Document()
    # 添加标题
    doc.add_heading(content_topic,level=1)
    # 按段落分割内容并添加
    if "\n\n" in doc_content:
        paragraphs = doc_content.split("\n\n")
    else:
        paragraphs = doc_content.split("\n")
    for para in paragraphs:
        if para.strip():
            doc.add_paragraph(para.strip())
    # 保存文档
    doc.save(save_path)
    print(f"Word文档已保存：{save_path}")
    return save_path
  
# 功能二：AI分析Excel数据
def ai_analyze_excel(file_path,save_path="ai_analysis.xlsx"):
    print(f"正在分析Excel文件：{file_path}")
    # 1.读取Excel数据
    if not os.path.exists(file_path):
        print(f"文件不存在：{file_path}")
        return None
    try:
        # 从现有路径加载xlsx文件
        wb = load_workbook(file_path)
        # 获取当前活动seet页
        ws = wb.active
        # 获取总行数
        total_row = ws.max_row
        # 动态决定读取行数，最多50条
        limit = min(total_row - 1,50)
        # 提取数据文本
        data_text = "Excle数据：\n"
        # 获取表头
        header = [cell.value for cell in ws[1]]
        data_text += f"表头：{header}\n"
        data_text += f"总行数：{total_row - 1}\n\n"
        data_text += f"部分数据样本\n"
        # 获取数据(设定限制，避免过多)
        end_row = min(limit + 1,total_row)
        for row in ws.iter_rows(min_row=2,max_row=end_row,values_only=True):
           # 过滤全空的行
           if any(cell is not None for cell in row):
               data_text += f"{row}\n"
        if total_row > limit + 1:
            data_text += "...(数据过多，仅展示部分)..."
        # AI分析数据
        prompt = f"""
        你是专业的数据分析师，分析Excel数据并生成分析报告。
        数据：{data_text}
        要求：
        1.包含数据概况、关键指标、结论建议
        2.语言简洁专业，适合放入Excel报告
        3.仅输出分析内容，不要多余解释
        """
        analysis = call_llm(prompt,temperature=0.4)
        if analysis.startswith(("LLM调用失败","返回格式异常")):
            print(f"{analysis}")
            return None
        # 生成分析报告Excel
        new_wb = Workbook()
        new_ws = new_wb.active
        new_ws.title = "数据分析报告"
        # 添加分析内容
        new_ws.cell(row=1,column=1,value="数据分析师报告")
        new_ws.cell(row=2,column=1,value="-" * 50)
        # 按行添加内容
        lines = analysis.split("\n")
        for i,line in enumerate(lines,start=3):
            if line.strip():
                new_ws.cell(row=i,column=1,value=line.strip())
        # 保存分析报告
        new_wb.save(save_path)
        print(f"数据分析报告已保存：{new_wb}")
        return save_path
    except Exception as e:
        print(f"Excel分析失败：{str(e)}")
        return None

# 功能三：AI发送个性化邮件
def ai_send_email(to_email,subject):
    print(f"正在发送邮件：{to_email}")
    # 1.AI生成邮件内容
    prompt = f"""
    你是专业的邮件写手，根据主题生成个性化邮件内容。
    收件人：{to_email}
    主题：{subject}
    要求：
    1.包含称呼、正文、结尾、署名
    2.语言礼貌专业，格式规范
    3.仅输出邮件内容，不要多余解释
    """
    email_content = call_llm(prompt,temperature=0.6)
    if email_content.startswith(("LLM调用失败","返回格式异常")):
        print(f"{email_content}")
        return False
    # 2.发送邮件
    try:
        #配置邮件服务器
        smtp_obj = smtplib.SMTP_SSL(
            host = EMAIL_SMTP,
            port = int(EMAIL_PORT) if EMAIL_PORT else 465
        )
        smtp_obj.login(
            user = EMAIL_USER,
            password = EMAIL_PASS
        )
        # 构造函数
        msg = MIMEText(email_content,"plain","utf-8")
        msg["From"] = Header(EMAIL_USER,"utf-8")
        msg["To"] = Header(to_email,"utf-8")
        msg["Subject"] = Header(subject,"utf-8")
        # 发送邮件
        smtp_obj.sendmail(
            EMAIL_USER,
            to_email,
            msg.as_string()
        )
        # 关闭邮件
        smtp_obj.quit()
        print(f"邮件已发送至：{to_email}")
        return True
    except Exception as e:
        print(f"邮件发送失败：{str(e)}")
        print("提示：请检查.env中的邮箱配置是否正确")
        return False

# 功能四：批量处理文档
def batch_process_documents(topics_list,save_dir="batch_output"):
    print(f"开始批量处理，共{len(topics_list)}个主题")
    # 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    # 批量生成
    results = []
    for i,topic in enumerate(topics_list,1):
        save_path = os.path.join(save_dir,f"文档{i}_{topic.replace(' ','_').replace('/','_')}.docx")
        path = ai_generate_word(topic,save_path)
        results.append({
            "topic": topic,
            "file_path": path,
            "status": "成功" if os.path.exists(path) else "失败"
        })
    # 生成处理报告
    report_path = os.path.join(save_dir,"批量处理报告.json")
    with open(report_path,"w",encoding="utf-8") as f:
        json.dump(results,f,ensure_ascii=False,indent=2)
    print(f"批量处理完成！报告已保存：{report_path}")
    return results

# 主函数：交互界面
def main():
    os.system("cls" if os.name == "nt" else "clear")
    print("=" * 60)
    print("AI自动化办公机器人")
    print("=" * 60)
    # 功能菜单
    menu = """
    请选择功能：
    1.AI生成Word文档
    2.AI分析Excel数据
    3.AI发送个性化邮件
    4.批量生成Word文档
    0：退出"""
    while True:
        print(menu)
        choice = input("输入功能编号：").strip()
        if choice == "0":
            print("退出程序，再见！")
            break
        elif choice == "1":
            topic = input("输入文档主题：").strip()
            if topic:
                ai_generate_word(topic)
            else:
                print("主题不能为空")
        elif choice == "2":
            file_path = input("输入Excel文件路径：").strip()
            if file_path:
                ai_analyze_excel(file_path)
            else:
                print("文件路径不能为空")
        elif choice == "3":
            to_email = input("输入收件人邮箱：").strip()
            subject = input("输入邮件主题：").strip()
            if to_email and subject:
                ai_send_email(to_email,subject)
            else:
                print("邮箱和主题都不能为空")
        elif choice == "4":
            print("批量生成Word文档（输入q结束）")
            topics = []
            while True:
                topic = input(f"输入第{len(topics) + 1}文档主题").strip()
                if topic.lower() == "q":
                    break
                if topic:
                    topics.append(topic)
            if topics:
                batch_process_documents(topics)
        else:
            print("无效选择，请重新输入!")
            input("\n按回车继续...")
            os.system("cls" if os.name == "nt" else "clear")
if __name__ == "__main__":
    main()