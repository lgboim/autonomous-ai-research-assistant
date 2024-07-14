# Autonomous AI Research Assistant

This project implements an autonomous AI research assistant that searches for, analyzes, and synthesizes information from recent AI research papers. It uses the arXiv API to find papers and leverages the Anthropic Claude API for in-depth analysis and research direction generation.

## Features

- Automated arXiv paper search based on dynamically generated queries
- PDF content extraction from arXiv papers
- In-depth paper analysis using Claude AI
- Dynamic research state updates
- Generation of new research directions and hypotheses
- Progress evaluation and research focus refinement

## Requirements

- Python 3.7+
- `requests`
- `beautifulsoup4`
- `anthropic`
- `PyPDF2`

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/autonomous-ai-research-assistant.git
   cd autonomous-ai-research-assistant
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Anthropic API key:
   - Sign up for an Anthropic API key at https://www.anthropic.com
   - Replace `'YOUR_ANTHROPIC_API_KEY'` in the code with your actual API key

## Usage

Run the main script:

```
python main.py
```

The script will perform multiple iterations of searching for papers, analyzing them, updating the research state, and generating new research directions.

## Code Structure

- `main.py`: The main script that orchestrates the entire research process
- `arxiv_search.py`: Functions for searching arXiv and extracting paper information
- `pdf_extraction.py`: Functions for extracting text content from PDF files
- `claude_analysis.py`: Functions for interacting with the Claude API and analyzing papers
- `research_state.py`: Functions for managing and updating the research state
- `utils.py`: Utility functions for JSON handling and text processing

## Configuration

You can adjust the following parameters in `main.py`:

- `num_iterations`: Number of search-analyze cycles
- `papers_per_iteration`: Number of papers to analyze in each iteration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for research and educational purposes only. Always respect the terms of service of the APIs and services used.
