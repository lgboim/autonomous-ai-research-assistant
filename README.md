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
   git clone https://github.com/lgboim/autonomous-ai-research-assistant.git
   cd autonomous-ai-research-assistant
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Set up your Anthropic API key:
   - Sign up for an Anthropic API key at https://www.anthropic.com
   - Replace `'YOUR_ANTHROPIC_API_KEY'` in the `main.py` file with your actual API key

## Usage

Run the main script:

```
python main.py
```

The script will perform multiple iterations of searching for papers, analyzing them, updating the research state, and generating new research directions.

## Configuration

You can adjust the following parameters in `main.py`:

- `num_iterations`: Number of search-analyze cycles (default is 5)
- `papers_per_iteration`: Number of papers to analyze in each iteration (default is 3)

## How It Works

1. The script starts with an initial research state.
2. It generates a search query based on the current research state.
3. It searches arXiv for relevant papers using the generated query.
4. For each selected paper:
   - It extracts the PDF content.
   - It uses Claude AI to analyze the paper and generate insights.
   - It updates the research state based on the analysis.
5. After analyzing papers, it generates new research directions.
6. This process repeats for the specified number of iterations.
7. Finally, it evaluates the overall progress made during the research process.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for research and educational purposes only. Always respect the terms of service of the APIs and services used. Be mindful of rate limits and usage restrictions for both arXiv and the Anthropic API.
