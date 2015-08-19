# encoding: UTF-8
import os.path
import re
import random
import hashlib
import hmac
from string import letters
from jinja2 import Environment, FileSystemLoader
import webapp2
from google.appengine.ext import db


tmp_dir = os.path.join(os.path.dirname(__file__), 'templates')
env = Environment(loader = FileSystemLoader(tmp_dir), autoescape = True)

uname_pattern = re.compile(r'\w+')
upw_pattern = re.compile(r'^.{3,20}$')



def render_str(template, **params):
    t = env.get_template(template)
    return t.render(**params)

def make_salt(length = 5):
    return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()
    hash_pw = hashlib.sha256(name+pw+salt).hexdigest()
    return '%s,%s' % (salt, hash_pw)

def users_key(group='default'):
    return db.Key.from_path('users', group)

def equal_pw(name, pw, hash_pw):
    salt = hash_pw.split(',')[0]
    if make_pw_hash(name, pw, salt) == hash_pw:
        return True
    else:
        return False

def check_secure_val(secure_val):
    val = secure_val.split('|')[0]
    if secure_val == make_secure_val(val):
        return val

def make_secure_val(val):
    return '%s|%s' % (val, hmac.new('tong', val).hexdigest())

class Handler(webapp2.RequestHandler):
    def render_write(self, template, **params):
        params['user'] = self.user
        self.response.out.write(render_str(template, **params))
        
    def write(self, *params):
        self.response.out.write(params)

    def set_secure_cookie(self, name, value):
        cookie_val = make_secure_val(value)
        self.response.headers.add_header(
                'Set-Cookie',
                '%s=%s; Path=/' % (name, cookie_val))

    def read_secure_cookie(self, name):
        cookie_val = self.request.cookies.get(name)
        return cookie_val and check_secure_val(cookie_val)
    
    def login(self, user):
        self.set_secure_cookie('user_id', str(user.key().id()))

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        uid = self.read_secure_cookie('user_id')
        self.user = uid and User.by_id(int(uid))


class User(db.Model):
    name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)

    @classmethod
    def register(cls, name, pw):
        hash_pw = make_pw_hash(name, pw)
        return User(parent = users_key(),
                name = name,
                password = hash_pw)

    @classmethod
    def by_name(cls, name):
        return User.all().filter("name =", name).get()

    @classmethod
    def login(cls, name, pw):
        u = cls.by_name(name)
        if u and equal_pw(name, pw, u.password):
            return u
    
    @classmethod
    def by_id(cls, uid):
        return User.get_by_id(uid, parent = users_key())

class Signup(Handler):
    def get(self):
        r_url = self.request.headers.get('referer', '/')
        self.render_write('signup.html', referer = r_url)

    def post(self):
        self.uname = self.request.get('uname')
        self.upw = self.request.get('upw')
        self.cpw = self.request.get('cpw')
        r_url = self.request.get('referer')
        
        if not r_url or r_url.startswith('/login'):
            r_url = '/'

        p = dict(vname = self.uname)
        flag = False

        if not (self.uname and uname_pattern.match(self.uname)):
            p['uerror'] = 'That is not a valid username'
            flag = True

        if not (self.upw and upw_pattern.match(self.upw)):
            p['perror'] = 'That was not a valid password'
            flag = True

        if self.cpw != self.upw:
            p['cperror'] = 'Your password did not match'
            flag = True

        if User.by_name(self.uname):
            p['uerror'] = 'The user already exists'
            flag = True
        
        if flag:
            self.render_write('signup.html', **p)
        else:
            u = User.register(name = self.uname, pw = self.upw)
            u.put()
            self.login(u)
            self.redirect(r_url)

class HomePage(Handler):
    def get(self):
        self.render_write('homepage.html')

class Login(Handler):
    def get(self):
        r_url = self.request.headers.get('referer', '/') 
        self.render_write('login.html', ref_url = r_url)

    def post(self):
        uname = self.request.get('uname')
        pw = self.request.get('pw')
        r_url = str(self.request.get('ref_url'))
        
        if not r_url or r_url.startswith('/login'):
            r_url = '/'

        u = User.login(uname, pw)
        if u:
            self.login(u)
            self.redirect(r_url)
        else:
            self.render_write('login.html', perror = 'Invalid login', 
                    ref_url = r_url)

class Logout(Handler):
    def get(self):
        r_url = self.request.headers.get('referer', '/')
        self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')
        self.redirect(r_url)

class Page(db.Model):
    content = db.TextProperty(required = True)
    author = db.ReferenceProperty(User, required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    modified = db.DateTimeProperty(auto_now = True)

    @staticmethod
    def parent_key(path):
        return db.Key.from_path('/root'+path, 'pages')

    @classmethod
    def by_path(cls, path):
        q = cls.all()
        q.ancestor(cls.parent_key(path))
        q.order('-created')
        return q

    @classmethod
    def by_id(cls, page_id, path):
        return cls.get_by_id(page_id, cls.parent_key(path))

class WikiPage(Handler):
    def get(self, path):
        v = self.request.get('v')
        if v.isdigit():
            p = Page.by_id(int(v), path)
        else:
            p = Page.by_path(path).get()
        if p:
            self.render_write('page.html', page = p, path = path)
        else:
            self.redirect('/_edit'+path)

class Edit(Handler):
    def get(self, path):
        if not self.user:
            self.redirect('/login')
        v = self.request.get('v')
        if v.isdigit():
            p = Page.by_id(int(v), path)
        else:
            p = Page.by_path(path).get()
        self.render_write('edit.html', page = p)

    def post(self, path):
        if not self.user:
            self.error(400)
            return 

        content = self.request.get('text_content')
        p = Page(parent = Page.parent_key(path), content = content, author = self.user)
        p.put()

        self.redirect(path)

class History(Handler):
    def get(self, path):
        if not self.user:
            self.redirect('/login')
        posts = Page.by_path(path)
        if posts:
            self.render_write('history.html', posts = posts, path = path)
        else:
            self.redirect(path)


PAGE_RE = r'(/\w*/?)'

app = webapp2.WSGIApplication([('/signup', Signup),
    ('/', HomePage), ('/login', Login), ('/logout', Logout),
    (PAGE_RE, WikiPage), ('/_edit'+PAGE_RE, Edit), 
    ('/_history'+PAGE_RE, History)], debug = True)
