from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
import BeautifulSoup
import logging
import os
import urllib
import re

class PageHandler(webapp.RequestHandler):
    def get(self):
        soup = self.get_page_body()
        links = self.get_links(soup)
        heading = self.get_heading(soup)
        self.send_response(links, heading)

    def get_page_body(self):
        pass        
    def get_links(self, soup):
        pass
    def get_heading(self, soup):
        pass
    def parse_story(self, story):
        pass
        
    def send_response(self, links, heading):
        articles = []
        for link in links:
            article = self.parse_story(link)
            if article:
                articles.append(article)

        template_values = {'heading': heading, 'articles': articles}
        
        path = os.path.join(os.path.dirname(__file__), 'list.html')
        self.response.out.write(template.render(path, template_values))
        
    def post(self):
        articles = self.request.get_all("articles")
        username = self.request.get('username')
        password = self.request.get('password')
        for url in articles:
           taskqueue.add(
               url='/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', 
               params={'url': url, 'username': username, 'password': password}
           )
        self.response.out.write("Sent %d articles to instapaper" % len(articles))        

class NYTimesTodaysPaperHandler(PageHandler):
    def get_page_body(self):
        return BeautifulSoup.BeautifulSoup(
            urlfetch.fetch(url='http://www.nytimes.com/pages/todayspaper/index.html').content
        )

    def get_links(self, soup):
        return soup.findAll('div', {'class': re.compile('story$|story headline')})

    def get_heading(self, soup):
        return soup.findAll('div', {'id':'columnistNameHdrInfo'})[0].h3.string.replace('\n',' ')

    def parse_story(self, story):
        link = story.a
        linktext = link.string
        url = link['href']
        byline = ""
        if story and linktext:
            try:
                #works for most things in the main block
                byline = link.nextSibling.nextSibling.string.strip()
            except AttributeError:
                try:
                    #works for the front page block
                    byline = story.find('div', {'class':'byline'}).string
                except AttributeError:
                    pass #give up
            return {
                'url': url,
                'byline': byline,
                'linktext': linktext,
            }  
                  
class BreakfastPoliticsHandler(PageHandler):
    def get_page_body(self):
        return BeautifulSoup.BeautifulSoup(urlfetch.fetch(url='http://www.breakfastpolitics.com').content)

    def get_links(self, soup):
        return soup.findAll('div', {'class':'entry-content'})[0].findAll('a')

    def get_heading(self, soup):
        return "Breakfast Politics for " + soup.findAll('h2', {'class':'date-header'})[0].string

    def parse_story(self, story):
        linktext = story.string
        url = story['href']
        byline = unicode(story.nextSibling).strip()
        return {
            'url': url,
            'byline': byline,
            'linktext': linktext,
        }

class GuardianHandler(PageHandler):
    def get_page_body(self):
        return BeautifulSoup.BeautifulSoup(urlfetch.fetch(url='http://www.guardian.co.uk/theguardian').content)

    def get_links(self, soup):
        li_list = soup.findAll('li',{'class':'normal'})
        links = []
        for li in li_list:
            if li and li.h3 and li.h3.a:
                links.append(li.h3.a)
        return links

    def get_heading(self, soup):
        return "The Guardian for " + soup.findAll('h2')[3].string

    def parse_story(self, story):
        linktext = story.string
        url = story['href']
        byline = ""
        return {
            'url': url,
            'byline': byline,
            'linktext': linktext,
        }

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
        logging.info(form_data)
        instapaper_response = urlfetch.fetch(
            url= "https://www.instapaper.com/api/add",
            method= urlfetch.POST,
            payload= form_data
        )
        logging.info("Lodged %s with instapaper. Reponse = %d" % (article_url, instapaper_response.status_code,))

class InstapaperValidationHandler(webapp.RequestHandler):
    def post(self):
        form_fields = {
          "username": self.request.get('username'),
          "password": self.request.get('password'),
        }
        form_data = urllib.urlencode(form_fields)
        logging.info(form_data)
        instapaper_response = urlfetch.fetch(
            url="https://www.instapaper.com/api/authenticate",
            method=urlfetch.POST,
            payload=form_data
        )
        return self.response.out.write("%d" % (instapaper_response.status_code,))
        
class IndexHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, {}))
def main():
    application = webapp.WSGIApplication([
        ('/breakfast', BreakfastPoliticsHandler),
        ('/nytimes', NYTimesTodaysPaperHandler),
        ('/guardian', GuardianHandler),
        ('/validate', InstapaperValidationHandler),
        ('/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', LoadWorkerHandler),
        ('/', IndexHandler), 
        ],
        debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
