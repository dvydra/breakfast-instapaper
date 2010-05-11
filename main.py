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
        logging.error('submiting instapaper: %s, %s' % (self.request.get('username'), self.request.get('password')))
        form_data = urllib.urlencode(form_fields)
        instapaper_response = urlfetch.fetch(
            url= "https://www.instapaper.com/api/add",
            method= urlfetch.POST,
            payload= form_data
        )
        logging.info("Lodged %s with instapaper. Reponse = %d" % (article_url, instapaper_response.status_code,))
        
class IndexHandler(webapp.RequestHandler):
    def get(self):        
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {}))

def main():
    application = webapp.WSGIApplication([
        ('/breakfast', sitehandlers.BreakfastPoliticsHandler),
        ('/nytimes', sitehandlers.NYTimesTodaysPaperHandler),
        ('/guardian/(.*)', sitehandlers.GuardianHandler),
        ('/guardian', sitehandlers.GuardianHandler),
        ('/delicious', sitehandlers.DeliciousHandler),
        ('/delicious/(.*)', sitehandlers.DeliciousHandler),
        ('/validate', pagehandler.InstapaperValidationHandler),        
        ('/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', LoadWorkerHandler),
        ('/', IndexHandler), 
        ],
        debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

