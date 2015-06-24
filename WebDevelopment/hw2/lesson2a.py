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

class FizzBuzz(BaseHandler):
     def get(self):
         text = self.request.get('n', 8)
         if text:
             text = int(text)
             self.render('fizzBuzz.html', n = text)



app = webapp2.WSGIApplication([('/', FizzBuzz)],
        debug=True)

