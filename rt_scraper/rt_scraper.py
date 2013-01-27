import os
import re
import urllib
import logging

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
        logging.info('Fetched {0} from cache'.format(url))
        with open(cache_filename, 'r') as f:
            html = f.read()
    else:
        logging.info('Fetching {0} from RT'.format(url))
        html = urllib.urlopen(url).read()
        logging.info('Caching {0} from into {1}'.format(url, cache_filename))
        with open(cache_filename, 'w') as f:
            f.write(BeautifulSoup(html).prettify().encode('utf-8'))

    return html

def clean_title(title):
    """Titles come with escaped quotes. Remove the slash
    """
    return re.sub(r"\\(.)", r"\1", title)

def parse_page(html):
    """Parses a page for the title, year and rating.
    Prints the tuple to stdout
    """
    soup = BeautifulSoup(html)

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

        logging.info('Found rating tuple: {0}'.format((movie, year, score)))

        yield((movie, year, score))

def get_n_pages(html):
    soup = BeautifulSoup(html)

    top_ul = soup.body.ul
    pages = int(top_ul['pages'])
    return pages

def get_total_number_user_rating_pages(user_id):
    html = get_rottentomatoes_html(user_id, 1)
    return get_n_pages(html)

