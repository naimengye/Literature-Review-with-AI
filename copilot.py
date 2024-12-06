
from openai import OpenAI
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from tenacity import retry, wait_random_exponential, stop_after_attempt
import os
@retry(wait=wait_random_exponential(multiplier=1, max=40), stop=stop_after_attempt(5))
def chat_completion_request(client, messages, model="gpt-4o",
                            **kwargs):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            **kwargs
        )
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

class Copilot:
    def __init__(self):
        reader = SimpleDirectoryReader(input_dir="./data", recursive=True)
        docs = reader.load_data()
        embedding_model = HuggingFaceEmbedding(
            model_name="BAAI/bge-small-en"
        )
        self.index = VectorStoreIndex.from_documents(docs, embed_model = embedding_model,
                                                     show_progress=True)
        self.retriever = self.index.as_retriever(
                        similarity_top_k=3
                        )
        
        self.system_prompt = """
    You are an expert at analyzing academic papers and creating literature reviews. Your task is to:
    1. Focus on the related work sections and references
    2. Identify key papers and their relationships
    3. Create a comprehensive overview of how these papers relate to each other
    4. Organize the citations into meaningful categories
    5. Highlight seminal works and their influence
    
    Please structure your response with:
    - Key research themes
    - Important papers in each theme
    - How papers build upon or relate to each other
    """

    def ask(self, question, messages, openai_key=None):
        ### initialize the llm client
        self.llm_client = OpenAI(api_key = openai_key)

        ### use the retriever to get the answer
        nodes = self.retriever.retrieve(question)
        ### make answer a string with "1. <>, 2. <>, 3. <>"
        retrieved_info = "\n".join([f"{i+1}. {node.text}" for i, node in enumerate(nodes)])
        

        processed_query_prompt = """
            The user is asking a question: {question}

            The retrived information is: {retrieved_info}

            Please answer the question based on the retrieved information.

            Please highlight the information with bold text and bullet points.
        """
        
        processed_query = processed_query_prompt.format(question=question, 
                                                        retrieved_info=retrieved_info)
        
        messages = [{"role": "system", "content": self.system_prompt}] + messages + [{"role": "user", "content": processed_query}]
        response = chat_completion_request(self.llm_client, 
                                           messages = messages, 
                                           stream=True)
        
        return retrieved_info, response


