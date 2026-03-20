# 统一入口
from core.logger import logger
from projects.interview_assistant.ai_interview_assistant import main as run_interview_assistant
from projects.knowledge_base.ai_knowledge_base import main as run_knowledge_base
from projects.office_robot.ai_office_robot import main as run_office_robot

def show_menu():
    print("=" * 30)
    print("AI项目集合")
    print("=" * 30)
    print("1.AI面试助手")
    print("2.AI知识库问答")
    print("3.自动化办公机器人")
    print("0.退出")
    
def main():
    logger.info("启动AI项目集合")
    while True:
        show_menu()
        choice = input("\n请输入功能编号：")
        if choice == "1":
            run_interview_assistant()
        elif choice == "2":
            run_knowledge_base()
        elif choice == "3":
            run_office_robot()
        elif choice == "0":
            logger.info("退出程序")
            break
        else:
            print("无效输入，请重新输入")
if __name__ == "__main__":
    main()
