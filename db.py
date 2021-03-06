import aiohttp
from motorengine import Document
from motorengine import StringField, IntField, BooleanField, ListField, FloatField
from motorengine import EmailField, EmbeddedDocumentField
import motorengine.errors
import logging
import time
from cid import make_cid
_OAUTH_USER_URL = 'https://api.github.com/user'


class Wallet(Document):
    likeid = StringField()
    filecoin = StringField()


class Author(Document):

    name = StringField(required=True)
    url = StringField()
    avatar = StringField()
    description = StringField()
    wallet = EmbeddedDocumentField(embedded_document_type=Wallet)
    # id = StringField()  # TODO: user's ipns profile, json&html
    # github_id = IntField()


class Share(Document):
    __collection__ = "share2"  # optional

    id = StringField(required=True, unique=True)  # ipfs:// ipns:// not cid
    idx = IntField(required=True, unique=True)  # just for fun
    publisher_id = IntField(required=True)  # we use github_id
    title = StringField(required=True)
    filetype = StringField(required=True)
    license = StringField()
    summary = StringField()
    content_html = StringField()
    url = StringField()  # URLField()

    tags = ListField(StringField(required=True, max_length=255))  # required=True
    authors = ListField(EmbeddedDocumentField(embedded_document_type=Author))
    # created_at = StringField()
    # update_at = StringField()

    # for filecoin
    data_cid = StringField()
    miner_ids = ListField(StringField(required=True, max_length=255))


class GithubAuth(Document):

    # basic
    token = StringField(required=True)
    id = IntField(required=True)
    login = StringField(required=True)
    node_id = StringField(required=True)

    name = StringField(required=True)
    avatar_url = StringField(required=True)
    created_at = StringField(required=True)
    updated_at = StringField(required=True)
    email = EmailField(required=True)  # private
    # optional
    followers = IntField(required=True)
    following = IntField(required=True)
    public_gists = IntField(required=True)
    public_repos = IntField(required=True)
    location = StringField(required=True)
    company = StringField(required=True)
    blog = StringField(required=True)
    site_admin = BooleanField()
    hireable = BooleanField()
    bio = StringField()
    twitter_username = StringField()


class Meta(Document):
    __collection__ = "meta4"  # optional

    path = StringField(required=True)
    eth = StringField(required=True)
    name = StringField(required=True)
    image = StringField(required=True)
    tags = ListField(StringField(required=True, max_length=255))  # required=True
    authors = StringField(required=True)
    idx = IntField(required=True, unique=True)  # just for fun
    created_at = FloatField()

class Metaversion(Document):
    __collection__ = "metaversion4"  # optional

    mid = StringField(required=True) # mongo_id
    cidnew = StringField(required=True)
    cidold = StringField(required=True) # verbose

