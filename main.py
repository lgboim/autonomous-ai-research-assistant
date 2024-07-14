import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
import time
import json
import urllib.parse
import re
from PyPDF2 import PdfReader
import tempfile
import io

# Replace with your actual Anthropic API key
ANTHROPIC_API_KEY = 'your-key-here'

def extract_json_from_text(text):
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        return json_match.group(0)
    return None

def clean_json_string(json_str):
    json_str = ''.join(ch for ch in json_str if ord(ch) >= 32)
    json_str = json_str.encode('ascii', 'backslashreplace').decode('ascii')
    return json_str

def simplify_query(query):
    simplified = re.sub(r'["\(\)]', '', query)
    simplified = re.sub(r'\s+(AND|OR)\s+', ' ', simplified)
    simplified = re.sub(r'\d{4}', '', simplified)
    words = simplified.split()
    return ' '.join(words[:min(4, len(words))])

def search_arxiv(query, max_results=200, retries=3):
    base_url = "https://arxiv.org/search/"
    params = {
        "searchtype": "all",
        "query": query,
        "abstracts": "show",
        "size": str(max_results),
        "order": "-announced_date_first"
    }
    url = base_url + "?" + urllib.parse.urlencode(params)
    
    for attempt in range(retries):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        papers = []
        for result in soup.find_all('li', class_='arxiv-result'):
            title_elem = result.find('p', class_='title')
            authors_elem = result.find('p', class_='authors')
            abstract_elem = result.find('span', class_='abstract-full')
            pdf_link_elem = result.find('a', string='pdf')
            
            if title_elem and authors_elem and abstract_elem and pdf_link_elem:
                pdf_link = pdf_link_elem['href']
                if not pdf_link.startswith('http'):
                    pdf_link = 'https://arxiv.org' + pdf_link
                paper = {
                    'title': title_elem.text.strip(),
                    'authors': authors_elem.text.replace('Authors:', '').strip(),
                    'abstract': abstract_elem.text.strip(),
                    'pdf_link': pdf_link
                }
                papers.append(paper)
        
        if papers:
            return papers
        elif attempt < retries - 1:
            print(f"No papers found. Simplifying query for attempt {attempt + 2}...")
            query = simplify_query(query)
            params['query'] = query
            url = base_url + "?" + urllib.parse.urlencode(params)
        else:
            print("No papers found after all attempts. Please check the search query.")
    
    return []

def extract_pdf_content(pdf_url):
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()
        
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file.seek(0)
            
            try:
                pdf_reader = PdfReader(temp_file.name)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text[:50000]  # Limit to first 50000 characters
            except Exception as e:
                return f"Error extracting PDF content: {str(e)}"
    except requests.RequestException as e:
        return f"Error downloading PDF: {str(e)}"

def analyze_paper_with_claude(client, paper, pdf_content, research_state):
    prompt = f"""
    You are an advanced AI researcher at the forefront of AI development. Your goal is to push the boundaries of AI and make groundbreaking discoveries. Analyze the following AI research paper in the context of our ongoing research:

    Title: {paper['title']}
    Authors: {paper['authors']}
    Abstract: {paper['abstract']}
    PDF Content (first 50000 characters): {pdf_content}

    Current Research State:
    {json.dumps(research_state, indent=2)}

    Please provide:
    1. A concise summary of the paper's main contributions.
    2. Identification of any potentially groundbreaking ideas or techniques.
    3. Critical analysis: What are the strengths and limitations of this approach?
    4. Synthesis: How does this work connect with or challenge our current understanding?
    5. Novel hypotheses: Generate 2-3 new, testable hypotheses inspired by this paper.
    6. Potential breakthroughs: Identify areas where this work could lead to significant advancements.
    7. Cross-disciplinary insights: Are there connections to other fields that could yield new perspectives?

    Format your response as a JSON object with the following keys:
    "summary", "groundbreaking_ideas", "critical_analysis", "synthesis", "novel_hypotheses", "potential_breakthroughs", "cross_disciplinary_insights"
    
    Ensure your response is a valid JSON object, starting with '{{' and ending with '}}'.
    Avoid using any control characters or non-UTF-8 characters in your response.
    """

    try:
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = response.content[0].text
        json_str = extract_json_from_text(response_text)
        if json_str:
            try:
                analysis = json.loads(json_str)
                return analysis
            except json.JSONDecodeError as e:
                cleaned_json_str = clean_json_string(json_str)
                try:
                    analysis = json.loads(cleaned_json_str)
                    return analysis
                except json.JSONDecodeError:
                    print(f"Failed to parse Claude's response as JSON. Falling back to text extraction.")
                    return extract_information_from_text(response_text)
        else:
            print("Failed to extract JSON from Claude's response. Falling back to text extraction.")
            return extract_information_from_text(response_text)
    except Exception as e:
        return {"error": f"Error analyzing paper: {str(e)}"}

