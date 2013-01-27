#!/usr/bin/env python
import sys
import argparse

import progressbar

from rt_scraper import config, rt_scraper

def scrape_rt(csv_output, rt_user_id):
    with open(csv_output, 'w') as f:
        rt_scraper.scrape(rt_user_id, outfile=f)


def main():
    parser = argparse.ArgumentParser(description='Work with ratings')

    parser.add_argument('-c', '--csv-output',
                        help='Filename for csv output')
    parser.add_argument('--rt-user-id',
                        default=config.RT_USER_ID,
                        help='Your RT user number')
    parser.add_argument('-s',
                        '--site',
                        choices=['rt'],
                        default='rt')

    args = parser.parse_args()

    if (args.site == 'rt'):
        scrape_rt(args.csv_output, args.rt_user_id)
    else:
        raise Exception("Didn't scrape")


if __name__ == '__main__':
    main()
