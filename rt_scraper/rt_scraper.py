import sys
import os
import re
import urllib
import errno

from bs4 import BeautifulSoup

SCORE_RE = re.compile(r'score(\d\d)')
YEAR_RE = re.compile(r'\((\d+)\)')

def get_url_filename(i):
    """Returns the cache file name
    """
    return "cache/rt_url%d.html" % i


def get_rottentomatoes_html(user_id, page_num):
    """Gets the html from cache or from the http url
    """
    url = "https://www.rottentomatoes.com/user/id/%s/" \
            "ratings?profileUserId=%s&sortby=" \
            "ratingDate&pageNum=%s" % (user_id, user_id, page_num)

    cache_filename = get_url_filename(page_num)

    html = None
    if os.path.exists(cache_filename):
        with open(cache_filename, 'r') as f:
            html = f.read()
    else:
        html = urllib.urlopen(url).read()
        with open(cache_filename, 'w') as f:
            f.write(BeautifulSoup(html).prettify().encode('utf-8'))

    return html


def clean_title(title):
    """Titles come with escaped quotes. Remove the slash
    """
    return re.sub(r"\\(.)", r"\1", title)


def parse_page(soup, outfile=sys.stdout):
    """Parses a page for the title, year and rating.
    Prints the tuple to stdout
    """
    if not isinstance(soup, BeautifulSoup):
        soup = BeautifulSoup(soup)

    for media_block in soup.find_all('li', attrs={'class', 'media_block'}):
        media_block_image = media_block.find_next('a',
                attrs={'class', 'media_block_image'})

        # Movie title
        movie = media_block_image['title']
        movie = clean_title(movie)

        # Year
        media_block_content = media_block.find('div',
                attrs={'class', 'media_block_content'})
        year_span = media_block_content.find('h3').span
        year = int(re.match(YEAR_RE, year_span.string.strip()).group(1))

        # Get the score
        score = re.match(SCORE_RE,
                media_block.find('span',
                    attrs={'class': SCORE_RE})['class'][3]
                ).group(1)
        score = int(score) / 5

        outfile.write((u"%s,%d,%s\n" % (movie, year, score)).encode('utf-8'))

def parse_first_page(soup, outfile=sys.stdout):
    """Preforms a parse on the first page.
    Returns the total number of pages
    """

    if not isinstance(soup, BeautifulSoup):
        soup = BeautifulSoup(soup)

    top_ul = soup.body.ul
    pages = int(top_ul['pages'])

    parse_page(soup, outfile=outfile)
    return pages


def scrape(user_id, outfile=sys.stdout):
    # Create cache dir if it doesn't exist
    try:
        os.mkdir('cache')
    except OSError:
        if OSError.errno == errno.EEXIST:
            pass

    html = get_rottentomatoes_html(user_id, 1)
    n_pages = parse_first_page(html, outfile)

    for page_num in range(2, n_pages+1):
        html = get_rottentomatoes_html(user_id, page_num)
        parse_page(html, outfile)

