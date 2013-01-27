# -*- coding: utf-8 -*-

import sys
import os
import json
import re
import logging

import urllib
import urllib2
import cookielib

from bs4 import BeautifulSoup

cookiejar = cookielib.LWPCookieJar()
url_opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookiejar))
url_opener.add_header = [('User-Agent',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]


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
        response = url_opener.open(request)
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
    response = url_opener.open(request)
    response_data = response.read()
    return response_data


def try_get_search_page(movie, year=None):
    html = search("%s %s" % (movie, year))
    soup = BeautifulSoup(html)

    find_list = soup.find('table', attrs={'class', 'findList'})
    top = find_list.find('td', attrs={'class', 'result_text'})

    top_a = top.find('a')

    td_string = top.get_text().strip()
    top_title, top_year = re.match(r'(.+) \((\d+)\)', td_string).groups()
    top_year = int(top_year)

    if not top_title.lower() == movie.lower():
        logging.warning('%s does not match %s exactly' % (top_title, movie))
        return None
    elif year and not year == top_year:
        logging.warning('Years for movie %s does not match (%d, %d)' %
                (top_title, year, top_year))
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
    response = url_opener.open(request)
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
    response = url_opener.open(request)
    response_data = response.read()
    return response_data

