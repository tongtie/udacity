#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import cgi

form="""
<form method="POST">
	<textarea rows="30" cols="50" name="text">
	%(c)s
	</textarea>
	<br>
	<input type="submit">
</form>
"""
class MainHandler(webapp2.RequestHandler):
    def write_form(self, c = ""):
	    self.response.out.write(form % {"c": cgi.escape(c, quote=True)})
    
    def get(self):
	    self.write_form()

    def post(self):
	    q = self.request.get('text')
	    self.write_form(self.rot13(self.Crot13(q)))

    def rot13(self, s):
        rot={'a':'n', 'b':'o', 'c': 'p', 'd': 'q', 'e': 'r', 'f': 's', 'g': 't', 'h': 'u', 'i': 'v', 'j': 'w', 'k': 'x', 'l': 'y', 'm': 'z', 'n': 'a', 'o': 'b', 'p':'c', 'q': 'd','r': 'e', 's': 'f', 't': 'g', 'u': 'h', 'v': 'i', 'w': 'j', 'x': 'k', 'y': 'l', 'z':'m'} 

        tmp = ""
        for i in s:
            if rot.get(i):
                tmp += rot.get(i)
            else:
                tmp += i
        return tmp


    def Crot13(self, s):
        tmp = ""
        for i in s:
            if i >= 'A' and i <= 'Z':
                tmp += self.rot13(i.lower()).upper()
            else:
                tmp += i
        return tmp

app = webapp2.WSGIApplication([('/', MainHandler)], debug=True)
