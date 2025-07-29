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

    # Header
    st.title("🎯 InterviewAI - Smart Interview Preparation")
    st.subheader("AI-Powered Mock Interviews with Real Company Questions")

    # Stage 1: Job Selection
    if st.session_state.stage == 'job_selection':
        st.header("🎯 Select Your Target Job")
        
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
        st.header("📄 Upload Your Resume")
        
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
        st.header("📊 Preparation Analysis Complete")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("📋 Resume Analysis")
            with st.expander("View Detailed Resume Analysis", expanded=True):
                st.write(st.session_state.resume_analysis)
        
        with col2:
            st.subheader("❓ Researched Interview Questions")
            with st.expander("View Company Interview Intelligence", expanded=True):
                st.write(st.session_state.interview_questions)
        
        st.header("🎤 Ready to Start Mock Interview")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🎯 Start Mock Interview", use_container_width=True):
                st.session_state.stage = 'interview'
                st.rerun()

    # Stage 4: Interview Conduct
    elif st.session_state.stage == 'interview':
        st.header(f"🎤 Mock Interview: {st.session_state.selected_job} at {st.session_state.company_name}")
        
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
                    
                    # Store conversation
                    st.session_state.conversation_history.append({
                        'question_num': st.session_state.current_question_num,
                        'question': st.session_state.current_question,
                        'answer': answer,
                        'feedback': feedback
                    })
                    
                    # Show feedback
                    st.success("✅ Answer submitted!")
                    with st.expander("📝 Feedback on Your Answer", expanded=True):
                        st.write(feedback)
                    
                    # Move to next question
                    if st.session_state.current_question_num < 10:
                        if st.button("➡️ Next Question"):
                            st.session_state.current_question_num += 1
                            st.session_state.current_question = None
                            st.rerun()
                    else:
                        if st.button("🏁 Finish Interview"):
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
        st.header("🎉 Interview Complete!")
        st.balloons()
        
        st.subheader("📊 Interview Summary")
        
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
                st.rerun()
        
        with col2:
            if st.button("📄 Download Interview Report", use_container_width=True):
                # Create and download report
                st.info("📄 Report generation feature coming soon!")

if __name__ == "__main__":
    main()
