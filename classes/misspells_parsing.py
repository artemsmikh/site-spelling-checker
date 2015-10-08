from bs4 import BeautifulSoup, SoupStrainer
from urllib2 import urlopen, URLError
from urlparse import urlparse
import re


class PageWithMisspells:
    def __init__(self):
        self.url = None
        self.title = None
        self.misspells = dict()
        self.links = set()


def parse(url):
    print "PARSE " + url
    try:
        content = urlopen(url)
    except URLError, ex:
        return None

    soup = BeautifulSoup(content, "lxml")

    page = PageWithMisspells()
    page.url = url
    page.title = soup.title.string
    page.misspells = __get_words(soup)
    page.links = __get_internal_links(soup, url)

    return page


def __get_words(soup):
    # kill all unnecessary elements
    for script in soup(["script", "style", "[document]", "head", "title", "meta"]):
        script.extract()    # rip it out

    # get content
    content = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in content.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    content = '\n'.join(chunk for chunk in chunks if chunk)
    content = content.encode('utf-8')

    # split text blob into words excluding all that isn't a word
    words = []
    for word in re.findall(r"[A-Za-z]+", content):
        if len(word) > 1:
            words.append(word.lower())

    words_with_misspells = dict()
    for word in words:
        # TODO: Check words spelling

        if word not in words_with_misspells:
            words_with_misspells[word] = 1
        else:
            words_with_misspells[word] += 1

    return words_with_misspells


def __get_internal_links(soup, current_url):
    parts = urlparse(current_url)
    scheme = parts.scheme
    netloc = parts.netloc
    page_links = set()
    try:
        for link in [h.get('href') for h in soup.find_all('a')]:
            # Skip broken urls and urls that links on current page
            if not link or link.startswith("#"):
                continue

            final_link = link
            if not link.startswith('http'):
                # Correct relational links
                if link.startswith('/'):
                    final_link = scheme + '://' + netloc + link
                else:
                    final_link = current_url + link
            else:
                # Check if link is internal
                domain = netloc
                if domain.startswith("www"):
                    domain = domain[3:]

                if domain not in urlparse(final_link).netloc:
                    # Skip external links
                    continue

            # Check if link is already added
            page_links.add(final_link)

    except Exception, ex:  # Magnificent exception handling
        print ex

    return page_links
