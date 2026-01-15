import os 
import pdfplumber
from docx import Document
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

llm=ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    api_key=os.getenv('gemini_api')
)


def summarizer(prompt):
    
    summary_prompt = PromptTemplate(
    input_variables=["text"], 
    template='''
    You are an expert text summarizer. 
    
    Summarize the following text clearly and conscisely. 
    Focus on key points and remove redundancy. 
    
    Text: {text}
    Summary: 
    '''
    )
    
    summary_chain = summary_prompt | llm
    
    result = summary_chain.invoke({"text": prompt})
    return result.content



def extract_text_from_pdf(file_path):
    """Extract text from all pages of a PDF file using pdfplumber."""
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_text_from_docx(file_path):
    """Extract text from all paragraphs in a DOCX file."""
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path):
    """Extract text from a TXT file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def get_file_type(file_path):
    _, ext = os.path.splitext(file_path)
    return ext.lower().lstrip('.')



def text_summarizer(file, prompt):
    
    if file:
        file_type = get_file_type(file) 
        if file_type == 'txt':
            context = extract_text_from_txt(file)
        elif file_type == 'docx':
            context = extract_text_from_docx(file)
        elif file_type == 'pdf':
            context = extract_text_from_pdf(file)
        else:
            context = "Please upload correct file type (txt, docx, pdf)"
            
        final_prompt = prompt + "\n" + context
        
        summarized_text = summarizer(final_prompt)
            
    else:
        summarized_text = summarizer(prompt)
        
    return summarized_text
        


