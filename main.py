#!/usr/bin/env python
import os
import sys
import argparse
import logging
import errno

import progressbar
import ucsv

from rt_scraper import config, rt_scraper

def scrape_rt(rt_user_id):
    widgets = ['RT: ', progressbar.Percentage(), ' ',
            progressbar.Bar(marker='|',left='[',right=']'),
            ' ', progressbar.ETA(), ' '] #see docs for other

    n_pages = rt_scraper.get_total_number_user_rating_pages(rt_user_id)

    pbar = progressbar.ProgressBar(widgets=widgets, maxval=n_pages)
    pbar.start()


    for page_num in range(1, n_pages+1):
        html = rt_scraper.get_rottentomatoes_html(rt_user_id, page_num)
        for result in rt_scraper.parse_page(html):
             yield result
        pbar.update(page_num)


def write_rt_ratings_to_csv(csv_output, rt_user_id):
    with open(csv_output, 'w') as f:
        writer = ucsv.writer(f)
        for n, row in enumerate(scrape_rt(rt_user_id)):
            writer.writerow(row)
    logging.info('Wrote {0} ratings to {1}'.format(n, csv_output))

def main():
    logging.basicConfig(
            filename='rt_scrape.log',
            level=logging.INFO)
    # Create cache dir if it doesn't exist
    try:
        os.mkdir('cache')
    except OSError:
        if OSError.errno == errno.EEXIST:
            pass

    parser = argparse.ArgumentParser(description='Work with ratings')

    parser.add_argument('-c', '--csv-output',
                        help='Filename for csv output')
    parser.add_argument('--rt-user-id',
                        default=config.RT_USER_ID,
                        help='Your RT user number')

    args = parser.parse_args()
    write_rt_ratings_to_csv(args.csv_output, args.rt_user_id)


if __name__ == '__main__':
    main()
