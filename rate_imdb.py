#!/usr/bin/env python
import sys
import argparse
import logging

import progressbar
import ucsv

import imdb
from imdb import utils, config


def rating_rows(rating_csv):
    with open(rating_csv, 'rb') as csv:
        reader = ucsv.reader(csv)
        for n, row in enumerate(reader):
            if len(row) != 3:
                raise Exception(
                "Wrong number of fields in row {0}: {1}".format(n+1, row))
            yield(row[0:3])

def main():
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description='Send ratings from rt to imdb')

    parser.add_argument('csv', help='Filename for csv output')
    parser.add_argument('--imdb-user', help='IMDb Username',
            default=imdb.config.IMDB_USERNAME)
    parser.add_argument('--imdb-pass', help='IMDb Password',
            default=imdb.config.IMDB_PASSWORD)

    args = parser.parse_args()

    # Login to imdb
    (username, password) = (args.imdb_user, args.imdb_pass)
    login_response = imdb.utils.login(username, password)
    logging.info('Logged into imdb as {0}'.format(username))

    all_films = set()
    unrated_films = set()

    # Open csv file and read it
    for row in rating_rows(args.csv):
        (film, year, rating) = row
        all_films.add((film, year, rating))
        filmid = imdb.utils.get_title_id(film, year)
        if filmid:
            # We have a match! Rate it!
            rating_response = imdb.utils.rate(filmid, rating)
        else:
            logging.warning('Film not ratable')
            unrated_films.add((film, year, rating))

    print('Rated')
    for film in all_films - unrated_films:
        print (film)
    print()
    print('Could not rate:')
    for film in unrated_films:
        print(film)

if __name__ == '__main__':
    main()