def extract_information_from_text(text):
    sections = [
        "summary", "groundbreaking_ideas", "critical_analysis", "synthesis",
        "novel_hypotheses", "potential_breakthroughs", "cross_disciplinary_insights"
    ]
    extracted_info = {}

    for i, section in enumerate(sections):
        pattern = rf"{section}:?(.*?)(?={sections[i+1]}|$)" if i < len(sections) - 1 else rf"{section}:?(.*)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Convert list-like text to actual lists
            if '\n-' in content:
                content = [item.strip('- ') for item in content.split('\n-') if item.strip()]
            extracted_info[section] = content
        else:
            extracted_info[section] = "No information provided."

    return extracted_info

def generate_search_query(client, research_state, previous_queries):
    prompt = f"""
    Based on our current research state and previous queries:
    Current Research State: {json.dumps(research_state, indent=2)}
    Previous Queries: {json.dumps(previous_queries, indent=2)}

    Generate a refined search query for arXiv that will help us find papers most relevant to our current focus and knowledge gaps.
    The query should be a string of keywords and phrases. You can use AND/OR operators, but keep it relatively simple.
    Avoid using quotation marks or parentheses. Focus on the most important 3-4 concepts.
    Consider the effectiveness of previous queries and adjust accordingly.
    Do not include any explanation, just provide the query string.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=100,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text.strip()
    except Exception as e:
        print(f"Error generating search query: {str(e)}")
        return "artificial intelligence AND recent advancements"  # Fallback query

def update_research_state(client, research_state, paper_analysis):
    prompt = f"""
    As an advanced AI researcher, update our research state based on the latest paper analysis:

    Current Research State:
    {json.dumps(research_state, indent=2)}

    Latest Paper Analysis:
    {json.dumps(paper_analysis, indent=2)}

    Please provide an updated research state that:
    1. Integrates new insights and refines our understanding of key AI concepts.
    2. Updates our hypotheses and theoretical frameworks.
    3. Identifies emerging trends or shifts in AI research directions.
    4. Highlights potential breakthroughs or revolutionary ideas.
    5. Refines our research focus and strategic direction.
    6. Identifies any new knowledge gaps or areas requiring further investigation.

    Format your response as a JSON object representing the new research state, maintaining the structure of the current state but updating its contents.
    Ensure your response is a valid JSON object, starting with '{{' and ending with '}}'.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = response.content[0].text
        json_str = extract_json_from_text(response_text)
        if json_str:
            return json.loads(json_str)
        else:
            print("Failed to extract JSON from Claude's response for research state update.")
            return {"error": "Failed to extract JSON from response"}
    except Exception as e:
        return {"error": f"Error updating research state: {str(e)}"}

