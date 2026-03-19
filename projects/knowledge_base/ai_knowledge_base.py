"""AI项目四：AI知识库问答机器人(进阶版)
优化内容：
1.在原有代码基础上健全了更加完善的异常处理机制
2.细化功能板块，对于关键且频繁需要调整的内容降低了耦合度，方便后续变更大模型信息"""
import requests
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from langchain_community.document_loaders import PyPDFLoader,Docx2txtLoader,TextLoader
from langchain_community.vectorstores import FAISS
from langchain_core.embeddings import Embeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
MODEL_CONFIG = {
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
    }
}

MODEL_TYPE = [
    "doubao",
    "qwen"
]

for model_name in MODEL_TYPE:
    if not all(value for value in MODEL_CONFIG[model_name].values()):
       raise ValueError(f"配置错误{model_name},请检查配置文件")
  
# 定义嵌入函数（调用大模型生成向量）
class CustomEmbedding(Embeddings):
    def __init__(self,api_key,api_url,api_name):
      self.api_key = api_key
      self.api_url = api_url
      self.api_name = api_name
      self.dimension = 1024 # 实际应用根据模型文档确认

    def embed_documents(self, texts):
       """批量生成文档向量"""
       embeddings = []
       for text in texts:
          emb = self._get_embedding(text)
          if emb:
             embeddings.append(emb)
          else:
             print(f"警告：出现一段无法生成向量的文本，{len(text)}")
             embeddings.append([0.0] * self.dimension)  #占位符，防止维度错误，实际需要根据维度调整
       return embeddings
    
    def embed_query(self, text):
       emb = self._get_embedding(text)
       if emb:
            return emb
       else:
            print(f"警告：该文本无法生成向量，{len(text)}")
            emb = [0.0] * self.dimension  #占位符，防止维度错误，实际需要根据维度调整
       return emb
          
    def _get_embedding(self,text):
       headers = {
          "Authorization": f"Bearer {self.api_key}",
          "Content-Type": "application/json"
       }
       data = {
          "model": self.api_name,
          "input": text
       }
       try:
          response = requests.post(self.api_url,headers=headers,json=data,timeout=60)
          response.raise_for_status()
          result = response.json()
          if "data" in result and len(result["data"]) > 0:
             return result["data"][0]["embedding"]
          else:
             print(f"返回格式异常{result}")
             return None
       except Exception as e:
          print(f"生成向量失败{e}")
          return None       
# 加载并处理文档
def load_documents(file_path:str):
   if not os.path.exists(file_path):
      print(f"文件不存在{file_path}")
      return []
   loader = None
   if file_path.lower().endswith(".pdf"):
      loader = PyPDFLoader(file_path)
   elif file_path.lower().endswith(".docx"):
      loader = Docx2txtLoader(file_path)
   elif file_path.lower().endswith(".txt"):
      loader = TextLoader(file_path,encoding="utf-8")
   else:
      print("不支持所提供的文件格式，目前仅支持PDF/Word/txt文件格式")
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
    print(f"文档加载完成，分割为{len(split_docs)}个片段")
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
         print("加载已存在的向量库")
      except Exception as e:
         print(f"加载现有向量库失败{e}")
         db = None
   if db is None:
      if not docs:
         raise ValueError("没有文档内容创建向量库")
      db = FAISS.from_documents(docs,embedding)
      db.save_local(db_path)
      print("新向量库创建并保存成功")
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
            3.回答简洁明了，逻辑清晰
"""
   headers = {
      "Authorization": f"Bearer {MODEL_CONFIG[model_name]['key']}",
      "Content-Type": "application/json"
   }
   data = {
      "model": MODEL_CONFIG[model_name]["model"],
      "messages":[{
         "role": "user",
         "content": prompt
      }],
      "temperature": 0.3,
      "max_tokens": 2000
   }
   try:
      response = requests.post(MODEL_CONFIG[model_name]["llm_url"],headers=headers,json=data,timeout=60)
      response.raise_for_status()
      result = response.json()
      if "choices" in result and len(result["choices"]) > 0:
         return result["choices"][0]["message"]["content"]
      else:
         return "格式错误，请检查格式"
   except Exception as e:
      return f"回答生成失败{str(e)}"

# 主函数：交互逻辑
def main():
   print("=" * 60)
   print("AI知识问答机器人")
   print("=" * 60)
   print("请选择模型")
   for i,m in enumerate(MODEL_TYPE):
      print(f"{i+1}.{m}")
   try:
      choice = int(input("请输入1或2,输入其他内容均无效").strip())
      if choice not in [1,2]:
         raise ValueError("无效输入")
      model_name = MODEL_TYPE[choice - 1]
      print(f"已选择模型：{model_name}")
   except Exception:
      print("输入无效内容，程序终止")
      return
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

    