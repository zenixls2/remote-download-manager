import os
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import login_required

class IndexPage(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__),'index.html')
        self.response.out.write(template.render(path,{}))

class UserManagePage(webapp.RequestHandler):
    @login_required
    def get(self):
        user = users.get_current_user()
        path = os.path.join(os.path.dirname(__file__),'manage.html')
        self.response.out.write(template.render(path,{
            'userEmail':user.email(),
            'logout_url':users.create_logout_url('/'),
            }))

class APIDocs(webapp.RequestHandler):
    @login_required
    def get(self):
        user = users.get_current_user()
        path = os.path.join(os.path.dirname(__file__),'api.html')
        self.response.out.write(template.render(path,{
            'user':user.email().lower(),
            }))

def main():
    application = webapp.WSGIApplication([
        ('/doc/API',APIDocs),
        ('/manage',UserManagePage),
        ('/', IndexPage)],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

