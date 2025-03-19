from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# 模型名称
model_name = 'sentence-transformers/all-mpnet-base-v2'

# 创建 HuggingFaceEmbeddings 实例
embeddings = HuggingFaceEmbeddings(model_name=model_name)

# 创建 Chroma 实例
vector_store = Chroma(
    collection_name="example_collection",
    embedding_function=embeddings,
    persist_directory="./chroma_langchain_db",  # Where to save data locally, remove if not necessary
)


from langchain_core.documents import Document

Document_1 = Document(
    page_content="大地电磁测深法（MT）数据处理的工作流程可以包括输入，计算和输出三个部分。输入对应的工作是数据文件输入，"
    "计算对应的工作有相位张量计算，视电阻率计算，数据拆包等，输出对应的工作有数据字典的key输出，数据格式输出，"
    "视电阻率数据图像输出。",
    metadata = {"source":"forAI"},
    id = 1,
)

Document_2 = Document(
    page_content="创造文件输入节点",
    metadata = {"source":"description"},
    id = 2,
)

Document_3 = Document(
    page_content="大地电磁测深一个典型的工作流程是输入数据文件，计算视电阻率，输出视电阻率可视化图。",
    metadata = {"source":"forAI"},
    id = 3,
)

Document_4 = Document(
    page_content="创造相位张量计算节点，计算相位张量。",
    metadata = {"source":"description"},
    id = 4,
)

Document_5 = Document(
    page_content="创造视电阻率计算节点，计算视电阻率。",
    metadata = {"source":"description"},
    id = 5,
)

Document_6 = Document(
    page_content="创造数据拆包节点，将数据拆成各个量。",
    metadata = {"source":"description"},
    id = 6,
)

Document_7 = Document(
    page_content="创造数据字典的键输出节点，输出数据字典的键。",
    metadata = {"source":"description"},
    id = 7,
)

Document_8 = Document(
    page_content="创造视电阻率数据图像输出节点，绘制并输出视电阻率数据图像。",
    metadata = {"source":"description"},
    id = 8,
)

documents = [Document_1,Document_2,Document_3,Document_4,Document_5,Document_6,Document_7,Document_8]
ids = ['1','2','3','4','5','6','7','8']
vector_store.add_documents(ids = ids ,documents=documents)

results = vector_store.similarity_search_by_vector_with_relevance_scores(
    embedding=embeddings.embed_query("为了实现您的需求，可以按照以下工作流程操作：1. **数据文件输入**：导入MT测量数据文件。2. **计算相位张量和视电阻率**：利用输入数据进行必要的数学处理来计算相位张量，并进一步推导出视电阻率。3. **输出视电阻率可视化图像**：将计算得到的视电阻率结果以图像形式展示，便于分析和解读。这样您可以从数据文件中直接绘制出所需的视电阻率数据图像。"),
    k=5,
    filter={"source": "description"},
)
for res,score in results:
    print(f"*[SIM = {score:3f}] {res.page_content}")