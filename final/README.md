# VTU Study Assistant - AI-Powered Textbook RAG System

A comprehensive AI-powered study assistant for VTU students that provides intelligent Q&A capabilities using uploaded textbooks, with support for both text and image content.

## 🚀 Features

### Core Functionality
- **Intelligent Q&A**: Ask questions about any subject and get AI-generated answers based on textbook content
- **Multi-Modal Support**: Handles both text and images from textbooks
- **Subject-Specific Filtering**: Automatically filters responses based on selected subject
- **Source Citations**: Every answer includes proper citations with book titles and page numbers
- **Image Retrieval**: Can find and display relevant diagrams, charts, and images from textbooks

### Admin Panel
- **PDF Upload**: Upload textbooks with drag-and-drop interface
- **Batch Operations**: Upload multiple files at once
- **Data Management**: View, search, and delete uploaded content
- **Health Monitoring**: Check system status and data statistics

### Student Interface
- **Modern UI**: Clean, aesthetic interface designed for college students
- **Subject Navigation**: Easy switching between subjects (Machine Learning, Deep Learning, Cryptography)
- **Chat Interface**: Interactive Q&A with conversation history
- **PDF Library**: Browse and download uploaded textbooks
- **Responsive Design**: Works on desktop and mobile devices

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
- **Vector Database**: ChromaDB (local, persistent)
- **Embeddings**: Sentence Transformers (text) + CLIP (images)
- **LLM**: OpenRouter API (Claude 3 Haiku)
- **Frontend**: HTML, CSS, JavaScript (Vanilla)
- **PDF Processing**: PyMuPDF

### Project Structure
```
final/
├── configs/
│   └── config.yaml          # Configuration settings
├── data/
│   ├── raw/                 # Original PDF files
│   └── processed/           # Extracted images and processed data
├── scripts/
│   ├── setup.ps1           # Environment setup script
│   ├── run_admin.ps1       # Admin panel launcher
│   └── run_student_ui.ps1  # Student UI launcher
├── src/
│   ├── admin/              # Admin panel backend and frontend
│   ├── student_ui/         # Student interface backend and frontend
│   ├── embeddings/         # Text and image embedding modules
│   ├── extract/            # PDF extraction and processing
│   ├── chunking/           # Text chunking utilities
│   ├── store/              # Vector database operations
│   ├── rag/                # RAG system implementation
│   ├── pipeline/           # Data ingestion pipeline
│   └── utils/              # Utility functions
├── storage/
│   └── vector/             # ChromaDB persistent storage
└── requirements.txt        # Python dependencies
```

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.11** (required for PyMuPDF compatibility)
- **PowerShell** (for Windows scripts)
- **OpenRouter API Key** (free tier available)

### Step 1: Environment Setup
1. **Clone or download** the project to your local machine
2. **Open PowerShell** in the project directory
3. **Run the setup script**:
   ```powershell
   .\scripts\setup.ps1
   ```
   This will:
   - Create a Python virtual environment
   - Install all required dependencies
   - Download embedding models

