# -*- coding: utf-8 -*-

import sys
import os
import json
import re
import logging
import time
import itertools
from base64 import b64encode

import urllib
import urllib2
import cookielib

from bs4 import BeautifulSoup

cookiejar = cookielib.LWPCookieJar()
url_opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookiejar))
url_opener.add_header = [('User-Agent',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 '
'Fedora/3.0.1-1.fc9 Firefox/3.0.1'),
('Accept-Language', 'en-US,en;q=0.8,en-CA;q=0.6')]

IMDB_THROTTLE = 2 # second
last_time_sent = 0
def open_url(request):
    global last_time_sent
    now = time.time()
    diff = now - last_time_sent
    if diff < IMDB_THROTTLE:
        logging.info('Throttling...')
        time.sleep(IMDB_THROTTLE - diff)
    last_time_sent = time.time()
    try:
        return url_opener.open(request)
    except Exception as ex:
        logging.error('Got an error. Retrying in 10 seconds: %s' % ex)
        time.sleep(10)
        return open_url(request)

def login(login, password):
    # Use mobile login because it actually works
    url = 'https://secure.imdb.com/oauth/m_login?origpath=/'
    values = {
        # '49e6c': 'cad9',
        'login': login,
        'password': password,
    }

    try:
        data = urllib.urlencode(values)
        request = urllib2.Request(url, data)
        response = open_url(request)
        return response
    except urllib2.HTTPError, ex:
        logging.error('Request failed: %d, %s', ex.code, response_data)
        raise


def search(query):
    encoded_query = urllib.urlencode({
        'q': query.encode('utf-8'),
        's': 'all',
        })
    url = 'http://www.imdb.com/find?{0}'.format(encoded_query)

    request = urllib2.Request(url)
    logging.info('Searching: %s' % url)
    response = open_url(request)
    response_data = response.read()
    return response_data

def unstrict_year_match(top_year, movie_year):
    if abs(movie_year - top_year) <= 1:
        logging.info('Year is only 1 different. Assume ok.')
        return True
    return False

def unstrict_title_match(top_title, movie_title):
    # Remove periods, commas and 3d
    remove_crap_re = (r'\.|,|(?:3[dD])')
    top_title = re.sub(remove_crap_re, '', top_title.lower())
    movie_title = re.sub(remove_crap_re, '', movie_title.lower())
    logging.info('Clean top = %s' % top_title)
    logging.info('Clean movie = %s' % movie_title)

    bracketed_titles_re = (r'\(([^\)]+)\)')
    top_brackets = re.findall(bracketed_titles_re, top_title)
    logging.info('TopGroups = %s' % top_brackets)
    movie_brackets = re.findall(bracketed_titles_re, movie_title)
    logging.info('MovieGroups = %s' % movie_brackets)

    unbracked_titles_re = r'\A([^\(]+)(?:\W\(|\Z)'
    top_non_brackets = re.findall(unbracked_titles_re, top_title)
    logging.info('TopGroups = %s' % top_non_brackets)
    movie_non_brackets = re.findall(unbracked_titles_re, movie_title)
    logging.info('MovieGroups = %s' % movie_non_brackets)

    for t, m in itertools.product(
            itertools.chain(top_brackets, top_non_brackets),
            itertools.chain(movie_brackets, movie_non_brackets)):
        if t == m:
            logging.info('Sub-titles %s = %s', t, m)
            return True
    return False

def match(top_title, top_year, movie_title, movie_year, strict=False):
    if not movie_year:
        return False
    if not top_title.lower() == movie_title.lower():
        logging.warning('%s does not match %s exactly' %
                        (top_title, movie_title))
        if strict:
            return False
        elif not unstrict_title_match(top_title, movie_title):
            return False
    if movie_year and not movie_year == top_year:
        logging.warning('Years for movie %s does not match (%d, %d)' %
                        (top_title, movie_year, top_year))
        if strict:
            return False
        elif not unstrict_year_match(top_year, movie_year):
            return False

    return True

def try_get_search_page(movie, year=None):
    html = search("%s %s" % (movie, year))
    soup = BeautifulSoup(html)

    find_list = soup.find('table', attrs={'class', 'findList'})
    if not find_list:
        logging.error('Search page for {0} invalid'.format(
            movie.encode('utf-8')))
        with open('{0}.html'.format(b64encode(movie.encode('utf-8'))), 'w') as f:
            f.write(soup.prettify().encode('utf-8')),
        return None
    top = find_list.find('td', attrs={'class', 'result_text'})

    top_a = top.find('a')

    td_string = top.get_text().strip()
    top_title, top_year = re.match(r'(.+) \((\d+)\)', td_string).groups()
    top_year = int(top_year)

    if not match(top_title, top_year, movie, year, False):
        return None

    return top_a['href']


def get_title_id(movie, year):
    link = try_get_search_page(movie, year)
    if link:
        title_id = re.match(r'/title/(.+)/', link).group(1)
        if not title_id:
            logging.error('Link was not in a good format: {0}'.format(link))
            return None
        return title_id
    return None

def get_title_page(movie_id):
    url = "http://www.imdb.com/title/{0}".format(movie_id)
    logging.info('Loading title page: %s' % url)
    request = urllib2.Request(url)
    response = open_url(request)
    return response

def get_rating_params(movie_id, new_rating):
    html = get_title_page(movie_id).read()
    soup = BeautifulSoup(html)

    rating_div = soup.find('div', attrs={'class', 'rating'})

    auth = rating_div['data-auth']

    idlist = rating_div['id'].split('|')
    tconst = idlist[0]
    tracking_tag = idlist[-1]

    return {'tconst': tconst,
            'rating': new_rating,
            'auth': auth,
            'tracking_tag': tracking_tag
            }

def rate(movie_id, rating):
    url = 'http://www.imdb.com/ratings/_ajax/title'

    rating_params = get_rating_params(movie_id, rating)
    data = urllib.urlencode(rating_params)
    request = urllib2.Request(url, data)
    logging.info('Posting ratings to %s' % url)
    response = open_url(request)
    response_data = response.read()
    return response_data

