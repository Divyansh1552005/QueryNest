"""
This file : 
- Website URL se main readable content nikalna
- Boilerplate (nav, ads, footer) remove karna
- LangChain Document object return karna

THis loader:
- Single URL
- Ya multiple URLs (list) handle kar sakta hai
"""

from typing import Iterable, Union
import requests
from readability import Document as ReadabilityDocument
from bs4 import BeautifulSoup

from langchain_core.documents import Document


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
    cleaned_text = "\n".join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )

    return cleaned_text


# loading a single web page
def load_web_page(url: str) -> Document:

    response = requests.get(
        url,
        timeout=10,
        headers={
            "User-Agent": "QueryNest/1.0"
        },
    )

    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch page ({response.status_code})")

    text = _extract_clean_text(response.text)

    if not text:
        raise RuntimeError("No readable content found on page")

    return Document(
        page_content=text,
        metadata={
            "source": url,
            "type": "web",
        },
    )


# if user gives multiple web pages (generator style using yield func) returns iterable of document objects
def load_web_pages(urls: Union[str, list[str]]) -> Iterable[Document]:

    if isinstance(urls, str):
        urls = [urls]

    for url in urls:
        yield load_web_page(url)
