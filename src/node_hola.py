#!/usr/bin/env python
# -*- coding: utf-8 -*-

""":Mod: node_hola

:Synopsis:

:Author:
    servilla

:Created:
    7/6/18
"""
import sys
import types

from bs4 import BeautifulSoup
import daiquiri
from docopt import docopt
from lxml import etree
import requests

logger = daiquiri.getLogger('node_hola: ' + __name__)


PRODUCTION = 'cn.dataone.org'
STAGING = 'cn-stage.test.dataone.org'
DEVELOPMENT = 'cn-dev.test.dataone.org'


def gmn_version(home_html: str):
    gmn_version = 'Unknown'
    parser = 'lxml'
    # et = etree.fromstring(home_html.encode('utf-8'))
    # table_rows = et.findall('tr')
    # for table_row in table_rows:
    #     table_data = table_row.getchildren()
    #     if table_data[0].text == 'GMN version:':
    #         gmn_version = table_data[1]
    #         break
    # BeautifulSoup required due to non-valid xhtml (it's xml lenient)
    soup = BeautifulSoup(home_html, parser)
    table_rows = soup.find_all('tr')
    for table_row in table_rows:
        table_data = table_row.find_all('td')
        if table_data[0].string == 'GMN version:':
            gmn_version = table_data[1].string
    return gmn_version


def metacat_version(version_xml: str):
    metacat_version = 'Unknown'
    et = etree.fromstring(version_xml.encode('utf-8'))
    metacat_version = et.text
    return metacat_version

def mn_poke(identifier: str, base_url: str):
    mn_type = 'Unknown'
    mn_version = 'Unknown'
    try:
        # Try as GMN
        gmn_url = base_url + '/home'
        r = requests.get(gmn_url)
        if r.status_code == requests.codes.OK:
            mn_type = 'GMN'
            mn_version = gmn_version(home_html=r.text)
            return mn_type, mn_version
        # Try as Metacat
        if '/d1/mn' in base_url: # Likely Metacat
            metacat_version_url = base_url.strip('/d1/mn') + \
                                  '/metacat?action=getversion'
            r = requests.get(metacat_version_url)
            if r.status_code == requests.codes.OK:
                mn_type = 'Metacat'
                mn_version = metacat_version(version_xml=r.text)
                return mn_type, mn_version
    except Exception as e:
        logger.error(e)
    return mn_type, mn_version


def node_list(domain: str):
    url = 'https://' + domain + '/cn/v2/node'
    nl = dict()
    try:
        r = requests.get(url)
        xml = r.text
        et = etree.fromstring(xml.encode('utf-8'))
        nodes = et.findall('node')
        for node in nodes:
            if node.attrib['type'] == 'mn':
                children = node.getchildren()
                # child 0 = MN identifier; child 3 = baseURL
                nl[children[0].text] = children[3].text
    except Exception as e:
        logger.error(e)
        nl = None
    return nl


def valid_domain(domain: str) -> bool:
    url = 'https://' + domain + '/cn/v2'
    valid = True
    try:
        r  = requests.get(url=url)
    except Exception as e:
        logger.error(e)
        valid = False
    return valid


def main(argv):
    '''
    node_hola returns information about DataONE member nodes registered within
    a specified operating domain (e.g., cn.dataone.org or
    cn-stage.test.dataone.org)

    Usage:
        node_hola.py <domain>
        node_hola.py (-h | --help)

        Arguments:
            domain  The DataONE operating domain that you would like to query

        Options:
            -h --help   This page
    '''
    args = docopt(str(main.__doc__))
    domain = args['<domain>']

    if not valid_domain(domain):
        msg = f'Domain "{domain}" not valid DataONE CN operating domain'
        logger.error(msg)
        return 1

    nl = node_list(domain)
    for mn_id in nl:
        base_url = nl[mn_id]
        mn_type, mn_version = mn_poke(identifier=mn_id, base_url=base_url)
        print(f'{mn_id}, {base_url}, {mn_type}, {mn_version}')
    return 0


if __name__ == "__main__":
    main(sys.argv)
