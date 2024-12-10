import json
import pandas as pd
import os

def extract_organizations(author_group):
    organizations = []
    
    # Handle cases where author-group is a dictionary or a list
    if isinstance(author_group, dict):  # Single author group
        author_group = [author_group]  # Convert to a list for consistent processing
    
    for group in author_group:  # Now always iterate as a list
        affiliation = group.get("affiliation", {})
        organization = affiliation.get("organization")
        
        # Check if organization is a list
        if isinstance(organization, list):
            # Get the last organization in the list
            last_org = organization[-1].get("$")
        elif isinstance(organization, dict):
            # Single organization in dict format
            last_org = organization.get("$")
        else:
            last_org = None

        if last_org:
            organizations.append(last_org)
    return organizations

def is_relevant_abstract(abstract, keywords):
    if not abstract:
        return False
    
    # Check if any keyword is in the abstract (case-insensitive)
    abstract_text = json.dumps(abstract).lower()  # Convert to string and lowercase for search
    return any(keyword in abstract_text for keyword in keywords)

def extract_all(base_folder, output_csv):
    # List to hold extracted data
    extracted_data = []
    keywords = ["carbon emission", "co2 emissions", "greenhouse gases", 
                "carbon footprint", "climate change", "decarbonization", "carbon neutrality"]
    
    # Walk through all subdirectories and files
    for root, _, files in os.walk(base_folder):
        for filename in files:
            if filename.endswith('.json'):  # Process only JSON files
                file_path = os.path.join(root, filename)
                print(f"Processing file: {file_path}")
                
                # Open and load each JSON file
                with open(file_path, 'r', encoding='utf-8') as file:
                    try:
                        data = json.load(file)
                        
                        # Extract specific fields
                        response = data.get("abstracts-retrieval-response", {})
                        item = response.get("item", {})
                        publication_year = (
                            item.get("ait:process-info", {})
                            .get("ait:date-delivered", {})
                            .get("@year")
                        )
                        record_head = item.get("bibrecord", {}).get("head", {})
                        author_group = record_head.get("author-group")
                        organizations = extract_organizations(author_group)
                        abstracts = record_head.get("abstracts")
                        title = record_head.get("citation-title")
                        
                        # Check abstract relevance
                        if is_relevant_abstract(abstracts, keywords):
                            extracted_data.append({
                                "Filename": os.path.relpath(file_path, base_folder),
                                "Title": title,
                                "Organizations": organizations[0],
                                "Publication Year": publication_year,
                                "Abstracts": abstracts
                            })
                    except json.JSONDecodeError:
                        print(f"Error decoding JSON in file: {file_path}")
    
    # Convert to DataFrame and save as CSV
    df = pd.DataFrame(extracted_data)
    df.to_csv(output_csv, index=False, encoding='utf-8')
    print(f"Data saved to {output_csv}")

# Run the extraction for the entire base folder and save to CSV
extract_all('Data2018-2023\\Project', 'filtered_data.csv')
