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

import daiquiri
from docopt import docopt
from lxml import etree
import requests

logger = daiquiri.getLogger('node_hola: ' + __name__)


PRODUCTION = 'cn.dataone.org'
STAGING = 'cn-stage.test.dataone.org'
DEVELOPMENT = 'cn-dev.test.dataone.org'


def valid_domain(domain: str) -> bool:
    url = 'https://' + domain + '/cn/v2'
    valid = True
    try:
        r  = requests.get(url=url)
    except Exception as e:
        logger.error(e)
        valid = False
    return valid


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


def mn_poke(identifier: str, base_url: str):
    gmn= base_url + '/home'
    try:
        r = requests.get(gmn)
        if r.status_code == requests.codes.OK:
            print(f'{identifier} is a GMN member node')
    except Exception as e:
        logger.error(e)


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
    for mn in nl:
        mn_poke(mn, nl[mn])

    return 0


if __name__ == "__main__":
    main(sys.argv)
