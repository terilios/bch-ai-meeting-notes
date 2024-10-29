import streamlit as st
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from pypdf import PdfReader
import docx
import markdown
from io import BytesIO
from streamlit_mermaid import st_mermaid
import re
import subprocess
import tempfile
import time
import json

# Initialize session state for storing generated documents and analysis
if 'minutes_md' not in st.session_state:
    st.session_state.minutes_md = None
if 'docx_data' not in st.session_state:
    st.session_state.docx_data = None
if 'pdf_data' not in st.session_state:
    st.session_state.pdf_data = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

# Load environment variables
load_dotenv()

# Configure Azure OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_API_BASE")
)
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

def get_analysis_schema():
    """Load the JSON schema for meeting analysis"""
    with open('schema.json', 'r') as f:
        return json.load(f)

def analyze_meeting_minutes(minutes_text):
    """Analyze meeting minutes using Azure OpenAI for quantitative scoring across multiple dimensions"""
    analysis_prompt = """You are a meeting analysis expert. Your task is to analyze meeting minutes and provide numerical scores across multiple dimensions. You must respond with a valid JSON object that matches the specified schema.

Analyze the following meeting minutes and provide scores, justifications, and evidence. Each metric should include:
- score: An integer between 0 and 100
- justification: A brief, single sentence explanation
- evidence: A specific example from the text

The response must strictly follow the schema structure without any additional properties."""

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": minutes_text}
            ],
            temperature=0.3,
            max_tokens=4000,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "meeting_analysis_schema",
                    "schema": get_analysis_schema()
                }
            }
        )
        
        try:
            # Parse the JSON response
            analysis_results = json.loads(response.choices[0].message.content)
            return analysis_results
        except json.JSONDecodeError as e:
            st.error(f"Error parsing analysis results: {str(e)}")
            return None
            
    except Exception as e:
        st.error(f"Error analyzing meeting minutes: {str(e)}")
        return None

