"""
This file :
- Website URL se main readable content nikalna
- Boilerplate (nav, ads, footer) remove karna
- LangChain Document object return karna

THis loader:
- Single URL
- Ya multiple URLs (list) handle kar sakta hai
"""

import sys
from typing import Iterable, Union

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from readability import Document as ReadabilityDocument


def _extract_clean_text(html: str) -> str:
    """
    Raw HTML se sirf readable text nikalta hai
    (internal helper function)
    """

    # Readability main article HTML extract karta hai
    doc = ReadabilityDocument(html)
    article_html = doc.summary()

    # BeautifulSoup se text clean
    soup = BeautifulSoup(article_html, "lxml")

    # Unwanted tags hata do
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Extra empty lines clean krdo
    cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return cleaned_text


# loading a single web page
def load_web_page(url: str) -> Document:
    """
    Fetches and extracts clean text from a web page.
    Exits with clear error message if fetching fails.
    """

    try:
        print(f"Fetching: {url}")

        response = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "QueryNest/1.0"},
        )

        if response.status_code != 200:
            print("\nError: Failed to fetch website")
            print(f"URL: {url}")
            print(f"Status Code: {response.status_code}")
            print("\nPossible reasons:")
            print("- Website is down or unreachable")
            print("- Invalid URL")
            print("- Website blocks automated requests")
            print("\nPlease check the URL and try again.")
            print("Exiting...\n")
            sys.exit(1)

        text = _extract_clean_text(response.text)

        if not text:
            print("\n❌ Error: No readable content found")
            print(f"URL: {url}")
            print("\nThe page might be:")
            print("- Empty or only contains images/videos")
            print("- Requiring JavaScript to load content")
            print("- Behind a login/paywall")
            print("\nPlease try a different URL.")
            print("Exiting...\n")
            sys.exit(1)

        print(f"Successfully fetched: {url}")

        return Document(
            page_content=text,
            metadata={
                "source": url,
                "type": "web",
            },
        )

    except requests.exceptions.Timeout:
        print("\nError: Request timed out")
        print(f"URL: {url}")
        print("\nThe website took too long to respond (>10 seconds).")
        print("Please check your internet connection or try a different URL.")
        print("Exiting...\n")
        sys.exit(1)

    except requests.exceptions.ConnectionError:
        print("\nError: Connection failed")
        print(f"URL: {url}")
        print("\nCannot connect to the website.")
        print("Please check:")
        print("- Your internet connection")
        print("- The URL is correct and accessible")
        print("- The website is not blocking your requests")
        print("Exiting...\n")
        sys.exit(1)

    except requests.exceptions.InvalidURL:
        print("\nError: Invalid URL format")
        print(f"URL: {url}")
        print("\nPlease provide a valid URL.")
        print("Example: https://example.com")
        print("Exiting...\n")
        sys.exit(1)

    except requests.exceptions.RequestException as e:
        print("\nError: Failed to fetch website")
        print(f"URL: {url}")
        print(f"Error: {str(e)}")
        print("\nPlease check the URL and try again.")
        print("Exiting...\n")
        sys.exit(1)

    except Exception as e:
        print("\nError: Unexpected error while processing website")
        print(f"URL: {url}")
        print(f"Error: {str(e)}")
        print("\nPlease try again or contact support.")
        print("Exiting...\n")
        sys.exit(1)


# if user gives multiple web pages (generator style using yield func) returns iterable of document objects
def load_web_pages(urls: Union[str, list[str]]) -> Iterable[Document]:
    """
    Loads multiple web pages.
    Exits if any page fails to load.
    """

    if isinstance(urls, str):
        urls = [urls]

    print(f"\nFetching {len(urls)} web page(s)...\n")

    for url in urls:
        yield load_web_page(url)

    print(f"\nSuccessfully fetched all {len(urls)} web page(s)\n")
