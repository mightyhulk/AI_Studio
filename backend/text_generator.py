import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="langchain_tavily")
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    temperature = 0,
    api_key = os.getenv('gemini_api_2')
)


tavily_tool = TavilySearch(
    max_result=3,
    search_depth="advanced"
)


def web_search(query):
    search_result = tavily_tool.invoke({"query": query})
    context = "\n".join([r.get("content") for r in search_result["results"]])
    return context

    
def text_gen(question):
    prompt = PromptTemplate(
        input_variables=["question", "context"],
        template = '''
        Use the following web search results to answer the question accurately.

Question:
{question}

Context:
{context}

Answer:       
        '''
        
    )
    
    context = web_search(question)
    text_chain = prompt | llm
    response = text_chain.invoke({"question": question, "context": context})
    return response.content
    
    

