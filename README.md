# Adobe Challenge 1B: Intelligent PDF Document Analysis System

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 🚀 Overview

An advanced AI-powered PDF document analysis system that processes multiple document collections and extracts contextually relevant content based on specific personas and use cases. The system leverages cutting-edge NLP techniques, fuzzy logic, and semantic analysis to provide intelligent document insights.

## 📂 Project Structure

```
adobe-1b/
├── 📄 main.py                      # Main processing engine
├── 📄 pdf_parser.py                # PDF content extraction
├── 📄 extract_outline_ultra_precise.py  # Advanced outline extraction
├── 📄 semanticAnalyzer.py          # AI-powered semantic analysis
├── 📄 requirements.txt             # Python dependencies
├── 🐳 Dockerfile                   # Docker container configuration
├── 📄 entrypoint.sh               # Docker entrypoint script
├── 📄 download_models.sh          # AI model download script
├── 📁 Collection 1/               # Travel Planning Dataset
│   ├── 📁 PDFs/                   # South of France travel guides (7 documents)
│   ├── 📄 challenge1b_input.json  # Input configuration
│   └── 📄 challenge1b_output.json # Analysis results
├── 📁 Collection 2/               # Adobe Acrobat Learning Dataset
│   ├── 📁 PDFs/                   # Acrobat tutorials (15 documents)
│   ├── 📄 challenge1b_input.json  # Input configuration
│   └── 📄 challenge1b_output.json # Analysis results
├── 📁 Collection 3/               # Recipe Collection Dataset
│   ├── 📁 PDFs/                   # Cooking guides (9 documents)
│   ├── 📄 challenge1b_input.json  # Input configuration
│   └── 📄 challenge1b_output.json # Analysis results
└── 📁 output/                     # Generated analysis results
```


## 🐳 Docker Setup & Usage

### Prerequisites
- Docker Desktop installed and running
- 8GB RAM available
- 15GB free disk space

### Quick Start

#### 1. Build the Image
```powershell
docker build -t adobe-pdf-analyzer .
```

#### 2. Run the Analysis
```powershell
# Process all collections
docker run --rm -v "$(pwd)/output:/app/output" adobe-pdf-analyzer

# Process specific collection
docker run --rm -v "$(pwd)/output:/app/output" adobe-pdf-analyzer --base-dir "/app/Collection 1"
```

### Common Commands

**Process Individual Collections:**
```powershell
# Travel Planning (Collection 1)
docker run --rm -v "$(pwd)/output:/app/output" adobe-pdf-analyzer --base-dir "/app/Collection 1"

# Adobe Acrobat (Collection 2)  
docker run --rm -v "$(pwd)/output:/app/output" adobe-pdf-analyzer --base-dir "/app/Collection 2"

# Recipe Collection (Collection 3)
docker run --rm -v "$(pwd)/output:/app/output" adobe-pdf-analyzer --base-dir "/app/Collection 3"
```

**Debug Mode:**
```powershell
# Run with detailed logging
docker run --rm -v "$(pwd)/output:/app/output" adobe-pdf-analyzer --verbose
```

### Management

**View Results:**
```powershell
# Check output files
ls output/
```

**Clean Up:**
```powershell
# Remove the image
docker rmi adobe-pdf-analyzer
```

## 💻 Local Development Setup

### Installation
```powershell
# Clone and setup
git clone https://github.com/Ayush-Vish/adobe-1b.git
cd adobe-1b

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Download Models
```powershell
# Download AI models (requires bash/WSL)
bash download_models.sh
```

### Run Processing
```powershell
# Process all collections
python main.py

# Process specific collection
python main.py --base-dir "Collection 1"
```

## 🚀 Usage Examples

### Basic Commands
```powershell
# Docker - Process all collections
docker run --rm -v "$(pwd)/output:/app/output" adobe-pdf-analyzer

# Local - Process all collections  
python main.py

