import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import re

# API endpoint
url = "https://wikimedia.org/api/rest_v1/feed/availability"

# Headers to include
headers = {
    "accept": 'application/json; charset=utf-8; profile="https://www.mediawiki.org/wiki/Specs/Availability/1.0.1"',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
}

# function to fetch metadata using the MediaWiki API
def fetch_metadata(title):


    url = f"http://en.wikipedia.org/w/api.php?action=query&prop=imageinfo&iiprop=extmetadata&titles=File%3a{title}&format=json"


    response = requests.get(url)
    data = response.json()
    
    page = next(iter(data['query']['pages'].values()))

    author_html = page['imageinfo'][0]['extmetadata'].get('Artist', {}).get('value', 'N/A')

    # Check if the author name is in HTML format
    if '<a ' in author_html:
        # Using regex to extract the name from the HTML
        author_name_match = re.search(r'>(.*?)<', author_html)
        if author_name_match:
            author = author_name_match.group(1)  # Extract the name without HTML tags
        else:
            author = 'N/A'
    else:
        author = author_html
    
    
    metadata = {
        'description': page['imageinfo'][0]['extmetadata'].get('ImageDescription', {}).get('value', 'N/A'),
        'creation_date': page['imageinfo'][0]['extmetadata'].get('DateTime', {}).get('value', 'N/A'),
        'author': author,
        'license': page['imageinfo'][0]['extmetadata'].get('LicenseShortName', {}).get('value', 'N/A'),

    }
    return metadata

# Get the data
response = requests.get(url, headers=headers)

# On successful response
if response.status_code == 200:
    data = response.json()  # Get JSON data from response
    
    # Extract the list of pages with "todays_featured_article"
    todays_featured_article = data.get("todays_featured_article", [])
    # print(len(todays_featured_article))
    
    # Find the English Wikipedia URL
    if "en.wikipedia.org" in todays_featured_article:
        # Make url for English Wikipedia
        english_wikipedia_url = "https://en.wikipedia.org/wiki/Main_Page"
        
        # get HTML content
        response = requests.get(english_wikipedia_url, headers=headers)
        
        if response.status_code == 200:
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the featured article section 
            featured_article_section = soup.find("div", {"id": "mp-tfa"})  
            
            if featured_article_section:
                # Extract the title and summary of the featured article
                featured_article_title = featured_article_section.find('b').get_text(strip=True)
                featured_article_summary = featured_article_section.get_text()
                featured_article_summary = ' '.join(featured_article_summary.split())
                
                # get date of featured article
                now = datetime.now()
                current_date = now.date()
                current_date_str = current_date.strftime("%d-%m-%Y")
                
                # Get link for the featured article              
                article_link_tag = featured_article_section.find('a', href=True)
                if article_link_tag:
                    article_link = article_link_tag['href']
                    article_url = "https://en.wikipedia.org" + article_link
                    article_response = requests.get(article_url, headers=headers)
                    
                    if article_response.status_code == 200:
                        # Parse the article page
                        article_soup = BeautifulSoup(article_response.text, 'html.parser')
                        
                        # Find the heading of the article (usually in <h1> tag)
                        heading = article_soup.find("h1").get_text(strip=True)
                        heading = heading[5:]
                        # Get metadata of the main image
                        metadata = fetch_metadata(heading)
                        
                    else:
                        print(f"Failed to retrieve the article page. Status code: {article_response.status_code}")

                
                # Store the information in a dictionary
                featured_article_data = {
                    "title": featured_article_title,
                    "summary": featured_article_summary,
                    "date of feature": current_date_str,
                    "title of main image": heading,
                    "metadata of main image": metadata
                }
                
                # Save the featured article data to a JSON file
                with open("featured_article.json", "w") as json_file:
                    json.dump(featured_article_data, json_file, indent=4)
                
                print("English Wikipedia featured article has been successfully saved to featured_article.json")
            else:
                print("Featured article section not found on the English Wikipedia main page.")
        else:
            print(f"Failed to retrieve English Wikipedia main page. Status code: {response.status_code}")
    else:
        print("English Wikipedia is not available in 'todays_featured_article' list.")
else:
    print(f"Failed to retrieve data. Status code: {response.status_code}")
