import os
import re
from string import letters

import hmac
import webapp2
import jinja2
import hashlib
import json

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)
SECRET = "tong"

def hash_str(s):
    return hashlib.md5(s).hexdigest()

def make_secure_val(s):
    return "%s|%s" %(s, hmac.new(SECRET, s).hexdigest())

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **kw):
        self.response.out.write(render_str(template, **kw))

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def set_secure_cookie(self, name, val):
        cookie_val = make_secure_val(val)
        self.response.headers.add_header(
                'Set-Cookie',
                '%s=%s; Path=/' % (name, cookie_val))
    
    def render_json(self, d):
        json_txt = json.dumps(d)
        self.response.headers['Content-Type'] = 'application/json;charset=utf-8'
        self.write(json_txt)

    def initialize(self, *a, **kw):
        webapp2.RequestHandler.initialize(self, *a, **kw)
        if self.request.url.endswith('.json'):
            self.format = 'json'
        else:
            self.format = 'html'

class Rot13(BaseHandler):
    def get(self):
        self.render('rot13-form.html')

    def post(self):
        rot13 = ''
        text = self.request.get('text')
        if text:
            rot13 = text.encode('rot13')

        self.render('rot13-form.html', text = rot13)


USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

class User(db.Model):
    uname = db.StringProperty(required = True)
    pword = db.StringProperty(required = True)
    email = db.StringProperty()

    def as_dict(self):
        d = {
                'username': self.uname,
                'password': self.pword,
                'email': self.email
                }
        return d

    @classmethod
    def by_name(cls, name):
        u = User.all().filter('uname = ', name).get()
        return u

    @classmethod
    def by_id(cls, uid):
        u_id = User.get_by_id(uid)
        return u_id

class Signup(BaseHandler):

    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                      email = email)


        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not have_error and User.by_name(username):
            params['error_username'] = 'The username already exist!'
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)
        else:
            u = User(uname = username, 
                    pword = hmac.new(SECRET, password).hexdigest(),
                    email = email)
            u.put()
            self.set_secure_cookie('usernam', str(u.key().id()))
            self.redirect('/unit2/welcome')

class Welcome(BaseHandler):
    def get(self):
        user_key = self.request.cookies.get('usernam')
        user_id = user_key.split('|')[0]
        username = User.by_id(int(user_id)) 
        if username:
            if self.format == 'html':
                self.render('welcome.html', username = username.uname)
            else:
                self.render_json(username.as_dict())
        else:
            self.redirect('/unit2/signup')

class Login(BaseHandler):
    def get(self):
        self.render('login.html')
    
    def post(self):
        uname = self.request.get('username')
        pword = self.request.get('password')

        u = User.by_name(uname)
        if u:
            if u.pword == hmac.new(SECRET, pword).hexdigest():
                self.set_secure_cookie('usernam', str(u.key().id()))
                self.redirect('/unit2/welcome')
            else:
                self.render('login.html', error_msg = "invilid login")
        else:
            self.render('login.html', error_msg = "invilid login")

class Logout(BaseHandler):
    def get(self):
        self.response.headers.add_header('Set-Cookie', 'usernam=; Path=/')
        self.redirect('/unit2/signup')

app = webapp2.WSGIApplication([('/unit2/rot13', Rot13),
                               ('/unit2/signup', Signup),
                               ('/unit2/welcome(?:.json)?', Welcome),
                               ('/unit4/login', Login),
                               ('/unit4/logout', Logout)],
                              debug=True)
