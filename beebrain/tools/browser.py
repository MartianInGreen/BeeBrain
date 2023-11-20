import requests, json, time, os, html, urllib.parse, re
from bs4 import BeautifulSoup

from common import get_api_keys

### ----------------------------------------------------------------------
### functions
### ----------------------------------------------------------------------

def get_api_key():
    api_keys = get_api_keys()
    return api_keys["brave-search"]

def remove_html_tags(text):
        """Remove html tags from a string"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)

def quick_search(query: str, country="DE", search_lang="en", test=False, count=5): 
    encoded_query = urllib.parse.quote(query)

    if count > 20:
        count = 20
    elif count < 3:
        count = 3

    url = f"https://api.search.brave.com/res/v1/web/search?q={encoded_query}&results_filter=web&country={country}&search_lang={search_lang}&extra_snippets=true&count={count}"
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": str(get_api_key())
    }

    if test==False:
        print ("Fetching results for the query: '" + encoded_query + "'.")
        start_time = time.time()
        response = requests.get(url, headers=headers)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Request took {elapsed_time} seconds.")
        data = response.json()
        print ("Got " + str(len(data["web"]["results"])) + " results for the query: '" + encoded_query + "' in " + str(elapsed_time) + " seconds.")
        #with open("raw.json", "w") as f:
        #    json.dump(data, f)
    elif test==True:
        # load json from search_results.json
        print("Loading test data from search_results.json")
        with open("raw.json", "r") as f:
            data = json.load(f)

    def decode_data(data):
        results = []

        # get number of entrys under "web"/"results"
        length = len(data["web"]["results"])

        i = 0
        while i < length:
            url = data["web"]["results"][i]["profile"]["url"]

            deep_results = []
            # if "deep_results" in data["web"]["results"][i]:
            #     deep_results_length = len(data["web"]["results"][i]["deep_results"]["buttons"])
            #     print(deep_results_length)
            #     i_deep_results = 0
            #     while i_deep_results < deep_results_length:
            #         deep_results.append({
            #             "title": data["web"]["results"][i]["deep_results"]["buttons"][i_deep_results]["title"],
            #             "snippets": data["web"]["results"][i]["extra_snippets"][i_deep_results],
            #         })
            #         i_deep_results += 1
            # else:
            try: 
                extra_snippets_length = len(data["web"]["results"][i]["extra_snippets"])
                i_deep_results = 0
                while i_deep_results < extra_snippets_length:
                    to_append_result = data["web"]["results"][i]["extra_snippets"][i_deep_results]
                    to_append_result = remove_html_tags(to_append_result)
                    deep_results.append({
                        "snippets": to_append_result,
                    })
                    i_deep_results += 1
                
                description = data["web"]["results"][i]["description"]
                description = remove_html_tags(description)

                results.append({
                    "description": description,
                    "url": url,
                    "deep_results": deep_results
                })
            except:
                description = data["web"]["results"][i]["description"]
                description = remove_html_tags(description)
                results.append({
                    "description": description,
                    "url": url,
                })

            # increment i
            i += 1
        
        return results

    results = decode_data(data)

    #with open("parsed.json", "w") as f:
    #    json.dump(results, f)

    return results          

def copilot(query: str, depth: int):
    results = quick_search(query)

    urls = []
    for result in results:
        urls.append(result["url"])

    url_length = len(urls)
    if depth > url_length:
        depth = url_length
    
    i = 0
    websites = []
    while i < depth:
        url = urls[i]
        print("Scraping " + url + "...")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        data = soup.get_text()
        data = html.unescape(data)

        lines = data.strip().split("\n")
        lines = [line.strip() for line in lines if line.strip() != '']

        text = ""
        for line in lines:
            text += line + "\n"

        websites.append({
            "url": url,
            "text": [text]
        })
        
        i += 1
    
    return websites

def scrape_url(url: str):
    print("Scraping " + url + "...")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    data = soup.get_text()
    data = html.unescape(data)

    lines = data.strip().split("\n")
    lines = [line.strip() for line in lines if line.strip() != '']

    text = ""
    for line in lines:
        text += line + "\n"
    
    return text

if __name__ == "__main__":
    response = quick_search("tallest building in the world")
    print(response)
    with open("response.json", "w") as f:
        json.dump(response, f)