async def fetch_user(token):
    headers = {}
    headers['Authorization'] = 'token {}'.format(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(_OAUTH_USER_URL, headers=headers) as resp:
            return await resp.json()


async def get_github_info(token):
    auth = await GithubAuth.objects.get(token=token)
    if auth:
        return auth.to_son()
    else:
        user = await fetch_user(token)
        user['token'] = token
        l_keys = 'html events followers following gists organizations received_events repos starred subscriptions'
        for k in l_keys.split():
            user.pop('{}_url'.format(k))
        user.pop('url')
        _auth = GithubAuth(**user)
        _auth = await _auth.save()
        return user


async def add_share(doc, token):
    cid = doc['id']
    if not cid.startswith('ipfs://') and not cid.startswith('ipns://'):
        return 'Error: Content ID should startswith ipfs:// or ipns://'
    shares = await Share.objects.filter(id=cid).limit(1).find_all()
    if shares:  # should update by same publisher_id
        try:
            ashare = shares[0]
            _id = ashare._id
            share = Share(_id=_id, **doc)
            share.idx = ashare.idx
            user = await get_github_info(token)
            if ashare.publisher_id != user['id']:
                return 'publisher should be same'
            share.publisher_id = user['id']
            if share.authors and len(share.authors) == 1:
                author = {}
                name = share.authors[0].get('name')
                author['name'] = name if name else user['name']
                url = share.authors[0].get('url')
                author['url'] = url if url else user['blog']
                wallet = share.authors[0].get('wallet')
                if wallet:
                    author['wallet'] = Wallet(**wallet)
                share.authors = [author]
            share.authors = [Author(**author) for author in share.authors]
            share = await share.save(upsert=True)
            share.authors = [author.to_son() for author in share.authors]
            return share
        except motorengine.errors.InvalidDocumentError as e:
            logging.error(e)
            return e
    try:
        share = Share(**doc)
        user = await get_github_info(token)
        share.publisher_id = user['id']
        if share.authors and len(share.authors) == 1:
            author = {}
            name = share.authors[0].get('name')
            author['name'] = name if name else user['name']
            url = share.authors[0].get('url')
            author['url'] = url if url else user['blog']
            wallet = share.authors[0].get('wallet')
            if wallet:
                author['wallet'] = Wallet(**wallet)
            share.authors = [author]
        share.authors = [Author(**author) for author in share.authors]
        share.idx = await Share.objects.count() + 1  # TODO 2
        share = await share.save()
        share.authors = [author.to_son() for author in share.authors]
        return share
    except motorengine.errors.InvalidDocumentError as e:
        logging.error(e)
        return e


async def add_meta(path, eth, name, image, tags, authors):

    try:
        doc = {}
        doc['eth'] = eth
        doc['name'] = name
        if 'https://ipfs.infura.io' in image: # v1
            id0 = image.replace('https://ipfs.infura.io/ipfs/','')
            cid = make_cid(id0)
            id1 = cid.to_v1().encode('base32').decode()
            image = 'https://{}.ipfs.infura-ipfs.io/'.format(id1)
        if path.startswith('Qm'):
            cid = make_cid(path)
            path = cid.to_v1().encode('base32').decode()
        doc['path'] = path
        doc['image'] = image
        doc['tags'] = tags
        doc['authors'] = authors
        doc['idx'] = await Meta.objects.count() + 1
        doc['created_at'] = time.time()
        meta = Meta(**doc)
        meta = await meta.save()
        return meta
    except motorengine.errors.InvalidDocumentError as e:
        print(e)
        logging.error(e)
        return e



async def edit_meta(previous_path, path, eth, name, image, tags, authors):

    try:
        if 'https://ipfs.infura.io' in image:
            id0 = image.replace('https://ipfs.infura.io/ipfs/','')
            cid = make_cid(id0)
            id1 = cid.to_v1().encode('base32').decode()
            image = 'https://{}.ipfs.infura-ipfs.io/'.format(id1)
        if path.startswith('Qm'):
            cid = make_cid(path)
            path = cid.to_v1().encode('base32').decode()
        if previous_path.startswith('Qm'):
            cid = make_cid(previous_path)
            previous_path = cid.to_v1().encode('base32').decode()

        doc = {}
        doc['eth'] = eth
        doc['name'] = name
        doc['path'] = path
        doc['image'] = image
        doc['tags'] = tags
        doc['authors'] = authors
        doc['updated_at'] = time.time()

        metas = await Meta.objects.filter(path=previous_path).limit(1).find_all()
        if metas:  # should update by same publisher_id
            try:
                ameta = metas[0]
                _id = ameta._id
                doc['idx'] = ameta.idx
                meta = Meta(_id=_id, **doc)
                meta = await meta.save(upsert=True)
                
                docv = {}
                docv['mid'] = str(_id)
                docv['cidold'] = previous_path
                docv['cidnew'] = path
                metav = Metaversion(**docv)
                metav = await metav.save()
                return meta
            except motorengine.errors.InvalidDocumentError as e:
                logging.error(e)
                return e
        else:
            return 'no doc'


    except motorengine.errors.InvalidDocumentError as e:
        print(e)
        logging.error(e)
        return e


async def get_meta(eth=None, tag=None):

    l_shares = []
    if eth:
        if eth == '*':
            shares = await Meta.objects.order_by('idx').find_all()
        else:
            shares = await Meta.objects.filter(eth=eth.lower()).find_all()
    elif tag:
        # shares = await Meta.objects.filter(eth=eth.lower()).find_all()
        shares = await Meta.objects.filter(tags=tag.lower()).find_all()
    if shares:
        for share in shares:
            l_shares.append(share._values)
    return l_shares[::-1]


async def search_shares(question):
    # TODO: add elasticsearch or MeiliSearch
    # init
    l_shares = []
    l_cids = set()
    l_searched = set()
    # search by title # x times # lower upper capitalize

    l_searched.add(question)
    shares = await Share.objects.filter(title=question).order_by('idx').limit(5).find_all()
    for share in shares:
        if share.id not in l_cids:
            share.authors = [author.to_son() for author in share.authors]
            item = share._values
            l_shares.append(item)
        l_cids.add(share.id)
    if question.upper() not in l_searched:
        l_searched.add(question.upper())
        shares = await Share.objects.filter(title=question.upper()).order_by('idx').limit(5).find_all()
        for share in shares:
            if share.id not in l_cids:
                share.authors = [author.to_son() for author in share.authors]
                item = share._values
                l_shares.append(item)
            l_cids.add(share.id)
    if question.capitalize() not in l_searched:
        l_searched.add(question.capitalize())
        shares = await Share.objects.filter(title=question.capitalize()).order_by('idx').limit(5).find_all()
        for share in shares:
            if share.id not in l_cids:
                share.authors = [author.to_son() for author in share.authors]
                item = share._values
                l_shares.append(item)
            l_cids.add(share.id)
    # tags
    shares = await Share.objects.filter(tags=question.lower()).order_by('idx').limit(42).find_all()
    for share in shares:
        share.authors = [author.to_son() for author in share.authors]
        item = share._values
        if share.id not in l_cids:
            l_shares.append(item)
        l_cids.add(share.id)
    # search by tags, it's slow now
    if not l_shares:
        shares = await Share.objects.filter(tags__contains=question).order_by('idx').limit(42).find_all()
        for share in shares:
            share.authors = [author.to_son() for author in share.authors]
            item = share._values
            if share.id not in l_cids:
                l_shares.append(item)
            l_cids.add(share.id)
    return l_shares


async def get_shares():
    shares = await Share.objects.limit(10).find_all()
    return shares