def extract_text_from_pdf(file):
    pdf_reader = PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = docx.Document(file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def generate_meeting_minutes(text):
    system_prompt = """You are a professional meeting minutes writer who captures comprehensive meeting details with precision and clarity. Your goal is to transform meeting transcripts into well-structured, actionable documentation using summaries, hierarchical bullet points, and visual representations through mermaid diagrams where appropriate.

Given a meeting transcript, create detailed meeting minutes that include:

Meeting Overview

Date, Time, Duration, Location
Attendees and Roles
Meeting Purpose/Objectives
Previous Meeting Follow-up
Executive Summary

High-level overview of key outcomes
Critical decisions and their rationale
Major milestones discussed (using markdown table)
Detailed Discussion Points

Strategic topics
Operational matters
Technical discussions
Risk assessments
Resource considerations
Action Items (using markdown table)

Priority level (High/Medium/Low)
Owner/Responsible party
Due date
Dependencies
Success criteria
Decisions Log (using markdown table)

Decision context
Alternatives considered
Rationale
Impact assessment
Required approvals
Visual Documentation

Process flows (using mermaid flowchart)
System architectures (using mermaid flowchart)
Timeline representations (using mermaid gantt and only if specific grounding dates are identified)
Organization structures (using mermaid flowchart)
Project dependencies (using mermaid flowchart)
Next Steps (using markdown table)

Immediate actions (using markdown table)
Future considerations (using markdown table)
Open items (using markdown table)
Required follow-ups
Supporting Information

Referenced documents
Related resources
Parking lot items
Open questions

Format the output in markdown. For any diagrams, use mermaid syntax within ```mermaid code blocks. For example:

```mermaid
flowchart TD
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
```

or

```mermaid
gantt
    title Project Timeline
    dateFormat  YYYY-MM-DD
    section Phase 1
    Task 1           :2024-01-01, 30d
    Task 2           :2024-02-01, 20d
```"""
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error generating meeting minutes: {str(e)}")
        return None

def render_markdown_with_mermaid(markdown_text):
    # Split the markdown into parts based on mermaid code blocks
    parts = re.split(r'(```mermaid.*?```)', markdown_text, flags=re.DOTALL)
    
    for part in parts:
        if part.strip().startswith('```mermaid'):
            # Extract the mermaid diagram code
            mermaid_code = part.strip().replace('```mermaid', '').replace('```', '').strip()
            # Render the mermaid diagram
            st_mermaid(mermaid_code)
        else:
            # Render regular markdown
            st.markdown(part)

def convert_markdown_to_docx(markdown_content, output_path):
    """Convert markdown to DOCX using pandoc with reference template and mermaid filter"""
    reference_docx = os.path.join('resources', 'reference.docx')
    
    # Create a temporary markdown file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_md:
        temp_md.write(markdown_content)
        temp_md_path = temp_md.name
    
    try:
        # Convert markdown to docx using pandoc with reference template and mermaid filter
        subprocess.run([
            'pandoc',
            '-t', 'docx',
            '--reference-doc=' + reference_docx,
            '-F', 'mermaid-filter',
            '-o', output_path,
            temp_md_path
        ], check=True)
    finally:
        # Clean up temporary file
        os.unlink(temp_md_path)

def convert_docx_to_pdf(docx_path, pdf_path):
    """Convert DOCX to PDF using pandoc"""
    subprocess.run([
        'pandoc',
        docx_path,
        '--pdf-engine=xelatex',
        '-o', pdf_path
    ], check=True)

def display_analysis_results(analysis_results):
    """Display analysis results with charts and scores"""
    if not analysis_results:
        return

    st.markdown("## Meeting Analysis")
    
    # Create tabs for different analysis dimensions
    tabs = st.tabs([
        "Meeting Effectiveness",
        "Participation & Engagement",
        "Action Item Management",
        "Risk Management",
        "Communication Quality"
    ])
    
    dimension_mapping = {
        "Meeting Effectiveness": "meeting_effectiveness",
        "Participation & Engagement": "participation_engagement",
        "Action Item Management": "action_item_management",
        "Risk Management": "risk_management",
        "Communication Quality": "communication_quality"
    }
    
    for tab, (display_name, key_name) in zip(tabs, dimension_mapping.items()):
        with tab:
            if key_name in analysis_results:
                dimension_data = analysis_results[key_name]
                
                # Create three columns for each category
                for category, data in dimension_data.items():
                    st.markdown(f"### {category.replace('_', ' ').title()}")
                    
                    # Display score with a metric
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        st.metric(label="Score", value=f"{data['score']}/100")
                    with col2:
                        st.markdown(f"**Justification:** {data['justification']}")
                        st.markdown(f"**Evidence:** {data['evidence']}")
                    
                    # Add a separator between categories
                    st.markdown("---")
                
                # Calculate and display average score for the dimension
                scores = [data['score'] for data in dimension_data.values()]
                avg_score = sum(scores) / len(scores)
                st.metric(f"{display_name} Overall Score", f"{avg_score:.1f}/100")

def display_download_options():
    """Display download options for generated documents"""
    if st.session_state.minutes_md:
        st.markdown("### Download Options")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.download_button(
                label="Download MD",
                data=st.session_state.minutes_md,
                file_name="meeting_minutes.md",
                mime="text/markdown",
                use_container_width=True
            )
        
        with col2:
            st.download_button(
                label="Download DOCX",
                data=st.session_state.docx_data,
                file_name="meeting_minutes.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )
        
        with col3:
            st.download_button(
                label="Download PDF",
                data=st.session_state.pdf_data,
                file_name="meeting_minutes.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        
        st.markdown("---")

def main():
    # Set up the Streamlit app
    logo_path = 'images/bch.png'  # Update the path if needed

    # Display the logo at the top left of the app
    st.sidebar.image(logo_path, use_column_width=True)
    st.sidebar.title("Meeting Minutes Generator")
    st.sidebar.markdown("---")
    
    input_method = st.sidebar.radio(
        "Choose input method",
        ["Upload File", "Paste Text"],
        key="input_method"
    )
    
    transcript_text = ""
    
    if input_method == "Upload File":
        st.sidebar.info("Upload a meeting transcript file (supported formats: TXT, PDF, DOCX, MD)")
        uploaded_file = st.sidebar.file_uploader("Choose a file", type=['txt', 'pdf', 'docx', 'md'])
        
        if uploaded_file is not None:
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            try:
                if file_type == 'txt' or file_type == 'md':
                    transcript_text = uploaded_file.read().decode()
                elif file_type == 'pdf':
                    transcript_text = extract_text_from_pdf(uploaded_file)
                elif file_type == 'docx':
                    transcript_text = extract_text_from_docx(uploaded_file)
                st.sidebar.success(f"File '{uploaded_file.name}' successfully loaded!")
            except Exception as e:
                st.sidebar.error(f"Error reading file: {str(e)}")
    else:
        st.info("Paste or type your meeting transcript below")
        transcript_text = st.text_area(
            "Meeting Transcript",
            height=300,
            placeholder="Paste your meeting transcript here..."
        )
    
    if transcript_text:
        if st.sidebar.button("Generate Minutes", type="primary", use_container_width=True):
            # Create a progress container
            progress_container = st.empty()
            
            # Initialize progress bar
            progress_bar = progress_container.progress(0)
            progress_text = st.empty()
            
            # Update progress
            progress_text.text("Generating meeting minutes...")
            progress_bar.progress(10)
            
            minutes_md = generate_meeting_minutes(transcript_text)
            
            if minutes_md:
                progress_bar.progress(30)
                progress_text.text("Preparing documents...")
                
                # Create temporary directory for document conversion
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Paths for temporary files
                    temp_docx = os.path.join(temp_dir, "meeting_minutes.docx")
                    temp_pdf = os.path.join(temp_dir, "meeting_minutes.pdf")
                    
                    try:
                        progress_text.text("Converting to DOCX format...")
                        progress_bar.progress(60)
                        
                        # Convert markdown to DOCX with mermaid support
                        convert_markdown_to_docx(minutes_md, temp_docx)
                        
                        progress_text.text("Converting to PDF format...")
                        progress_bar.progress(70)
                        
                        # Convert DOCX to PDF
                        convert_docx_to_pdf(temp_docx, temp_pdf)
                        
                        progress_text.text("Analyzing meeting content...")
                        progress_bar.progress(80)
                        
                        # Analyze meeting minutes
                        analysis_results = analyze_meeting_minutes(minutes_md)
                        
                        progress_text.text("Preparing final output...")
                        progress_bar.progress(90)
                        
                        # Read the generated files for download
                        with open(temp_docx, 'rb') as docx_file, open(temp_pdf, 'rb') as pdf_file:
                            # Store generated documents in session state
                            st.session_state.minutes_md = minutes_md
                            st.session_state.docx_data = docx_file.read()
                            st.session_state.pdf_data = pdf_file.read()
                            st.session_state.analysis_results = analysis_results
                        
                        # Complete progress
                        progress_bar.progress(100)
                        progress_text.text("Processing complete!")
                        
                        # Clear progress after a short delay
                        time.sleep(1)
                        progress_container.empty()
                        progress_text.empty()
                        
                    except subprocess.CalledProcessError as e:
                        st.error(f"Error during document conversion: {str(e)}")
                        st.error("Please ensure pandoc and mermaid-filter are installed.")
                        # Clear progress on error
                        progress_container.empty()
                        progress_text.empty()
    
    # Display download options if documents are available
    display_download_options()
    
    # Display generated minutes if available
    if st.session_state.minutes_md:
        st.markdown("## Generated Meeting Minutes")
        render_markdown_with_mermaid(st.session_state.minutes_md)
        
        # Display analysis results if available
        if st.session_state.analysis_results:
            display_analysis_results(st.session_state.analysis_results)

if __name__ == "__main__":
    main()
