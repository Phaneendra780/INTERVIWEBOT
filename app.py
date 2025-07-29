import streamlit as st
import os
import pandas as pd
from PIL import Image
from io import BytesIO
from phi.agent import Agent
from phi.model.google import Gemini
from phi.tools.tavily import TavilyTools
from tempfile import NamedTemporaryFile
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.units import inch
from datetime import datetime
import re
import json
import PyPDF2
import docx

# Set page configuration
st.set_page_config(
    page_title="InterviewAI - Smart Interview Preparation",
    layout="wide",
    initial_sidebar_state="collapsed",
    page_icon="🎯"
)

# Custom CSS for white theme with perfect contrast - FIXED VERSION
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Root variables - Enhanced contrast */
    :root {
        --primary-white: #FFFFFF;
        --secondary-white: #FAFAFA;
        --light-gray: #F5F5F5;
        --medium-gray: #E0E0E0;
        --primary-white: #FFFFFF;
        --text-primary: #1A1A1A;
        --text-secondary: #404040;
        --text-light: #666666;
        --accent-blue: #1E40AF;
        --accent-blue-light: #3B82F6;
        --accent-green: #059669;
        --accent-orange: #EA580C;
        --border-color: #D1D5DB;
        --border-color-dark: #9CA3AF;
        --shadow-light: 0 2px 8px rgba(0, 0, 0, 0.08);
        --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.12);
        --focus-ring: 0 0 0 3px rgba(30, 64, 175, 0.2);
    }
    
    /* Main app styling */
    .stApp {
        background-color: var(--primary-white);
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: var(--text-primary);
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
     footer {visibility: hidden;}
   
      
    
    
    /* Custom header styling */
    .main-header {
        
        padding: 2rem 0;
        border-bottom: 2px solid var(--border-color);
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .main-header h1 {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 3rem !important;
        margin-bottom: 0.5rem !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .main-header .subtitle {
        color: var(--text-secondary) !important;
        font-size: 1.2rem !important;
        font-weight: 400 !important;
        margin-top: 0 !important;
    }
    
    /* Title styling */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
    }
    
    /* Main title */
    .stApp > div > div > div > div > h1 {
        color: var(--text-primary) !important;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 0.5rem !important;
        border-bottom: 3px solid var(--accent-blue);
        padding-bottom: 1rem;
    }
    
    /* Subtitle */
    .stApp > div > div > div > div > div[data-testid="stMarkdownContainer"] h2 {
        color: var(--text-secondary) !important;
        font-size: 1.3rem !important;
        font-weight: 500 !important;
        margin-top: 0 !important;
    }
    
    /* Text content - Enhanced contrast */
    p, div, span, li {
        color: var(--text-primary) !important;
        line-height: 1.6 !important;
    }
    
    /* Card-like containers */
    .stContainer > div {
        background-color: var(--primary-white);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-light);
    }
    
    /* Info boxes - Enhanced contrast */
    .stInfo {
        background-color: var(--secondary-white) !important;
        border: 1px solid var(--accent-blue) !important;
        border-left: 4px solid var(--accent-blue) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow-light) !important;
    }
    
    .stInfo > div {
        color: var(--text-primary) !important;
    }
    
    .stInfo div[data-testid="stMarkdownContainer"] p {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Success boxes */
    .stSuccess {
        background-color: var(--secondary-white) !important;
        border: 1px solid var(--accent-green) !important;
        border-left: 4px solid var(--accent-green) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow-light) !important;
    }
    
    .stSuccess > div {
        color: var(--text-primary) !important;
    }
    
    .stSuccess div[data-testid="stMarkdownContainer"] p {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Error boxes */
    .stError {
        background-color: var(--secondary-white) !important;
        border: 1px solid var(--accent-orange) !important;
        border-left: 4px solid var(--accent-orange) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow-light) !important;
    }
    
    .stError > div {
        color: var(--text-primary) !important;
    }
    
    .stError div[data-testid="stMarkdownContainer"] p {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Buttons - Enhanced contrast */
    .stButton > button {
        background-color: var(--accent-blue) !important;
        color: var(--primary-white) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: var(--shadow-light) !important;
        text-transform: none !important;
        letter-spacing: 0.5px !important;
        min-height: 3rem !important;
    }
    
    .stButton > button:hover {
        background-color: #1E3A8A !important;
        box-shadow: var(--shadow-medium) !important;
        transform: translateY(-2px) !important;
    }
    
    .stButton > button:focus {
        outline: none !important;
        box-shadow: var(--focus-ring) !important;
    }
    
    .stButton > button:disabled {
        background-color: var(--medium-gray) !important;
        color: var(--text-light) !important;
        cursor: not-allowed !important;
        transform: none !important;
        box-shadow: none !important;
    }
    
    /* Input fields - Enhanced contrast */
    .stTextInput > div > div > input {
        background-color: var(--primary-white) !important;
        border: 2px solid var(--border-color-dark) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        padding: 0.75rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        transition: border-color 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: var(--focus-ring) !important;
        outline: none !important;
    }
    
    .stTextInput > div > div > input::placeholder {
        color: var(--text-light) !important;
        opacity: 0.8 !important;
    }
    
    /* Text areas - Enhanced contrast */
    .stTextArea > div > div > textarea {
        background-color: var(--primary-white) !important;
        border: 2px solid var(--border-color-dark) !important;
        border-radius: 8px !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        line-height: 1.6 !important;
        transition: border-color 0.3s ease !important;
    }
    
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-blue) !important;
        box-shadow: var(--focus-ring) !important;
        outline: none !important;
    }
    
    .stTextArea > div > div > textarea::placeholder {
        color: var(--text-light) !important;
        opacity: 0.8 !important;
    }
    
    /* Select boxes - MAJOR FIX for dropdown contrast */
    .stSelectbox > div > div {
        background-color: var(--primary-white) !important;
        border: 2px solid var(--border-color-dark) !important;
        border-radius: 8px !important;
        min-height: 3rem !important;
    }
    
    .stSelectbox > div > div > div {
        color: var(--text-primary) !important;
        padding: 0.75rem !important;
        font-weight: 500 !important;
    }
    
    /* Dropdown menu items - CRITICAL FIX */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: var(--primary-white) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color-dark) !important;
    }
    
    /* Dropdown options list */
    .stSelectbox ul {
        background-color: var(--primary-white) !important;
        border: 2px solid var(--border-color-dark) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow-medium) !important;
        max-height: 200px !important;
        overflow-y: auto !important;
    }
    
    .stSelectbox li {
        background-color: var(--primary-white) !important;
        color: var(--text-primary) !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        border-bottom: 1px solid var(--light-gray) !important;
        cursor: pointer !important;
    }
    
    .stSelectbox li:hover {
        background-color: var(--light-gray) !important;
        color: var(--text-primary) !important;
    }
    
    .stSelectbox li:last-child {
        border-bottom: none !important;
    }
    
    /* Selected option in dropdown */
    .stSelectbox div[aria-selected="true"] {
        background-color: var(--accent-blue) !important;
        color: var(--primary-white) !important;
        font-weight: 600 !important;
    }
    
    /* Dropdown arrow */
    .stSelectbox svg {
        fill: var(--text-primary) !important;
    }
    
    /* File uploader - Enhanced contrast */
    .stFileUploader > div {
        background-color: var(--secondary-white) !important;
        border: 2px dashed var(--border-color-dark) !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        text-align: center !important;
        transition: all 0.3s ease !important;
    }
    
    .stFileUploader > div:hover {
        border-color: var(--accent-blue) !important;
        background-color: var(--light-gray) !important;
    }
    
    .stFileUploader > div > div {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Progress bar - Enhanced visibility */
    .stProgress > div > div > div {
        background-color: var(--accent-blue) !important;
        border-radius: 10px !important;
    }
    
    .stProgress > div > div {
        background-color: var(--medium-gray) !important;
        border-radius: 10px !important;
        border: 1px solid var(--border-color) !important;
    }
    
    /* Expanders - Enhanced contrast */
    .streamlit-expanderHeader {
        background-color: var(--secondary-white) !important;
        border: 2px solid var(--border-color-dark) !important;
        border-radius: 8px 8px 0 0 !important;
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        cursor: pointer !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: var(--light-gray) !important;
        border-color: var(--accent-blue) !important;
    }
    
    .streamlit-expanderContent {
        background-color: var(--primary-white) !important;
        border: 2px solid var(--border-color-dark) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
        padding: 1.5rem !important;
    }
    
    /* Expander arrow */
    .streamlit-expanderHeader svg {
        fill: var(--text-primary) !important;
    }
    
    /* Columns */
    .stColumn {
        background-color: var(--primary-white);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem;
        box-shadow: var(--shadow-light);
        border: 1px solid var(--border-color);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: var(--accent-blue) !important;
    }
    
    /* Labels - Enhanced contrast */
    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stFileUploader > label {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* Metric styling */
    .stMetric {
        background-color: var(--secondary-white) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        text-align: center !important;
        box-shadow: var(--shadow-light) !important;
    }
    
    .stMetric > div {
        color: var(--text-primary) !important;
    }
    
    /* Custom section headers */
    .section-header {
        background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2rem !important;
        font-weight: 700 !important;
        margin: 2rem 0 1rem 0 !important;
        text-align: center;
    }
    
    /* Stage indicators */
    .stage-indicator {
        background: linear-gradient(135deg, var(--secondary-white) 0%, var(--light-gray) 100%);
        border: 2px solid var(--accent-blue);
        border-radius: 50px;
        padding: 0.5rem 1.5rem;
        color: var(--accent-blue) !important;
        font-weight: 600;
        font-size: 1rem;
        text-align: center;
        margin-bottom: 1rem;
        display: inline-block;
    }
    
    /* Conversation history styling */
    .conversation-entry {
        background-color: var(--secondary-white);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: var(--shadow-light);
    }
    
    /* Custom balloons effect */
    .celebration {
        background: linear-gradient(45deg, var(--accent-blue), var(--accent-green), var(--accent-orange));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        text-align: center;
        margin: 2rem 0;
        animation: bounce 2s infinite;
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    
    /* Help text */
    .help-text {
        color: var(--text-secondary) !important;
        font-size: 0.9rem !important;
        font-style: italic !important;
        margin-top: 0.5rem !important;
    }
    
    /* Enhanced accessibility - Improved focus indicators */
    *:focus-visible {
        outline: 3px solid var(--accent-blue) !important;
        outline-offset: 2px !important;
        border-radius: 4px !important;
    }
    
    /* High contrast text */
    strong, b {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
    }
    
    /* Custom dividers */
    hr {
        border: none !important;
        height: 2px !important;
        background: linear-gradient(90deg, transparent, var(--border-color-dark), transparent) !important;
        margin: 2rem 0 !important;
    }
    
    /* Subheader styling */
    .stSubheader {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Markdown content in containers */
    .stMarkdown p {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Textarea disabled state */
    .stTextArea textarea:disabled {
        background-color: var(--light-gray) !important;
        color: var(--text-secondary) !important;
        opacity: 0.8 !important;
    }
    
    /* Loading states */
    .stSpinner {
        color: var(--accent-blue) !important;
    }
    
    /* Warning boxes */
    .stWarning {
        background-color: var(--secondary-white) !important;
        border: 1px solid var(--accent-orange) !important;
        border-left: 4px solid var(--accent-orange) !important;
        color: var(--text-primary) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow-light) !important;
    }
    
    .stWarning > div {
        color: var(--text-primary) !important;
    }
    
    .stWarning div[data-testid="stMarkdownContainer"] p {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem !important;
        }
        
        .main-header .subtitle {
            font-size: 1rem !important;
        }
        
        .stColumn {
            margin: 0.25rem;
            padding: 0.75rem;
        }
        
        .stButton > button {
            padding: 0.5rem 1rem !important;
            font-size: 0.9rem !important;
        }
    }
    
    /* Dark mode compatibility (if needed) */
    @media (prefers-color-scheme: dark) {
        :root {
            --primary-white: #FFFFFF;
            --secondary-white: #FAFAFA;
            --text-primary: #1A1A1A;
            --text-secondary: #404040;
        }
    }
    
    /* Ensure all text is readable */
    div, p, span, label, input, textarea, select, button {
        color: var(--text-primary) !important;
    }
    
    /* Override any Streamlit defaults that might interfere */
    .stApp div[data-testid="stMarkdownContainer"] * {
        color: var(--text-primary) !important;
    }
    
    /* Fix for selectbox placeholder */
    .stSelectbox div[data-baseweb="select"] div[role="combobox"] {
        color: var(--text-primary) !important;
    }
    
    /* Fix for selectbox icon */
    .stSelectbox div[data-baseweb="select"] svg {
        fill: var(--text-primary) !important;
    }
</style>
""", unsafe_allow_html=True)

# API Keys
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY")
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY")

# Check if API keys are available
if not TAVILY_API_KEY or not GOOGLE_API_KEY:
    st.error("🔑 API keys are missing. Please check your configuration.")
    st.stop()

# Job categories and roles
JOB_CATEGORIES = {
    "Technology": [
        "Software Engineer", "Data Scientist", "Machine Learning Engineer", 
        "DevOps Engineer", "Cybersecurity Analyst", "Product Manager",
        "UI/UX Designer", "Full Stack Developer", "Backend Developer",
        "Frontend Developer", "Cloud Architect", "AI Engineer"
    ],
    "Finance": [
        "Financial Analyst", "Investment Banker", "Risk Manager",
        "Portfolio Manager", "Accountant", "Financial Planner",
        "Quantitative Analyst", "Treasury Analyst"
    ],
    "Marketing": [
        "Digital Marketing Manager", "Content Marketing Specialist",
        "Social Media Manager", "Brand Manager", "SEO Specialist",
        "Marketing Analyst", "Growth Hacker"
    ],
    "Healthcare": [
        "Nurse", "Doctor", "Healthcare Administrator", "Medical Technician",
        "Pharmacist", "Physical Therapist", "Healthcare Analyst"
    ],
    "Consulting": [
        "Management Consultant", "Strategy Consultant", "Business Analyst",
        "Operations Consultant", "IT Consultant"
    ],
    "Sales": [
        "Sales Representative", "Account Manager", "Business Development Manager",
        "Sales Engineer", "Customer Success Manager"
    ]
}

# System prompts for different agents
RESUME_ANALYSIS_PROMPT = """
You are an expert HR professional and resume analyst with years of experience in talent acquisition.
Your role is to thoroughly analyze resumes and provide comprehensive insights about a candidate's qualifications, strengths, weaknesses, and suitability for specific roles.

Analyze the provided resume content and extract:
1. Key skills and technical competencies
2. Work experience and career progression
3. Educational background
4. Notable achievements and projects
5. Areas of expertise
6. Potential weaknesses or gaps
7. Overall career trajectory and level (entry, mid, senior)

Provide actionable insights that can be used to tailor interview questions and assess candidate fit.
"""

INTERVIEW_QUESTIONS_SCRAPER_PROMPT = """
You are an expert interview preparation specialist with deep knowledge of recruitment processes across industries.
Your role is to research and compile comprehensive interview questions for specific companies and job roles.

When given a company name and job role, use web search to find:
1. Company-specific interview questions and experiences
2. Technical questions relevant to the role
3. Behavioral questions commonly asked
4. Company culture and value-based questions
5. Role-specific scenarios and case studies
6. Recent interview experiences shared by candidates
7. Questions about company products, services, and challenges

Compile this information into a structured format categorized by question type (technical, behavioral, company-specific, etc.).
Focus on authentic, recently reported interview questions rather than generic ones.
"""

INTERVIEW_CONDUCTOR_PROMPT = """
You are an experienced interview conductor and career coach with expertise in conducting professional interviews across various industries.
Your role is to conduct realistic, adaptive mock interviews that help candidates prepare effectively.

Based on the candidate's resume analysis and researched company questions, conduct an interview that:
1. Starts with appropriate warm-up questions
2. Progresses logically through different question types
3. Adapts difficulty based on candidate responses
4. Provides realistic follow-up questions
5. Maintains professional interview atmosphere
6. Gives constructive feedback after each response
7. Tracks interview progress and performance

Be encouraging but realistic, and provide specific suggestions for improvement.
"""

@st.cache_resource
def get_resume_agent():
    """Initialize and cache the resume analysis agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=RESUME_ANALYSIS_PROMPT,
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing resume agent: {e}")
        return None

@st.cache_resource
def get_questions_agent():
    """Initialize and cache the interview questions scraper agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=INTERVIEW_QUESTIONS_SCRAPER_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing questions agent: {e}")
        return None

@st.cache_resource
def get_interview_agent():
    """Initialize and cache the interview conductor agent."""
    try:
        return Agent(
            model=Gemini(id="gemini-2.0-flash-exp", api_key=GOOGLE_API_KEY),
            system_prompt=INTERVIEW_CONDUCTOR_PROMPT,
            tools=[TavilyTools(api_key=TAVILY_API_KEY)],
            markdown=True,
        )
    except Exception as e:
        st.error(f"❌ Error initializing interview agent: {e}")
        return None

def extract_text_from_pdf(file):
    """Extract text from PDF file."""
    try:
        reader = PyPDF2.PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

def extract_text_from_docx(file):
    """Extract text from DOCX file."""
    try:
        doc = docx.Document(file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
        return None

def extract_text_from_txt(file):
    """Extract text from TXT file."""
    try:
        return str(file.read(), "utf-8")
    except Exception as e:
        st.error(f"Error reading TXT: {e}")
        return None

def analyze_resume(resume_text, job_role):
    """Analyze resume content using AI."""
    agent = get_resume_agent()
    if agent is None:
        return None

    try:
        with st.spinner("🔍 Analyzing your resume..."):
            prompt = f"""
            Analyze this resume for a {job_role} position:
            
            Resume Content:
            {resume_text}
            
            Provide a comprehensive analysis including:
            - Key strengths and skills
            - Experience level assessment
            - Areas for improvement
            - Fit for {job_role} role
            - Specific technical/domain expertise
            """
            response = agent.run(prompt)
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error analyzing resume: {e}")
        return None

def scrape_interview_questions(company_name, job_role):
    """Scrape interview questions for specific company and role."""
    agent = get_questions_agent()
    if agent is None:
        return None

    try:
        with st.spinner(f"🌐 Researching interview questions for {company_name}..."):
            prompt = f"""
            Research and compile comprehensive interview questions for:
            Company: {company_name}
            Job Role: {job_role}
            
            Find and organize:
            1. Company-specific interview questions
            2. Technical questions for {job_role}
            3. Behavioral questions
            4. Culture and values-based questions
            5. Recent candidate experiences
            
            Focus on authentic, recently reported questions from reliable sources.
            """
            response = agent.run(prompt)
            return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error scraping interview questions: {e}")
        return None

def conduct_interview_session(resume_analysis, interview_questions, job_role, company_name, question_number, conversation_history):
    """Conduct the interview session."""
    agent = get_interview_agent()
    if agent is None:
        return None

    try:
        prompt = f"""
        You are conducting a mock interview for a {job_role} position at {company_name}.
        
        Candidate Profile Summary:
        {resume_analysis[:500]}...
        
        Available Interview Questions Research:
        {interview_questions[:1000]}...
        
        Current Interview State:
        - Question Number: {question_number}
        - Conversation History: {conversation_history}
        
        Based on the above information:
        1. If this is question 1, start with a warm welcome and brief company/role introduction
        2. Ask an appropriate interview question for question number {question_number}
        3. Make it progressive (start easy, increase difficulty)
        4. Consider the candidate's background from resume analysis
        5. Use company-specific questions when appropriate
        6. Keep the question focused and professional
        
        Only provide the question, not the expected answer.
        """
        
        response = agent.run(prompt)
        return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error conducting interview: {e}")
        return None

def evaluate_answer(question, answer, resume_analysis, job_role):
    """Evaluate candidate's answer and provide feedback."""
    agent = get_interview_agent()
    if agent is None:
        return None

    try:
        prompt = f"""
        Evaluate this interview answer:
        
        Question: {question}
        Answer: {answer}
        Job Role: {job_role}
        Candidate Background: {resume_analysis[:300]}...
        
        Provide:
        1. Score out of 10
        2. Strengths in the answer
        3. Areas for improvement
        4. Specific suggestions
        5. Whether to continue or dive deeper
        
        Be constructive and encouraging while being honest about areas for improvement.
        """
        
        response = agent.run(prompt)
        return response.content.strip()
    except Exception as e:
        st.error(f"🚨 Error evaluating answer: {e}")
        return None

def main():
    # Initialize session state
    if 'stage' not in st.session_state:
        st.session_state.stage = 'job_selection'
    if 'selected_job' not in st.session_state:
        st.session_state.selected_job = None
    if 'company_name' not in st.session_state:
        st.session_state.company_name = ""
    if 'resume_text' not in st.session_state:
        st.session_state.resume_text = None
    if 'resume_analysis' not in st.session_state:
        st.session_state.resume_analysis = None
    if 'interview_questions' not in st.session_state:
        st.session_state.interview_questions = None
    if 'current_question_num' not in st.session_state:
        st.session_state.current_question_num = 1
    if 'conversation_history' not in st.session_state:
        st.session_state.conversation_history = []
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'answer_submitted' not in st.session_state:
        st.session_state.answer_submitted = False
    if 'current_answer' not in st.session_state:
        st.session_state.current_answer = ""
    if 'current_feedback' not in st.session_state:
        st.session_state.current_feedback = ""

    # Custom Header
    st.markdown("""
    <div class="main-header">
        <h1>🎯 InterviewAI</h1>
        <div class="subtitle">Smart Interview Preparation with AI-Powered Mock Interviews</div>
    </div>
    """, unsafe_allow_html=True)

    # Stage 1: Job Selection
    if st.session_state.stage == 'job_selection':
        st.markdown('<div class="stage-indicator">Step 1 of 5: Job Selection</div>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">🎯 Select Your Target Job</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Choose Job Category")
            selected_category = st.selectbox(
                "Select a category:",
                list(JOB_CATEGORIES.keys()),
                help="Choose the industry category that matches your target role"
            )
            
            st.subheader("Choose Specific Role")
            selected_role = st.selectbox(
                "Select a job role:",
                JOB_CATEGORIES[selected_category],
                help="Select the specific position you're preparing for"
            )
            
            st.subheader("Target Company")
            company_name = st.text_input(
                "Enter the company name:",
                placeholder="e.g., Google, Microsoft, Goldman Sachs",
                help="Enter the specific company you're interviewing with"
            )
        
        with col2:
            st.subheader("📋 What happens next?")
            st.info("""
            **Step 1:** Select your target job role and company
            
            **Step 2:** Upload your resume for analysis
            
            **Step 3:** AI will research company-specific interview questions
            
            **Step 4:** Start your personalized mock interview
            
            **Step 5:** Get real-time feedback and suggestions
            """)
            
            if selected_role and company_name:
                st.success(f"✅ Selected: **{selected_role}** at **{company_name}**")
        
        if st.button("Continue to Resume Upload", disabled=not (selected_role and company_name)):
            st.session_state.selected_job = selected_role
            st.session_state.company_name = company_name
            st.session_state.stage = 'resume_upload'
            st.rerun()

    # Stage 2: Resume Upload and Analysis
    elif st.session_state.stage == 'resume_upload':
        st.markdown('<div class="stage-indicator">Step 2 of 5: Resume Upload & Analysis</div>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📄 Upload Your Resume</h2>', unsafe_allow_html=True)
        
        # Display selected job info
        st.info(f"**Target Position:** {st.session_state.selected_job} at {st.session_state.company_name}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            uploaded_file = st.file_uploader(
                "Upload your resume",
                type=["pdf", "docx", "txt"],
                help="Upload your resume in PDF, DOCX, or TXT format"
            )
            
            if uploaded_file:
                st.success(f"✅ Uploaded: {uploaded_file.name}")
                
                # Extract text based on file type
                if uploaded_file.type == "application/pdf":
                    resume_text = extract_text_from_pdf(uploaded_file)
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    resume_text = extract_text_from_docx(uploaded_file)
                else:
                    resume_text = extract_text_from_txt(uploaded_file)
                
                if resume_text:
                    st.session_state.resume_text = resume_text
                    
                    with st.expander("📖 Preview Resume Content"):
                        st.text_area("Resume Text", resume_text[:1000] + "..." if len(resume_text) > 1000 else resume_text, height=200, disabled=True)
        
        with col2:
            if st.session_state.resume_text:
                st.subheader("🔍 Ready for Analysis")
                st.write("Your resume has been successfully uploaded and is ready for AI analysis.")
                
                if st.button("🚀 Analyze Resume & Research Interview Questions", use_container_width=True):
                    # Analyze resume
                    resume_analysis = analyze_resume(st.session_state.resume_text, st.session_state.selected_job)
                    if resume_analysis:
                        st.session_state.resume_analysis = resume_analysis
                        
                        # Research interview questions
                        interview_questions = scrape_interview_questions(st.session_state.company_name, st.session_state.selected_job)
                        if interview_questions:
                            st.session_state.interview_questions = interview_questions
                            st.session_state.stage = 'preparation_complete'
                            st.success("🎉 Analysis complete! Ready to start your mock interview.")
                            st.rerun()
            else:
                st.info("👆 Please upload your resume to proceed")

    # Stage 3: Preparation Complete - Show Analysis
    elif st.session_state.stage == 'preparation_complete':
        st.markdown('<div class="stage-indicator">Step 3 of 5: Preparation Analysis</div>', unsafe_allow_html=True)
        st.markdown('<h2 class="section-header">📊 Preparation Analysis Complete</h2>', unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 Resume Analysis")
            with st.expander("View Detailed Resume Analysis", expanded=True):
                st.write(st.session_state.resume_analysis)
        
        with col2:
            st.subheader("❓ Researched Interview Questions")
            with st.expander("View Company Interview Intelligence", expanded=True):
                st.write(st.session_state.interview_questions)
        
        st.markdown('<h2 class="section-header">🎤 Ready to Start Mock Interview</h2>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Start Mock Interview", use_container_width=True):
                st.session_state.stage = 'interview'
                st.rerun()

    # Stage 4: Interview Conduct
    elif st.session_state.stage == 'interview':
        st.markdown('<div class="stage-indicator">Step 4 of 5: Mock Interview Session</div>', unsafe_allow_html=True)
        st.markdown(f'<h2 class="section-header">🎤 Mock Interview: {st.session_state.selected_job} at {st.session_state.company_name}</h2>', unsafe_allow_html=True)
        
        # Progress indicator
        progress = min(st.session_state.current_question_num / 10, 1.0)
        st.progress(progress, text=f"Question {st.session_state.current_question_num} of 10")
        
        # Get current question if not available
        if not st.session_state.current_question:
            question = conduct_interview_session(
                st.session_state.resume_analysis,
                st.session_state.interview_questions,
                st.session_state.selected_job,
                st.session_state.company_name,
                st.session_state.current_question_num,
                str(st.session_state.conversation_history[-3:])  # Last 3 exchanges
            )
            st.session_state.current_question = question
        
        # Display current question
        if st.session_state.current_question:
            st.subheader(f"Question {st.session_state.current_question_num}:")
            st.write(st.session_state.current_question)
            
            # Show answer input only if answer hasn't been submitted
            if not st.session_state.answer_submitted:
                # Answer input
                answer = st.text_area(
                    "Your Answer:",
                    height=150,
                    placeholder="Type your answer here...",
                    key=f"answer_{st.session_state.current_question_num}"
                )
                
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col2:
                    if st.button("Submit Answer", use_container_width=True, disabled=not answer.strip()):
                        # Evaluate answer
                        feedback = evaluate_answer(
                            st.session_state.current_question,
                            answer,
                            st.session_state.resume_analysis,
                            st.session_state.selected_job
                        )
                        
                        # Store the answer and feedback
                        st.session_state.current_answer = answer
                        st.session_state.current_feedback = feedback
                        st.session_state.answer_submitted = True
                        
                        # Store conversation
                        st.session_state.conversation_history.append({
                            'question_num': st.session_state.current_question_num,
                            'question': st.session_state.current_question,
                            'answer': answer,
                            'feedback': feedback
                        })
                        
                        st.rerun()
            
            # Show feedback and next question button if answer has been submitted
            if st.session_state.answer_submitted:
                st.success("✅ Answer submitted!")
                
                # Display the submitted answer
                st.subheader("Your Answer:")
                st.write(st.session_state.current_answer)
                
                # Display feedback
                with st.expander("📝 Feedback on Your Answer", expanded=True):
                    st.write(st.session_state.current_feedback)
                
                # Navigation buttons
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col2:
                    # Move to next question or finish interview
                    if st.session_state.current_question_num < 10:
                        if st.button("➡️ Next Question", use_container_width=True):
                            # Reset for next question
                            st.session_state.current_question_num += 1
                            st.session_state.current_question = None
                            st.session_state.answer_submitted = False
                            st.session_state.current_answer = ""
                            st.session_state.current_feedback = ""
                            st.rerun()
                    else:
                        if st.button("🏁 Finish Interview", use_container_width=True):
                            st.session_state.stage = 'interview_complete'
                            st.rerun()
        
        # Show conversation history
        if st.session_state.conversation_history:
            st.subheader("📜 Interview History")
            for entry in st.session_state.conversation_history:
                with st.expander(f"Question {entry['question_num']}", expanded=False):
                    st.write(f"**Q:** {entry['question']}")
                    st.write(f"**A:** {entry['answer']}")
                    st.write(f"**Feedback:** {entry['feedback']}")

    # Stage 5: Interview Complete
    elif st.session_state.stage == 'interview_complete':
        st.markdown('<div class="stage-indicator">Step 5 of 5: Interview Complete</div>', unsafe_allow_html=True)
        st.markdown('<div class="celebration">🎉 Interview Complete! 🎉</div>', unsafe_allow_html=True)
        st.balloons()
        
        st.markdown('<h2 class="section-header">📊 Interview Summary</h2>', unsafe_allow_html=True)
        
        # Display all Q&A with feedback
        for entry in st.session_state.conversation_history:
            with st.expander(f"Question {entry['question_num']}", expanded=False):
                st.write(f"**Question:** {entry['question']}")
                st.write(f"**Your Answer:** {entry['answer']}")
                st.write(f"**Feedback:** {entry['feedback']}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🔄 Start New Interview", use_container_width=True):
                # Reset for new interview
                st.session_state.stage = 'job_selection'
                st.session_state.current_question_num = 1
                st.session_state.conversation_history = []
                st.session_state.current_question = None
                st.session_state.answer_submitted = False
                st.session_state.current_answer = ""
                st.session_state.current_feedback = ""
                st.rerun()
        
        with col2:
            if st.button("📄 Download Interview Report", use_container_width=True):
                # Create and download report
                st.info("📄 Report generation feature coming soon!")

if __name__ == "__main__":
    main()