### Step 2: Configuration
1. **Get an OpenRouter API Key**:
   - Visit [OpenRouter.ai](https://openrouter.ai)
   - Sign up for a free account
   - Generate an API key

2. **Update the configuration**:
   - Open `configs/config.yaml`
   - Replace `your_openrouter_api_key_here` with your actual API key
   - Optionally adjust other settings (model, chunk size, etc.)

### Step 3: Launch the System

#### Option A: Using PowerShell Scripts (Recommended)
1. **Start Admin Panel**:
   ```powershell
   .\scripts\run_admin.ps1
   ```
   - Admin panel will be available at: `http://localhost:8001`

2. **Start Student Interface** (in a new PowerShell window):
   ```powershell
   .\scripts\run_student_ui.ps1
   ```
   - Student interface will be available at: `http://localhost:8002`

#### Option B: Manual Launch
1. **Activate virtual environment**:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```

2. **Start Admin Panel**:
   ```powershell
   cd final
   python -m uvicorn src.admin.app:app --host 0.0.0.0 --port 8001
   ```

3. **Start Student Interface** (in new terminal):
   ```powershell
   cd final
   python -m uvicorn src.student_ui.app:app --host 0.0.0.0 --port 8002
   ```

## 📚 Usage Guide

### Admin Panel (http://localhost:8001)

#### Uploading Textbooks
1. **Access the admin panel** at `http://localhost:8001`
2. **Upload PDFs**:
   - Use the "Upload PDF" section
   - Enter the admin token: `qwertyui12345678asdfghjklmnbvcxz0987654321`
   - Select subject, semester, and book title
   - Drag and drop PDF files or click to browse
   - Click "Upload" to process the files

3. **Batch Upload** (for multiple files):
   - Use the "Batch Upload" section
   - Upload multiple PDFs at once
   - System will automatically extract text and images

#### Managing Data
- **View Uploaded Files**: Check the "List Files" section
- **Search Content**: Use the search functionality to find specific content
- **Delete Files**: Use the delete section to remove unwanted files
- **System Health**: Check statistics and system status

### Student Interface (http://localhost:8002)

#### Getting Started
1. **Access the student interface** at `http://localhost:8002`
2. **Select a Subject**:
   - Click on "Machine Learning", "Deep Learning", or "Cryptography"
   - This sets the context for your questions

#### Using the Chat
1. **Ask Questions**:
   - Type your question in the chat input
   - Press Enter or click the send button
   - Get AI-generated answers based on textbook content

2. **View Sources**:
   - Every answer includes source citations
   - See which book and page the information came from
   - Click on image sources to view diagrams

3. **Browse PDFs**:
   - Switch to the "PDFs" tab
   - View all available textbooks for the selected subject
   - Download PDFs for offline study

## 🎯 Supported Subjects

Currently configured for **Semester 7** with three subjects:

| Subject Code | Display Name | Description |
|--------------|--------------|-------------|
| `ml` | Machine Learning | Machine learning algorithms and concepts |
| `dl` | Deep Learning | Neural networks and deep learning |
| `crytography` | Cryptography | Information security and cryptography |

## 🔧 Configuration Options

### configs/config.yaml
```yaml
# LLM Settings
llm:
  api_key: "your_openrouter_api_key_here"
  model: "anthropic/claude-3-haiku"
  max_tokens: 1500
  temperature: 0.7

# Chunking Settings
chunking:
  chunk_size: 1000
  chunk_overlap: 200

# Storage Settings
storage:
  chroma_path: "storage/vector"

# Admin Settings
admin:
  token: "qwertyui12345678asdfghjklmnbvcxz0987654321"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. PyMuPDF DLL Error
**Problem**: `ImportError: DLL load failed`
**Solution**: 
- Ensure you're using Python 3.11
- Delete `.venv` folder and run setup script again
- Install Microsoft Visual C++ Redistributable

#### 2. Port Already in Use
**Problem**: `Address already in use`
**Solution**:
- Kill existing processes: `taskkill /f /im python.exe`
- Use different ports in the scripts
- Check if other applications are using ports 8001/8002

#### 3. API Key Issues
**Problem**: LLM responses failing
**Solution**:
- Verify your OpenRouter API key is correct
- Check your OpenRouter account has sufficient credits
- Ensure internet connection is stable

#### 4. No Sources in Responses
**Problem**: Sources showing as "None"
**Solution**:
- Ensure PDFs are properly uploaded and processed
- Check that subject names match exactly
- Verify vector store has data using the check script

### Debug Tools

#### Check Vector Store Data
```powershell
python check_data.py
```

#### Test RAG System
```powershell
python test_rag.py
```

## 📊 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11, macOS, or Linux
- **RAM**: 4GB (8GB recommended)
- **Storage**: 2GB free space
- **Python**: 3.11.x
- **Internet**: Required for LLM API calls

### Recommended Requirements
- **RAM**: 8GB or more
- **Storage**: 5GB free space
- **GPU**: Optional (for faster embedding generation)

## 🔒 Security Notes

- **Admin Token**: Change the default admin token in production
- **API Keys**: Never commit API keys to version control
- **File Uploads**: Admin panel accepts PDF files only
- **Local Storage**: All data is stored locally on your machine

## 🚀 Future Enhancements

### Planned Features
- **Multi-Semester Support**: Add support for other semesters
- **User Authentication**: Individual student accounts
- **Progress Tracking**: Track study progress and quiz results
- **Mobile App**: Native mobile application
- **Offline Mode**: Local LLM support for offline use
- **Collaborative Features**: Study groups and shared notes

### Contributing
This project is designed for VTU students. To contribute:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in the terminal
3. Ensure all prerequisites are met
4. Verify configuration settings

## 📄 License

This project is developed for educational purposes at VTU. Please respect the academic integrity guidelines when using this system.

---

**Happy Studying! 🎓**

*Built with ❤️ for VTU Students*
