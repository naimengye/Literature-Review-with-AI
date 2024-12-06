# literature_expander.py
import yaml
import re
import arxiv
import os
from copilot import Copilot
import requests
from urllib.parse import urlparse
from pathlib import Path
from semanticscholar import SemanticScholar
from Bio import Entrez

class LiteratureExpander:
    def __init__(self, yaml_path):
        # Load initial configuration
        with open(yaml_path, 'r') as file:
            self.config = yaml.safe_load(file)
            print(self.config)
        
        # Ensure data directory exists
        Path('./data').mkdir(exist_ok=True)
        print("Data directory created")
        
        # Initialize OpenAI key
        self.openai_api_key = os.getenv("OPENAI_API_KEY") or self.config.get('openai_api_key')
        if not self.openai_api_key:
            self.openai_api_key = input("Please enter your OpenAI API Key: ")
        print("OpenAI API key initialized")
        
        # Initialize other API keys from config or environment
        #self.ieee_api_key = os.getenv("IEEE_API_KEY") or self.config.get('ieee_api_key')
        #self.acm_api_key = os.getenv("ACM_API_KEY") or self.config.get('acm_api_key')
        #self.semantic_scholar_api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY") or self.config.get('semantic_scholar_api_key')
        #self.pubmed_email = os.getenv("PUBMED_EMAIL") or self.config.get('pubmed_email')
    
    def extract_references(self, text):
        """Extract paper titles from GPT response"""
        # Look for titles in [brackets] as per our prompt format
        references = re.findall(r'\[(.*?)\]', text)
        # Also look for titles that might be preceded by common patterns
        patterns = [
            r'titled "([^"]*)"',
            r'paper "([^"]*)"',
            r'study "([^"]*)"'
        ]
        for pattern in patterns:
            references.extend(re.findall(pattern, text))
        return list(set(references))  # Remove duplicates
    
    def download_paper(self, title):
        """Download paper from multiple sources"""
        # Define a list of download strategies
        download_strategies = [
            self.download_paper_arxiv,
            #self.download_paper_semantic_scholar,
            #self.download_paper_ieee_xplore,
            #self.download_paper_acm_digital_library,
            #self.download_paper_pubmed
        ]
        
        for strategy in download_strategies:
            success = strategy(title)
            if success:
                return True
        print(f"Failed to download paper from all sources: {title}")
        return False
    
    def download_paper_arxiv(self, title):
        """Download paper from arXiv"""
        try:
            # Search arxiv
            search = arxiv.Search(
                query=title,
                max_results=1,
                sort_by=arxiv.SortCriterion.Relevance
            )
            
            for result in search.results():
                filename = f"./data/{result.get_short_id()}.pdf"
                if not os.path.exists(filename):
                    print(f"Downloading (arXiv): {result.title}")
                    result.download_pdf(filename=filename)
                return True

            return False
        except Exception as e:
            print(f"Error downloading from arXiv {title}: {e}")
            return False
    
    def download_paper_semantic_scholar(self, title):
        """Download paper from Semantic Scholar"""
        if not self.semantic_scholar_api_key:
            print("Semantic Scholar API key not provided.")
            return False
        scholar = SemanticScholar(api_key=self.semantic_scholar_api_key)
        try:
            # Search for the paper by title
            paper = scholar.search_paper(title)
            if paper and 'pdfUrl' in paper and paper['pdfUrl']:
                pdf_url = paper['pdfUrl']
                filename = f"./data/{paper['paperId']}.pdf"
                if not os.path.exists(filename):
                    response = requests.get(pdf_url)
                    with open(filename, 'wb') as f:
                        f.write(response.content)
                    print(f"Downloaded (Semantic Scholar): {paper['title']}")
                return True
            else:
                print(f"No PDF found on Semantic Scholar for: {title}")
                return False
        except Exception as e:
            print(f"Error downloading from Semantic Scholar {title}: {e}")
            return False
    
    def download_paper_ieee_xplore(self, title):
        """Download paper from IEEE Xplore"""
        if not self.ieee_api_key:
            print("IEEE Xplore API key not provided.")
            return False
        search_url = "https://ieeexploreapi.ieee.org/api/v1/search/articles"
        params = {
            'apikey': self.ieee_api_key,
            'format': 'json',
            'max_records': 1,
            'sort_order': 'desc',
            'sort_field': 'relevance',
            'querytext': title
        }
        try:
            response = requests.get(search_url, params=params)
            data = response.json()
            if data['totalRecords'] > 0:
                article = data['articles'][0]
                pdf_url = article.get('pdf_url', None)
                if pdf_url:
                    filename = f"./data/{article['articleNumber']}.pdf"
                    if not os.path.exists(filename):
                        pdf_response = requests.get(pdf_url)
                        with open(filename, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"Downloaded (IEEE Xplore): {article['title']}")
                    return True
            print(f"No PDF found on IEEE Xplore for: {title}")
            return False
        except Exception as e:
            print(f"Error downloading from IEEE Xplore {title}: {e}")
            return False
    
    def download_paper_acm_digital_library(self, title):
        """Download paper from ACM Digital Library"""
        if not self.acm_api_key:
            print("ACM Digital Library API key not provided.")
            return False
        search_url = "https://api.acm.org/publication/v1/articles"
        headers = {
            'Authorization': f'Bearer {self.acm_api_key}'
        }
        params = {
            'query': title,
            'count': 1,
            'sort': 'relevance'
        }
        try:
            response = requests.get(search_url, headers=headers, params=params)
            data = response.json()
            if data['totalResults'] > 0:
                article = data['results'][0]
                pdf_url = article.get('pdfUrl', None)
                if pdf_url:
                    filename = f"./data/{article['articleId']}.pdf"
                    if not os.path.exists(filename):
                        pdf_response = requests.get(pdf_url, headers=headers)
                        with open(filename, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"Downloaded (ACM): {article['title']}")
                    return True
            print(f"No PDF found on ACM for: {title}")
            return False
        except Exception as e:
            print(f"Error downloading from ACM Digital Library {title}: {e}")
            return False
    
    def download_paper_pubmed(self, title):
        """Attempt to find and access paper via PubMed"""
        if not self.pubmed_email:
            print("PubMed email not provided.")
            return False
        Entrez.email = self.pubmed_email  # Required by NCBI
        try:
            # Search for the paper by title
            handle = Entrez.esearch(db="pubmed", term=title, retmax=1)
            record = Entrez.read(handle)
            handle.close()
            if record['IdList']:
                paper_id = record['IdList'][0]
                # Fetch the paper details
                handle = Entrez.efetch(db="pubmed", id=paper_id, rettype="medline", retmode="text")
                paper = handle.read()
                handle.close()
                # Extract DOI (if available)
                doi_match = re.search(r'DOI- (\S+)', paper)
                if doi_match:
                    doi = doi_match.group(1)
                    pdf_url = f"https://doi.org/{doi}"
                    filename = f"./data/{doi.replace('/', '_')}.pdf"
                    if not os.path.exists(filename):
                        # This approach assumes the DOI link redirects to a PDF
                        pdf_response = requests.get(pdf_url)
                        with open(filename, 'wb') as f:
                            f.write(pdf_response.content)
                        print(f"Downloaded (PubMed via DOI): {title}")
                        return True
                print(f"DOI not found or PDF not directly accessible for: {title}")
                return False
            else:
                print(f"No PubMed record found for: {title}")
                return False
        except Exception as e:
            print(f"Error downloading from PubMed {title}: {e}")
            return False
    
    def analyze_and_expand(self):
        # Initialize Copilot
        copilot = Copilot()
        print("Copilot initialized")
        # Modify system prompt to ensure structured output with bracketed references
        copilot.system_prompt = """
        You are an expert at analyzing academic papers and creating literature reviews. Your task is to:
        1. Focus on the related work sections and references
        2. Identify key papers and their relationships
        3. Create a comprehensive overview of how these papers relate to each other
        4. Organize the citations into meaningful categories
        5. Highlight seminal works and their influence
        
        IMPORTANT: When mentioning paper titles, always enclose them in square brackets, like [Paper Title Here].
        
        Please structure your response with:
        - Key research themes
        - Important papers in each theme
        - How papers build upon or relate to each other
        """
        
        # Hard-coded literature review question
        question = "Please analyze these papers and create a structured literature review. Focus on how papers relate to each other and their key contributions."
        
        # Get initial analysis
        retrieved_info, answer = copilot.ask(question, messages=[], openai_key=self.openai_api_key)


        if isinstance(answer, str):
            print(answer)
        else:
            answer_str = ""
            for chunk in answer:
                content = chunk.choices[0].delta.content
                if content:
                    answer_str += content
                    print(content, end="", flush=True)
            print()
            answer = answer_str
        
        # # Process streaming response if necessary
        # if not isinstance(answer, str):
        #     answer_str = ""
        #     try:
        #         for chunk in answer:
        #             content = chunk.get('choices', [{}])[0].get('delta', {}).get('content', '')
        #             if content:
        #                 answer_str += content
        #                 print(content, end="", flush=True)
        #         print()
        #         answer = answer_str
        #     except Exception as e:
        #         print(f"Error processing streaming response: {e}")
        #         answer = ""

        
        
        print("Answer processed", answer)

        # Extract references
        references = self.extract_references(answer)
        
        # Download each referenced paper
        for title in references:
            success = self.download_paper(title)
            if not success:
                print(f"Failed to download paper: {title}")
        
        return answer
