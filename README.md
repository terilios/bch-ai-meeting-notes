# BCH AI Meeting Notes Generator

An intelligent meeting minutes generator powered by Azure OpenAI and Streamlit. This application transforms meeting transcripts into well-structured, actionable documentation with automated analysis and multiple export formats.

## Features

- **Multiple Input Formats**: Support for TXT, PDF, DOCX, and MD files
- **Intelligent Processing**: Uses Azure OpenAI for content generation and analysis
- **Rich Output Formats**: Export as Markdown, DOCX, or PDF
- **Meeting Analysis**: Automated scoring across multiple dimensions:
  - Meeting Effectiveness
  - Participation & Engagement
  - Action Item Management
  - Risk Management
  - Communication Quality
- **Visual Documentation**: Automated generation of Mermaid diagrams for:
  - Process flows
  - System architectures
  - Timeline representations
  - Organization structures
  - Project dependencies

## Prerequisites

- Python 3.8+
- Pandoc (for document conversion)
- Mermaid-filter (for diagram generation)
- Azure OpenAI API access

## Environment Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/bch-ai-meeting-notes.git
cd bch-ai-meeting-notes
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Install system dependencies:

```bash
# On macOS
brew install pandoc
npm install -g mermaid-filter

# On Ubuntu/Debian
sudo apt-get install pandoc
npm install -g mermaid-filter

# On Windows
choco install pandoc
npm install -g mermaid-filter
```

5. Create a `.env` file with your Azure OpenAI credentials:

```env
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_API_VERSION=your_api_version
AZURE_OPENAI_API_BASE=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment_name
```

## Running the Application

### Local Development

```bash
streamlit run main.py
```

### Docker Deployment

1. Build the Docker image:

```bash
docker build -t bch-ai-meeting-notes .
```

2. Run the container:

```bash
docker run -p 8501:8501 --env-file .env bch-ai-meeting-notes
```

Access the application at http://localhost:8501

## Usage

1. Choose input method:
   - Upload a transcript file (TXT, PDF, DOCX, MD)
   - Paste text directly
2. Click "Generate Minutes"
3. Review the generated minutes and analysis
4. Download in your preferred format (MD, DOCX, PDF)

## Project Structure

```
bch-ai-meeting-notes/
├── main.py              # Main application file
├── schema.json          # Analysis schema definition
├── requirements.txt     # Python dependencies
├── .env                # Environment variables (not in git)
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
└── images/             # Application images
    ├── bch.png
    ├── user.png
    └── user.svg
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
