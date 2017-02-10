import os
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.util import login_required
from django.utils import simplejson as json

class Download(db.Model):
    user = db.EmailProperty(required=True)
        url = db.StringProperty(required=True)
        create = db.DateTimeProperty(auto_now_add=True)
        update = db.DateTimeProperty(auto_now=True)
        status = db.StringProperty(required=True)
        progress = db.FloatProperty(default=0.0)

# Create /API/add
# arg
#   user:email
#   url:string
# return
#   id:int
#   fail:-1,ok:>0
#
class Create(webapp.RequestHandler):
    def post(self):
        #email = users.get_current_user().email()
        error = False

        try:
            url = self.request.get('url',default_value='')
            url = json.loads(url)
            email = self.request.get('user',default_value='')
            email = json.loads(email)
            email = email.lower()
        except:
            error = True

        if not error and len(url)>0 and len(email)>0:
            try:
                d = Download(
                    user = email,
                    url  = url,
                    status = "queue")
                d.put()
            except:
                error = True

            if error:
                self.response.out.write("-1")
            else:
                self.response.out.write(str(d.key().id()))

# Update /API/upd
# arg:
#   user:email
#   update:[
#       {"id":int,
#       "status":string,(queue,download,done,fail,cancel,delete)
#        "progress":float},
#   ]
# return:
#   [
#       {"id":int,
#        "update",string},
#   ]
#
class Update(webapp.RequestHandler):
    status = ['queue','download','done','fail','cancel','delete']
        def post(self):
            error = False
            success = []
            try:
                updates = self.request.get('update',default_value='[]')
                updates = json.loads(updates)
                email = self.request.get('user',default_value='')
                email = json.loads(email)
                email = email.lower()
            except:
                error = True

            if not error and len(updates)>0 and len(email) > 0:
                for upd in updates:
                    upd_err = False
                    tmp = {}
                    try:
                        if not 'id' in upd or not 'status' in upd or not 'progress' in upd:
                            upd_err = True
                        elif upd['status'] in self.status:
                            d = Download.get_by_id(upd['id'])
                            if d.user == email:
                                d.status = upd['status']
                                d.progress = upd['progress']
                                d.put()
                                tmp['id'] = upd['id']
                                tmp['update'] = str(d.update)
                            else:
                                upd_err = True
                        else:
                            upd_err = True
                    except:
                        upd_err = True

                    if not upd_err:
                        #success.append(upd['id'])
                        success.append(tmp)

            if error:
                self.response.out.write("[]")
            else:
                self.response.out.write(json.dumps(success))

# Request   /API/get
# arg:
#   user:email
#   type:string	(all,queue,download,done,fail,cancel)
# return:
#   [
#       {"id":int,
#        "url":string,
#        "status":string,
#        "create":string,
#        "update":string,
#        "progress":float},
#   ]
#
class Request(webapp.RequestHandler):
    def post(self):
        #email = users.get_current_user().email()
        error = False
        result = []

        try:
            qtype = self.request.get('type',default_value='')
            qtype = json.loads(qtype)
            email = self.request.get('user',default_value='')
            email = json.loads(email)
            email = email.lower()
        except:
            error = True

        if not error and len(qtype)>0 and len(email) > 0:
            try:
                query_string = "SELECT * FROM Download WHERE user = '"+email+"'"
                if qtype == 'all':
                    pass
                elif qtype == 'queue':
                    query_string = query_string + " AND status = 'queue'"
                elif qtype == 'download':
                    query_string = query_string + " AND status = 'download'"
                elif qtype == 'done':
                    query_string = query_string + " AND status = 'done'"
                elif qtype == 'fail':
                    query_string = query_string + " AND status = 'fail'"
                elif qtype == 'cancel':
                    query_string = query_string + " AND status = 'cancel'"
                else:
                    error = True
                if not error:
                    results = db.GqlQuery(query_string)
                results = results.fetch(1000)
                for r in results:
                    tmp = {}
                    tmp['id'] = r.key().id()
                    tmp['url'] = r.url
                    tmp['status'] = r.status
                    tmp['progress'] = r.progress
                    tmp['create'] = str(r.create)
                    tmp['update'] = str(r.update)
                    result.append(tmp)
            except:
                error = True

            if error:
                self.response.out.write("[]")
            else:
                self.response.out.write(json.dumps(result))

class GetByTime(webapp.RequestHandler):
    def post(self):
        error = False
        result = []

        try:
            email = self.request.get('user',default_value='')
            email = json.loads(email)
            email = email.lower()
            updtime = self.request.get('time',default_value='')
            updtime = json.loads(updtime)
            updtime = updtime[:updtime.index('.')]
        except:
            error = False

        if not error and len(email) > 0 and len(updtime) > 0:
            query_string = "SELECT * FROM Download WHERE user = '"+email+"' AND update > DATETIME('"+updtime+"')"
            results = db.GqlQuery(query_string)
            results = results.fetch(1000)
            for r in results:
                tmp = {}
                tmp['id'] = r.key().id()
                tmp['url'] = r.url
                tmp['status'] = r.status
                tmp['progress'] = r.progress
                tmp['create'] = str(r.create)
                tmp['update'] = str(r.update)
                result.append(tmp)

            self.response.out.write(json.dumps(result))

        else:
            self.response.out.write('[]')

# GetById   /API/getById
# arg:
#   user:email
#   id:int
# return:
#   {"id":int,
#    "url":string,
#    "status":string,
#    "create":string,
#    "update":string,
#    "progress":float}
#
#   if fail: id=-1
#
class GetById(webapp.RequestHandler):
    def post(self):
        #email = users.get_current_user().email()
        error = False

        try:
            did = self.request.get('id',default_value='-1')
            did = json.loads(did)
            email = self.request.get('user',default_value='')
            email = json.loads(email)
            email = email.lower()
        except:
            error = True

        tmp = {}
        if not error and did>0 and len(email)>0:
            try:
                d = Download.get_by_id(did)
                if d.user == email:
                    tmp['id'] = d.key().id()
                    tmp['url'] = d.url
                    tmp['status'] = d.status
                    tmp['progress'] = d.progress
                    tmp['create'] = str(d.create)
                    tmp['update'] = str(d.update)
                else:
                    tmp['id'] = -1
            except:
                error = True
                tmp['id'] = -1

            if error:
                self.response.out.write(json.dumps(tmp))
            else:
                self.response.out.write(json.dumps(tmp))

def main():
    application = webapp.WSGIApplication([
        ('/API/add', Create),
        ('/API/get', Request),
        ('/API/getById',GetById),
        ('/API/upd', Update),
        ('/API/getByTime',GetByTime)],debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

