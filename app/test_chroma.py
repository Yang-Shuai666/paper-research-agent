from app.rag.vector_store import ChromaStore

__test__ = False



def main() -> None:
    store = ChromaStore()
    documents = [
        "Transformer是一种基于自注意力机制的神经网络架构。",
        "RAG通过检索外部知识来增强大语言模型的生成能力。",
        "知识增强生成可以降低大语言模型产生幻觉的概率。",
        "向量数据库可以用于存储文本的向量表示，并进行相似度搜索。",
    ]
    ids = ["doc_001", "doc_002", "doc_003", "doc_004"]

    store.add_documents(documents, ids)

    result = store.search("什么是RAG？", n_results=2)
    print(result)


if __name__ == "__main__":
    main()