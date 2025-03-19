from langchain_ollama import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from PySide6.QtCore import QThread, Signal

class Langchainchat(QThread):
    chat_finished = Signal(str)

    system_prompt = (
    "你是一个任务解析助手，你的目标是将用户的需求转换为标准任务流程。\n"
    "任务流程由以下固定节点组成：\n"
    "- `input_file`: 读取输入文件\n"
    "- `cal_PhaseTensor`: 计算相位张量\n"
    "- `cal_Apr`: 计算视电阻率\n"
    "- `cal_UnpackData`: 数据拆包\n"
    "- `output_Key`: 输出数据字典的键\n"
    "- `output_Aprplot`: 输出视电阻率图像\n"
    "请分析用户输入，并按照正确的任务顺序生成格式化流程。\n"
    "如果用户的需求可以拆解成多个任务，请按正确顺序输出标准化流程。\n"
    "如果用户提出一个特定的节点（固定列表中的某个节点），则直接输出该节点。\n"
    "仅输出格式化流程，示例：\n"
    "- `example1`: input_file -> cal_PhaseTensor -> cal_Apr -> cal_UnpackData -> output_Key\n"
    "- `example2`: cal_Apr\n"
    "- `example3`: cal_PhaseTensor -> cal_Apr -> output_Aprplot\n"
)
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOllama(
            model="phi4",
            temperature=0.5,
            num_predict=256,
            # other params ...
        )
        self.parser = StrOutputParser()
        self.chain = self.llm | self.parser
    
    def set_human_prompt(self, prompt):
        defualt_prompt = ("仅输出格式化流程，不要有多余文字。")
        self.human_prompt = prompt+ "\n"+defualt_prompt

    def chat(self):
        messages = [
            ("system", self.system_prompt),
            ("human", self.human_prompt),
        ]
        result = self.chain.invoke(messages)
        print(result)
        self.chat_finished.emit(result)
        return result



if __name__ == "__main__":
    langchainchat = Langchainchat()
    langchainchat.set_human_prompt("加一个数据拆包节点")
    langchainchat.chat_finished.connect(print)
    langchainchat.chat()


