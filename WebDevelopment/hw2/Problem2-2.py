import webapp2
import re

form = """
<form method="POST">
    <h1>Signup</h1>
    <label>Username
        <input name="uname">
        <label style="color:red">%(uerror)s</label>
    </label>
    <br>
    <label>Password
        <input name="pw" type="password">%(perror)s
    </label>
    <br>
    <label>Verify Password
        <input name="vpw" type="password">%(verror)s
    </label>
    <br>
    <label>Email(optional)
        <input name="email">%(eerror)s
    </label>
    <br>
    <input type="submit">
</form>"""

class MainHandler(webapp2.RequestHandler):
    def writeForm(self, uerror = "", perror="", verror="",
            eerror=""):
        self.response.out.write(form % {'uerror': uerror,
            'perror': perror,
            'verror': verror,
            'eerror': eerror})
    
    def get(self):
        self.writeForm()

    def post(self):
        pw = self.request.get('pw')
        uname = self.request.get('uname')
        email = self.request.get('email')
        vpw = self.request.get("vpw")
        """passwd only allow number and alphabet
        logic error:username and password should be split 
        judgement!"""
        if not(uname.isalpha() and pw.isalnum()):
            self.writeForm("Username is not vaild!",
                    "Password is not vaild!")
        elif pw != vpw:
            self.writeForm(verror="confirm password!")
        elif email and not(re.match(
            '[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$', email)):
            self.writeForm(eerror="Email is not vaild!")

        else:
            self.redirect('/welcome?username='+uname)

class WelcomeHandler(webapp2.RequestHandler):
    def get(self):
		uname = self.request.get('username')
        self.response.out.write("welcome\t" + uname)

app = webapp2.WSGIApplication([('/', MainHandler),
    ('/welcome', WelcomeHandler)],
        debug=True)

