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

def parse_rt_csv(rt_csv_filename):
    with open(rt_csv_filename, 'rb') as csv:
        reader = ucsv.reader(csv)
        for n, row in enumerate(reader):
            logging.info('Reading row %d' % n)
            if len(row) != 3:
                raise Exception(
                "Wrong number of fields in row {0}: {1}".format(n+1, row))
            yield tuple(row[0:3])

def parse_imdb_csv(csv_filename):
    with open(csv_filename, 'rb') as csv:
        reader = ucsv.DictReader(csv)
        for n, row in enumerate(reader):
            yield (row['Title'], row['Year'], row['You rated'])

def main():
    logging.basicConfig(level=logging.INFO,
            filename='rate_imdb.log')
    parser = argparse.ArgumentParser(description='Send ratings from rt to imdb')

    parser.add_argument('--rt-csv', help='RottenTomatoes csv. Generate using '
                        './rt_dump.py')
    parser.add_argument('--imdb-csv', help='Imdb Csv Link. Download from IMDb')
    parser.add_argument('--imdb-user', help='IMDb Username',
                        default=imdb.config.IMDB_USERNAME)
    parser.add_argument('--imdb-pass', help='IMDb Password',
                        default=imdb.config.IMDB_PASSWORD)

    parser.add_argument('--rated-csv', default=None)
    parser.add_argument('--unrated-csv', default=None)

    args = parser.parse_args()

    # Login to imdb
    (username, password) = (args.imdb_user, args.imdb_pass)
    login_response = imdb.utils.login(username, password)
    logging.info('Logged into imdb as {0}'.format(username))

    rated_films = set()

    imdb_rated_films = set(parse_imdb_csv(args.imdb_csv))
    rt_rated_films = set(parse_rt_csv(args.rt_csv))

    to_rate = rt_rated_films - imdb_rated_films

    widgets = ['Rating: ', progressbar.Percentage(), ' ',
            progressbar.Bar(marker='|',left='[',right=']'),
            ' ', progressbar.ETA(), ' '] #see docs for other
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=len(to_rate))
    pbar.start()

    # Open csv file and read it
    for n, (film, year, rating) in enumerate(to_rate):
        to_rate.add((film, year, rating))
        pbar.update(n+1)

        try:
            filmid = imdb.utils.get_title_id(film, year)
            if filmid:
                # We have a match! Rate it!
                rating_response = imdb.utils.rate(filmid, rating)
                rated_films.add((film, year, rating))
            else:
                logging.warning('Film not ratable')
        except Exception as ex:
            logging.error('{0}'.format(ex))

    pbar.finish()


    print('Rated:')
    for film in rated_films:
        print (film)
    print()
    print('Could not rate:')
    for film in to_rate - rated_films:
        print(film)

if __name__ == '__main__':
    main()