# Process specific collection
python main.py --base-dir "Collection 1"
```

### Output
Results are saved in `output/` directory:
- `challenge1b_output_round_1b_001.json` - Collection 3 results
- `challenge1b_output_round_1b_002.json` - Collection 1 results  
- `challenge1b_output_round_1b_003.json` - Collection 2 results
- `processing_report.json` - Summary report

## 📊 System Requirements

- **RAM**: 8GB minimum
- **Storage**: 15GB free space
- **CPU**: 4 cores recommended
- **OS**: Windows 10/11, macOS, or Linux

## 🔍 Troubleshooting

### Common Issues

**Out of Memory:**
```powershell
# Use low memory mode
docker run --rm --memory="4g" -v "$(pwd)/output:/app/output" adobe-pdf-analyzer
```

**Model Download Failed:**
```powershell
# Re-download models
rm -rf models/
bash download_models.sh
```

**Slow Processing:**
```powershell
# Process one collection at a time
python main.py --base-dir "Collection 1"
```

## 📈 Performance Metrics

- **Collection 1** (7 PDFs): ~3-5 minutes
- **Collection 2** (15 PDFs): ~6-10 minutes  
- **Collection 3** (9 PDFs): ~4-7 minutes
- **All Collections**: ~15-25 minutes

## 🤖 Technology Stack

- **Python 3.10+** with PyTorch (CPU-optimized)
- **SentenceTransformers** for semantic analysis
- **TinyLLaMA** for content generation
- **PyMuPDF** for PDF processing
- **Fuzzy Logic** for content classification

## 📋 Input/Output Format

### Input JSON Structure
```json
{
  "challenge_info": {
    "challenge_id": "round_1b_XXX",
    "test_case_name": "specific_test_case",
    "description": "Challenge description"
  },
  "documents": [
    {
      "filename": "document.pdf",
      "title": "Document Title"
    }
  ],
  "persona": {
    "role": "User Persona",
    "description": "Detailed persona description"
  },
  "job_to_be_done": {
    "task": "Specific task description",
    "context": "Additional context"
  }
}
```

### Output JSON Structure
```json
{
  "metadata": {
    "input_documents": ["list_of_processed_files"],
    "persona": "User Persona",
    "job_to_be_done": "Task description",
    "processing_time": "timestamp",
    "total_sections": 25
  },
  "extracted_sections": [
    {
      "document": "source.pdf",
      "section_title": "Section Title",
      "importance_rank": 1,
      "page_number": 5,
      "confidence_score": 0.95
    }
  ],
  "subsection_analysis": [
    {
      "document": "source.pdf",
      "section_title": "Parent Section",
      "refined_text": "AI-generated relevant content summary",
      "page_number": 5,
      "relevance_score": 0.87
    }
  ]
}
```

## 🔧 Advanced Features

### Fuzzy Logic Document Analysis
- **Font Size Analysis (25%)**: Gaussian membership functions
- **Length Optimization (20%)**: Trapezoidal membership for word counts
- **Pattern Matching (25%)**: Regex-based structural recognition
- **Semantic Analysis (15%)**: Context-aware classification
- **Typography Analysis (10%)**: Font style detection
- **Position Analysis (5%)**: Spatial positioning heuristics
- **Whitespace Analysis (10%)**: Layout-based separation

### Multi-threaded Processing
- **Adaptive Worker Scaling**: Based on CPU cores and available memory
- **Resource Management**: Automatic garbage collection and memory optimization
- **Error Recovery**: Graceful degradation with detailed error reporting
- **Thread Safety**: Lock-based coordination for concurrent processing

### Content Ranking Algorithm
1. **Semantic Similarity**: Vector-based content matching to persona/task
2. **Structural Importance**: Heading hierarchy and document position
3. **Content Quality**: Length, completeness, and information density
4. **Contextual Relevance**: Domain-specific keyword matching

## 🛠️ Development

### Project Dependencies
```text
# Core PDF Processing
PyMuPDF>=1.23.0
pdfminer.six>=20220524

# AI/ML Stack  
torch>=2.0.0
transformers>=4.30.0
sentence-transformers>=2.2.0
ctransformers>=0.2.0

# Data Processing
numpy>=1.24.0
scipy>=1.10.0
scikit-learn>=1.3.0
Pillow>=9.5.0

# Utilities
psutil>=5.9.0
networkx>=3.1
jinja2>=3.1.0
```

### Code Structure
```
src/
├── main.py                     # Main orchestrator
├── pdf_parser.py              # PDF content extraction
├── extract_outline_ultra_precise.py  # Advanced outline detection
├── semanticAnalyzer.py        # AI-powered analysis
└── utils/
    ├── fuzzy_logic.py         # Fuzzy membership functions
    ├── resource_manager.py    # System resource monitoring
    └── logging_config.py      # Centralized logging setup
```

### Testing
```powershell
# Run basic functionality test
python -c "
import main
processor = main.RobustPDFProcessor(max_workers=1)
print('✅ Core components loaded successfully')
"

# Test individual collection
python main.py --base-dir "Collection 1" --output-dir test_output --verbose
```

## 📞 Support & Troubleshooting

### Getting Help
1. **Check Logs**: Review `pdf_processing.log` for detailed error information
2. **System Resources**: Ensure adequate RAM and disk space
3. **Model Downloads**: Verify all AI models downloaded correctly
4. **Permissions**: Ensure write access to output directory

### Common Error Solutions

**Error: "CUDA out of memory"**
```powershell
# Force CPU-only processing
$env:CUDA_VISIBLE_DEVICES = ""
python main.py --max-workers 1
```

**Error: "Model not found"**
```powershell
# Re-download models
Remove-Item -Recurse -Force models/
bash download_models.sh
```

**Error: "Permission denied"**
```powershell
# Fix Windows permissions
icacls output /grant Everyone:(OI)(CI)F
```

### Performance Optimization

**For Large Document Sets:**
```powershell
# Increase memory allocation
docker run --memory="12g" --cpus="4" adobe-pdf-analyzer

# Process collections separately
python main.py --base-dir "Collection 1" --max-workers 2
```

**For Limited Resources:**
```powershell
# Minimal resource usage
python main.py --max-workers 1 --base-dir "Collection 1"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Contact

- **Repository**: [adobe-1b](https://github.com/Ayush-Vish/adobe-1b)
- **Issues**: [GitHub Issues](https://github.com/Ayush-Vish/adobe-1b/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Ayush-Vish/adobe-1b/discussions)

---

**🚀 Happy Processing!** This system demonstrates the power of AI-driven document analysis for real-world use cases. The combination of fuzzy logic, semantic analysis, and multi-threaded processing delivers robust, scalable PDF content extraction tailored to specific personas and objectives.
 