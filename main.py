from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
import BeautifulSoup
import logging
import os
import urllib
class PageHandler(webapp.RequestHandler):
    def get(self):
        pass
        
    def send_response(self, links, heading):
        articles = []
        for link in links:
            linktext = link.string
            url = link['href']
            byline = unicode(link.nextSibling).strip()
            articles.append({
                'url': url,
                'byline': byline,
                'linktext': linktext,
                }
            )
        template_values = {'heading': heading, 'articles': articles}
        
        path = os.path.join(os.path.dirname(__file__), 'list.html')
        self.response.out.write(template.render(path, template_values))
        
    def post(self):
        articles = self.request.get_all("articles")
        for url in articles:
           taskqueue.add(
               url='/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', 
               params={'url': url}
           )
        self.response.out.write("Sent %d articles to instapaper" % len(articles))        

class BreakfastPoliticsHandler(PageHandler):
    def get(self):
        soup = BeautifulSoup.BeautifulSoup(urlfetch.fetch(url='http://www.breakfastpolitics.com').content)
        heading = soup.findAll('h2', {'class':'date-header'})[0].string
        links = soup.findAll('div', {'class':'entry-content'})[0].findAll('a')
        self.send_response(links, heading)
        
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

def main():
    application = webapp.WSGIApplication([
        ('/breakfast', BreakfastPoliticsHandler),
        ('/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', LoadWorkerHandler),        
        ],
        debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
