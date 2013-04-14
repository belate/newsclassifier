"""
scraper.py
==========

Using several online newspapers like BBC, The Guardian, The Telegraph,
and Reuters, scrap the latest news to create a training set of data already
classified by category.

This script will generate a json file for each category inside the ``articles``
folder.

Usage
-----
$ python scraper.py

"""

import os
import re
import json
import random
from collections import OrderedDict

import requests
from bs4 import BeautifulSoup


#
# Newspapers parsers
#

def extract_text_from_p(body):
    return clean(' '.join([t.get_text() for t in body[0].find_all('p')]))


def bbc(soup):
    body = soup.find_all('div', class_='story-body')
    if body:
        return extract_text_from_p(body)
    return None


def theguardian(soup):
    body = soup.find_all('div', id='content')
    if body:
        return extract_text_from_p(body)
    return None


def telegraph(soup):
    body = soup.find_all('div', class_='story')
    if body:
        return extract_text_from_p(body)
    return None


def reuters(soup):
    body = soup.find_all('div', id_='articleText')
    if body:
        return extract_text_from_p(body)
    return None

#
# Categories we'll use to classify
#

CATEGORIES = OrderedDict(
        [['business', [[bbc, 'business'],
                       [theguardian, 'business'],
                       [telegraph, 'finance']]],
         ['politics', [[bbc, 'politics'],
                       [telegraph, 'politics']]],
         ['health', [[bbc, 'health'],
                     [theguardian, 'lifeandstyle'],
                     [reuters, 'UKHealthNews']]],
         ['science', [[bbc, 'science_and_environment'],
                      [theguardian, 'environment'],
                      [reuters, 'UKScienceNews']]],
         ['technology', [[bbc, 'technology'],
                         [theguardian, 'technology'],
                         [telegraph, 'technology'],
                         [reuters, 'technologyNews']]],
         ['entertainment', [[bbc, 'entertainment_and_arts'],
                            [theguardian, 'tv-and-radio'],
                            [theguardian, 'culture'],
                            [telegraph, 'culture']]],
         ['sports', [[theguardian, 'sport'],
                     [telegraph, 'sport'],
                     [telegraph, 'football'],
                     [reuters, 'UKSportsNews']]]])

#
# RSS for every newspaper
#

RSS = {bbc: 'http://feeds.bbci.co.uk/news/{0}/rss.xml',
       theguardian: 'http://feeds.guardian.co.uk/theguardian/{0}/rss',
       telegraph: 'http://www.telegraph.co.uk/{0}/rss',
       reuters: 'http://mf.feeds.reuters.com/reuters/{0}'}


def clean(text):
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def main(path):

    # Create destination directory if it doesn't exist:
    if not os.path.exists(path):
        os.mkdir(path)

    # Get a json of articles for every category.
    for category, sources in CATEGORIES.iteritems():

        content = []

        for parser, source_category in sources:

            # Get the RSS
            link = RSS.get(parser).format(source_category)
            print link
            print "=" * 50

            feed = requests.get(link, timeout=20)
            if feed.status_code != 200:
                continue

            # Loop all over the news and parse each one using
            # the appropiate parser.

            for url in BeautifulSoup(feed.content).find_all('guid'):
                try:
                    print url.text
                    article = requests.get(url.text, timeout=20)
                except Exception:
                    continue
                soup = BeautifulSoup(article.content, 'html5lib')

                body = parser(soup)
                if body:
                    content.append(body)

        random.shuffle(content)

        # Save all the articles shuffled as json
        with open('articles/{0}.json'.format(category), 'w') as output:
            output.write(json.dumps(content))

if __name__ == '__main__':
    main('articles')
