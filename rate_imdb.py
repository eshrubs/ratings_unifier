#!/usr/bin/env python
import sys
import argparse
import logging

import progressbar
import ucsv

import imdb
from imdb import utils, config


def n_lines(filename):
    with open(filename, 'r') as f:
        return len(list(l for l in f))

def rating_rows(rating_csv):
    widgets = ['Rating: ', progressbar.Percentage(), ' ',
            progressbar.Bar(marker='|',left='[',right=']'),
            ' ', progressbar.ETA(), ' '] #see docs for other
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=n_lines(rating_csv))
    pbar.start()

    with open(rating_csv, 'rb') as csv:
        reader = ucsv.reader(csv)
        for n, row in enumerate(reader):
            logging.info('Reading row %d' % n)
            if len(row) != 3:
                raise Exception(
                "Wrong number of fields in row {0}: {1}".format(n+1, row))
            yield(row[0:3])
            pbar.update(n+1)

    pbar.end()

def main():
    logging.basicConfig(level=logging.INFO,
            filename='rate_imdb.log')
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
    rated_films = set()

    # Open csv file and read it
    for row in rating_rows(args.csv):
        (film, year, rating) = row
        all_films.add((film, year, rating))
        try:
            filmid = imdb.utils.get_title_id(film, year)
            if filmid:
                # We have a match! Rate it!
                rating_response = imdb.utils.rate(filmid, rating)
                rated_films.add((film, year, rating))
            else:
                logging.warning('Film not ratable')
        except Exception as ex:
            logging.error('Error! {0}'.format(ex))


    print('Rated:')
    for film in rated_films:
        print (film)
    print()
    print('Could not rate:')
    for film in all_films - rated_films:
        print(film)

if __name__ == '__main__':
    main()
