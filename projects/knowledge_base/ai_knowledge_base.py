"""AI项目四：AI知识库问答机器人
1.基于 LangChain+FAISS + 大模型 API 开发企业级知识库问答系统，支持 PDF/Word/TXT 多格式文档导入
2.实现文档分割、向量检索、精准问答核心流程，解决通用 AI 回答脱离企业私有数据的问题
3.加入异常处理、问答记录保存功能，提升系统稳定性和可追溯性
4，技术栈：Python、LangChain、FAISS 向量库、大模型 API、Prompt 工程
优化内容：
1.在原有代码基础上健全了更加完善的异常处理机制
2.细化功能板块，对于关键且频繁需要调整的内容降低了耦合度，方便后续变更大模型信息"""
import os
import json
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader,TextLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from core.llm_client import MODEL_CONFIG,MODEL_TYPE,call_llm,CustomEmbedding
from core.logger import logger
# 加载并处理文档
def load_documents(file_path:str):
   if not os.path.exists(file_path):
      logger.error(f"文件不存在{file_path}")
      return []
   loader = None
   if file_path.lower().endswith(".pdf"):
      loader = PyPDFLoader(file_path)
   elif file_path.lower().endswith(".docx"):
      loader = Docx2txtLoader(file_path)
   elif file_path.lower().endswith(".txt"):
      loader = TextLoader(file_path,encoding="utf-8")
   else:
      logger.error("不支持所提供的文件格式，目前仅支持PDF/Word/txt文件格式")
      return []
   # 处理文档
   try:
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500, # 每个片段500字
        chunk_overlap = 50, #重叠50字，保存上下文连续
        separators= ["\n\n","\n","。","！","？","，","、"," "]
    )
    split_docs = text_splitter.split_documents(docs)
    logger.info(f"文档加载完成，分割为{len(split_docs)}个片段")
    return split_docs
   except Exception as e:
      print(f"文档处理失败：{e}")
      return []


# 创建向量库并检索
def create_vector_db(docs,embedding,db_path = "knowledge_base_db"):
   """创建/加载向量库"""
   db = None
   if os.path.exists(db_path) and os.listdir(db_path):
      try:
         db = FAISS.load_local(db_path,embedding,allow_dangerous_deserialization=True)
         logger.info("加载已存在的向量库")
      except Exception as e:
         logger.error(f"加载现有向量库失败{e}")
         db = None
   if db is None:
      if not docs:
         raise ValueError("没有文档内容创建向量库")
      db = FAISS.from_documents(docs,embedding)
      db.save_local(db_path)
      logger.info("新向量库创建并保存成功")
   return db
def retrieve_similar_docs(db:FAISS,query,top_k=3):
   """检索与问题最相似的文档片段"""
   similar_docs = db.similarity_search(query,k=top_k)
   return [doc.page_content for doc in similar_docs]

# 调用大模型生成回答
def genetate_answer(model_name,query,similar_docs):
   """结合相似文档生成精准回答"""
   if not similar_docs:
      return "未找到相似文档片段，无法回答"
   prompt = f"""
            角色：你是专业的知识问答助手，仅基于提供的文档内容回答问题
            文档内容：
            {chr(10).join(similar_docs)}
            用户问题：{query}
            要求：
            1.严格基于文档内容回答，不要编造信息
            2.如果文档中没有相关内容，直接回答：”文档中未找到相关信息“
            3.回答简洁明了，逻辑清晰"""
   response = call_llm(prompt,model_name,temperature=0.3,max_tokens=2000)
   if response:
      return response
   else:
      logger.error("回答生成失败")
      return "回答生成失败"

# 主函数：交互逻辑
def main():
   print("=" * 60)
   print("AI知识问答机器人")
   print("=" * 60)
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
# 初始化嵌入函数
   embeddings = CustomEmbedding(MODEL_CONFIG[model_name]["key"],MODEL_CONFIG[model_name]["embedding_url"],MODEL_CONFIG[model_name]["embedding_name"])
# 输入文件路径
   file_path = input("\n请输入本地文件路径：").strip()
   docs = load_documents(file_path)
   if not docs:
      return
# 创建向量库
   db = create_vector_db(docs,embeddings)
# 交互问答
   print("\n知识库加载完成，开始提问（输入q结束）")
   while True:
      query = input("\n你的问题：").strip()
      if query.lower() == "q":
         print("结束问答")
         break
      if not query:
         print("请输入有效问题")
         continue
      # 检索相似问答
      similar_docs = retrieve_similar_docs(db,query)
      # 生成回答
      answer = genetate_answer(model_name,query,similar_docs)
      # 输出结果
      print(f"\nAI回答：{answer}")

      # 保存文件
      log_entry = {
         "timestamp": datetime.now().isoformat(),
         "query": query,
         "answer": answer,
         "similar_docs": len(similar_docs)
      }
      with open("kb_qa_history.json","a",encoding="utf-8") as f:
         f.write(json.dumps(log_entry,ensure_ascii=False) + "\n")

if __name__ == "__main__":
   main()

    