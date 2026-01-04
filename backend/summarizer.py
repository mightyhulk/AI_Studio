import os 
import pdfplumber
from docx import Document




def summarizer(prompt):
    return True





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
            text = extract_text_from_txt(file)
        elif file_type == 'docx':
            text = extract_text_from_docx(file)
        elif file_type == 'pdf':
            text = extract_text_from_pdf(file)
        else:
            text = "Please upload correct file type (txt, docx, pdf)"
            
        final_prompt = prompt + "\n" + text
        
        summarized_text = summarizer(final_prompt)
            
    else:
        summarized_text = summarizer(prompt)
        
    return summarized_text
        
   