def generate_research_directions(client, research_state):
    prompt = f"""
    As a pioneering AI researcher, analyze our current research state:
    {json.dumps(research_state, indent=2)}

    Based on this, please:
    1. Identify 3-5 most promising areas for potential breakthroughs.
    2. Formulate 2-3 bold, testable hypotheses that could lead to significant advancements.
    3. Suggest 1-2 unconventional approaches or experiments that could yield novel insights.
    4. Identify any emerging patterns or trends across our analyzed papers that might indicate a shift in the field.
    5. Propose a concrete next step or experiment to pursue based on our current findings.

    Format your response as a JSON object with the following keys:
    "promising_areas", "bold_hypotheses", "unconventional_approaches", "emerging_trends", "next_step"
    
    Ensure your response is a valid JSON object, starting with '{{' and ending with '}}'.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = response.content[0].text
        json_str = extract_json_from_text(response_text)
        if json_str:
            return json.loads(json_str)
        else:
            print("Failed to extract JSON from Claude's response for research directions.")
            return {"error": "Failed to extract JSON from response"}
    except Exception as e:
        return {"error": f"Error generating research directions: {str(e)}"}

def evaluate_progress(client, initial_state, current_state):
    prompt = f"""
    As an AI research evaluator, assess the progress made in our research:

    Initial Research State:
    {json.dumps(initial_state, indent=2)}

    Current Research State:
    {json.dumps(current_state, indent=2)}

    Please provide:
    1. A summary of key advancements and insights gained.
    2. An evaluation of how well we've addressed our initial knowledge gaps.
    3. Identification of any pivotal discoveries or potential breakthroughs.
    4. An assessment of the overall direction and focus of our research.
    5. Recommendations for areas that require further investigation or refinement.

    Format your response as a JSON object with the following keys:
    "advancements", "gap_assessment", "pivotal_discoveries", "direction_assessment", "recommendations"
    
    Ensure your response is a valid JSON object, starting with '{{' and ending with '}}'.
    """

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        response_text = response.content[0].text
        json_str = extract_json_from_text(response_text)
        if json_str:
            return json.loads(json_str)
        else:
            print("Failed to extract JSON from Claude's response for progress evaluation.")
            return {"error": "Failed to extract JSON from response"}
    except Exception as e:
        return {"error": f"Error evaluating progress: {str(e)}"}

def main():
    print("Initiating Comprehensive Autonomous AI Research Process")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    initial_research_state = {
        "current_focus": "Identifying cutting-edge advancements and potential breakthroughs in AI",
        "key_concepts": [],
        "emerging_theories": [],
        "potential_breakthroughs": [],
        "knowledge_gaps": ["Comprehensive understanding of latest AI paradigms"],
        "research_direction": "Explore recent AI papers to uncover revolutionary ideas and formulate novel hypotheses"
    }

    research_state = initial_research_state.copy()
    analyzed_papers = set()  # Keep track of analyzed papers
    previous_queries = []  # Keep track of previous search queries

    num_iterations = 5  # Number of search-analyze cycles
    papers_per_iteration = 3  # Number of papers to analyze in each iteration

    for iteration in range(num_iterations):
        print(f"\nIteration {iteration + 1}/{num_iterations}")

        # Generate search query
        search_query = generate_search_query(client, research_state, previous_queries)
        previous_queries.append(search_query)
        print(f"Generated search query: {search_query}")

        # Search arXiv
        papers = search_arxiv(search_query, max_results=200)
        print(f"Found {len(papers)} papers")

        # Filter out already analyzed papers
        new_papers = [p for p in papers if p['title'] not in analyzed_papers]

        # Analyze top papers
        for i in range(min(papers_per_iteration, len(new_papers))):
            paper = new_papers[i]
            print(f"\nAnalyzing paper {i + 1}/{min(papers_per_iteration, len(new_papers))}:")
            print(f"Title: {paper['title']}")
            analyzed_papers.add(paper['title'])  # Mark this paper as analyzed

            pdf_content = extract_pdf_content(paper['pdf_link'])
            analysis = analyze_paper_with_claude(client, paper, pdf_content, research_state)

            if "error" in analysis:
                print(f"Error in paper analysis: {analysis['error']}")
                continue

            print("\nKey Insights and Potential Breakthroughs:")
            for idea in analysis.get('groundbreaking_ideas', []):
                if isinstance(idea, str):
                    print(f"- {idea}")
                elif isinstance(idea, list):
                    for sub_idea in idea:
                        print(f"- {sub_idea}")
            
            print("\nNovel Hypotheses Generated:")
            for hypothesis in analysis.get('novel_hypotheses', []):
                if isinstance(hypothesis, str):
                    print(f"- {hypothesis}")
                elif isinstance(hypothesis, list):
                    for sub_hypothesis in hypothesis:
                        print(f"- {sub_hypothesis}")

            new_research_state = update_research_state(client, research_state, analysis)
            if "error" in new_research_state:
                print(f"Error occurred while updating research state: {new_research_state['error']}")
                print("Continuing with previous research state.")
            else:
                research_state = new_research_state

        print("\nUpdated Research Focus:")
        print(research_state.get('current_focus', 'No focus available'))

        # Generate new research directions
        print("\nGenerating New Research Directions...")
        new_directions = generate_research_directions(client, research_state)
        if "error" not in new_directions:
            print("\nPromising Areas for Breakthroughs:")
            for area in new_directions.get('promising_areas', []):
                print(f"- {area}")
            print("\nBold New Hypotheses:")
            for hypothesis in new_directions.get('bold_hypotheses', []):
                print(f"- {hypothesis}")
            print("\nNext Step:")
            print(new_directions.get('next_step', 'No next step provided'))
        else:
            print(f"Error generating new research directions: {new_directions['error']}")

        time.sleep(5)

    print("\nComprehensive Autonomous AI Research Process Completed")
    print("\nEvaluating Overall Progress...")
    progress_evaluation = evaluate_progress(client, initial_research_state, research_state)
    if "error" not in progress_evaluation:
        print("\nKey Advancements:")
        for advancement in progress_evaluation.get('advancements', []):
            print(f"- {advancement}")
        print("\nPivotal Discoveries:")
        for discovery in progress_evaluation.get('pivotal_discoveries', []):
            print(f"- {discovery}")
        print("\nRecommendations for Further Research:")
        for recommendation in progress_evaluation.get('recommendations', []):
            print(f"- {recommendation}")
    else:
        print(f"Error evaluating progress: {progress_evaluation['error']}")

    print("\nFinal Research State and Potential Breakthroughs:")
    print(json.dumps(research_state, indent=2))

if __name__ == "__main__":
    main()
