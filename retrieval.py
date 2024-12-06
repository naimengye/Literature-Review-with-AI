# main.py

import os
from literature_expander import LiteratureExpander

def main():
    # Path to your YAML configuration
    yaml_path = 'config.yaml'
    
    # Check if config.yaml exists
    if not os.path.exists(yaml_path):
        print(f"Configuration file {yaml_path} not found. Please create it with necessary API keys.")
        return
    
    # Initialize LiteratureExpander
    literature_expander = LiteratureExpander(yaml_path)
    
    # Start the analysis and expansion process
    literature_review = literature_expander.analyze_and_expand()
    
    # Optionally, save the literature review to a file
    with open('literature_review.txt', 'w', encoding='utf-8') as f:
        f.write(literature_review)
    
    print("\nLiterature review generated and saved to 'literature_review.txt'.")

if __name__ == "__main__":
    main()
