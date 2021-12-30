#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
import json
import tornado.ioloop
import tornado.web
import tornado.auth
import tornado.escape
import tornado.log
from tornado.web import RequestHandler
from motorengine import connect
from auth import GithubMixin2
import db
import options
from log import logger
import argparse
from version import BackendVersion

parser = argparse.ArgumentParser(
    description='Welcome to Dweb World')
parser.add_argument(
    '-p', '--port',
    dest='port',
    action='store',
    type=int,
    default=options.port,
    help='run on the given port'
)
args = parser.parse_args()


class JsonHandler(RequestHandler):

    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self):
        pass


class ProxyHandler(JsonHandler, GithubMixin2):

    async def get(self):
        code = self.get_argument('code', None)
        client_id = self.get_argument('client_id', None)
        if not client_id or client_id not in options.d_auth:
            self.write({'error': 'wrong client_id'})
            return
        params = {
            'client_id': client_id,
            'client_secret': options.d_auth[client_id],
            'code': code,
            # TODO: add state as param
        }
        ret = await self.get_authenticated_user(**params)
        ret = codecs.decode(ret, 'ascii')
        ret = json.loads(ret)
        self.write(ret)


class ShareHandler(JsonHandler):
    async def post(self):
        token = self.request.headers['Authorization'][6:]
        d = tornado.escape.json_decode(self.request.body)
        if 'tags' in d and isinstance(d['tags'], str):
            d['tags'] = [tag.strip() for tag in d['tags'].strip().split(',')]
        if 'miner_ids' in d:
            miner_ids = d['miner_ids'].strip().split(',')
            d['miner_ids'] = [i.strip() for i in miner_ids if i.strip()]
        share = await db.add_share(d, token)
        if hasattr(share, '_values'):
            ret = {'data': share._values}
        else:
            ret = {'error': str(share)}
        self.write(ret)


class AddMetaHandler(JsonHandler):
    async def post(self):
        path = self.get_argument("path", '')
        eth = self.get_argument("eth", '')
        name = self.get_argument("name", '')
        image = self.get_argument("image", '')
        tags = self.get_argument("tags", '')
        authors = self.get_argument("authors", '')
        if not path:
            logger.info(self.request.body)
            d = json.loads(self.request.body.decode('u8'))
            path = d.get('path')
            eth = d.get('eth')
            name = d.get('name')
            image = d.get('image')
            tags = d.get('tags')
            authors = d.get('authors')
        if not path:
            self.write({'error': 'server got no data'})
            return
        tags = tags.strip().split()
        meta = await db.add_meta(path, eth, name, image, tags, authors)
        print(dir(meta))
        if hasattr(meta, '_values') and meta._values:
            ret = {'data': meta._values}
        else:
            ret = {'error': str(meta)}
        self.write(ret)

    async def get(self):
        return await self.post()


class GetMetaHandler(JsonHandler):
    async def get(self):
        eth = self.get_argument("eth", '')
        if not eth:
            self.write({'error': 'no path'})
            return
        docs = await db.get_meta(eth)
        ret = {'data': docs}
        self.write(ret)


class SearchHandler(JsonHandler):
    async def get(self):
        question = self.get_argument("question", '')
        ret = {}
        ret['version'] = 'https://jsonfeed.org/version/1'
        ret['title'] = 'Search Results of: {}'.format(question)
        if question:
            ret['items'] = await db.search_shares(question)
        else:
            ret['error'] = 'no question'
        print(ret)
        self.write(ret)


class SharesHandler(JsonHandler):
    async def get(self):
        shares = await db.get_shares()
        l_shares = []
        for share in shares:
            l_shares.append(dict(share._values))
        ret = {'data': l_shares}
        self.write(ret)

class VersionHandler(JsonHandler):
    async def get(self):
        ret = {'version': BackendVersion}
        self.write(ret)


def make_app():
    return tornado.web.Application([
        (r"/proxy", ProxyHandler),
        (r"/share", ShareHandler),
        (r"/shares", SharesHandler),
        (r"/search", SearchHandler),
        (r"/add_meta", AddMetaHandler),
        (r"/get_meta", GetMetaHandler),
        (r"/version", VersionHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(args.port)
    logger.info('Server started on %s' % args.port)
    io_loop = tornado.ioloop.IOLoop.instance()
    connect("test2", host="localhost", port=27017, io_loop=io_loop)
    io_loop.start()
