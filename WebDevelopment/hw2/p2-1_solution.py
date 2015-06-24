import webapp2
import jinja2
import os

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
template_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)

def to_render(template, **para):
    t = template_env.get_template(template)
    return t.render(para)

class BaseHandler(webapp2.RequestHandler):
    def render(self, template, **para):
        self.response.out.write(to_render(template, **para))

class Rot13(BaseHandler):
     def get(self):
         self.render('rot13.html')

     def post(self):
         rot13_text = ""
         text = self.request.get('text')
         if text:
             rot13_text = text.encode('rot13')
             self.render('rot13.html', text = rot13_text)



app = webapp2.WSGIApplication([('/', Rot13)],
        debug=True)

