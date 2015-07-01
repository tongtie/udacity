import webapp2
import jinja2
import os
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

def to_render(template, **para):
    t = template_env.get_template(template)
    return t.render(para)

def blog_key(name='default'):
        return db.Key.from_path('blog', name)

class Art(db.Model):
    title = db.StringProperty(required = True)
    arc = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)

    def render(self):
        self._render_text = self.arc.replace('\n', '<br>')
        return to_render('post.html', p = self)
        

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **para):
        self.response.out.write(to_render(template, **para))

class FrontPage(BaseHandler):
     def get(self):
        arts = []
        arts = db.GqlQuery("select * from Art order by created DESC")
        self.render("frontPage.html", arts = arts)

class ShowPost(BaseHandler):
     def get(self, post_id):
         key = db.Key.from_path('Art', int(post_id), parent=blog_key())
         post = db.get(key)

         self.render('permanlink.html', post = post)

"""Problem: 
        1. redirect('/blog') don't refresh the page
        2. how  add id colum to db automatiaclly increase
        3. miss click on the title jump to a new page 
"""
class NewPost(BaseHandler):
     def get(self):
        self.render("newPost.html")

     def post(self):
         title = self.request.get('title')
         arc = self.request.get('arc')
         if title and arc.strip():
             a = Art(parent=blog_key(), title = title, arc = arc)
             a.put()
             
             self.redirect('/blog/%s' % str(a.key().id()))
         else:
             self.render("newPost.html", title=title, arc = arc, error="Content insufficiency")

app = webapp2.WSGIApplication([('/blog/?', FrontPage), ('/blog/newpost', NewPost), ('/blog/([0-9]+)', ShowPost)],
        debug=True)

