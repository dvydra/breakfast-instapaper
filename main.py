from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.api import users
from models import InstapaperLogin
import pagehandler
import sitehandlers
import BeautifulSoup
import logging
import os
import urllib
import re
import datetime
from pagehandler import PageHandler, InstapaperValidationHandler

class LoadWorkerHandler(webapp.RequestHandler):
    def post(self):
        article_url = self.request.get('url')
        form_fields = {
          "username": self.request.get('username'),
          "password": self.request.get('password'),
          "url": article_url,
          "auto-title": "1"
        }
        form_data = urllib.urlencode(form_fields)
        instapaper_response = urlfetch.fetch(
            url= "https://www.instapaper.com/api/add",
            method= urlfetch.POST,
            payload= form_data
        )
        logging.info("Lodged %s with instapaper. Reponse = %d" % (article_url, instapaper_response.status_code,))

class DeleteAccountHandler(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user: 
            instapaper_login = InstapaperLogin.gql("WHERE owner = :owner", owner=user).get()
            if instapaper_login:
                username = instapaper_login.owner.email()
                instapaper_login.delete()
                message = "Removed all information for the google account: %s" % username
            else:
                message = "I don't have any account details stored for this google account."
        else:
            message = "You are not logged into your google account."

        path = os.path.join(os.path.dirname(__file__), 'message.html')
        self.response.out.write(template.render(path, {"message": message}))

class IndexHandler(webapp.RequestHandler):
    def get(self):
        logged_in = False
        details_saved = False
        user = users.get_current_user()
        if user: 
            logged_in = True
            instapaper_login = InstapaperLogin.gql("WHERE owner = :owner", owner=user).get()
            if instapaper_login:
                details_saved = True
        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {
            'logged_in': logged_in, 'details_saved': details_saved, 'logout_url': users.create_logout_url("/")
        }))

def main():
    application = webapp.WSGIApplication([
        ('/breakfast', sitehandlers.BreakfastPoliticsHandler),
        ('/nytimes', sitehandlers.NYTimesTodaysPaperHandler),
        ('/theage', sitehandlers.TheAgeTodaysPaperHandler),
        ('/guardian/(.*)', sitehandlers.GuardianHandler),
        ('/guardian', sitehandlers.GuardianHandler),
        ('/delicious', sitehandlers.DeliciousHandler),
        ('/delicious/(.*)', sitehandlers.DeliciousHandler),
        ('/validate', pagehandler.InstapaperValidationHandler),        
        ('/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', LoadWorkerHandler),
        ('/delete', DeleteAccountHandler),
        ('/', IndexHandler), 
        ],
        debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

