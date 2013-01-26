# -*- coding: utf-8 -*-

import sys
import os
import json
import re

import urllib
import urllib2
import cookielib

from bs4 import BeautifulSoup

cookiejar = cookielib.CookieJar()
url_opener = urllib2.build_opener(
        urllib2.HTTPCookieProcessor(cookiejar))
url_opener.add_header = [('User-Agent', 'ratings-unifier/1')]


def login(login, password):
    url = "https://secure.imdb.com/oauth/login"
    values = {
        'login': login,
        'password': password,
    }

    try:
        data = urllib.urlencode(values)
        request = urllib2.Request(url, data)
        response = url_opener.open(request)
        response_data = response.read()
    except urllib2.HTTPError, ex:
        sys.stderr.write('Request failed: %d, %s', ex.code, response_data)
        raise


def search(query):
    encoded_query = urllib.urlencode({
        'q': query.encode('utf-8'),
        's': 'all',
        })
    url = 'http://www.imdb.com/find?{0}'.format(encoded_query)

    sys.stderr.write('%s\n' % url)
    request = urllib2.Request(url)
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

    sys.stderr.write('%s, %d\n' % (top_title, top_year))

    if not top_title.lower() == movie.lower():
        sys.stderr.write('%s does not match %s exactly\n' % (top_title, movie))
    elif year and not year == top_year:
        sys.strerr.write('Years for movie %s does not match (%d, %d)\n' %
                (top_title, year, top_year))

    return top_a['href']


def rate(movie_id, rating):
    url = 'http://www.imdb.com/ratings/_ajax'
    values = {
        'tconst': movie_id,
        'csrf': 'f04f',
        'rating': rating,
        'auth': [c.value for c in cookiejar if c.name == 'uu'][0]
    }

    data = urllib.urlencode(values)
    request = urllib2.Request(url, data)
    response = url_opener.open(request)
    response_data = response.read()

