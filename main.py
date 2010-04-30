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

def render_to_response(response, template_path, context):
    path = os.path.join(os.path.dirname(__file__), template_path)
    response.out.write(template.render(path, context))

def validate_instapaper_account(username, password):
    form_fields = {
      "username": username,
      "password": password,
    }
    form_data = urllib.urlencode(form_fields)
    instapaper_response = urlfetch.fetch(
        url="https://www.instapaper.com/api/authenticate",
        method=urlfetch.POST,
        payload=form_data
    )
    return instapaper_response
        
class PageHandler(webapp.RequestHandler):
    def get(self, path=None):
        soup, status_code = self.get_page_body(path)
        links = self.get_links(soup)
        if status_code == 200 and links:
            heading = self.get_heading(soup)
            self.send_response(links, heading)
        else:            
            self.error(404)
            render_to_response(self.response, '404.html', {})

    def get_page_body(self, path=None):
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

        render_to_response(self.response, 'list.html', {'heading': heading, 'articles': articles})
        
    def post(self):
        articles = self.request.get_all("articles")
        username = self.request.get('username')
        password = self.request.get('password')
        response = validate_instapaper_account(username, password)
        if response.status_code == 200:
            for url in articles:
               taskqueue.add(
                   url='/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', 
                   params={'url': url, 'username': username, 'password': password}
               )
            self.response.out.write("Sent %d articles to instapaper <br/><a href='/'>Back to homepage</a>" % len(articles))
        else:
            self.response.out.write("Instapaper login failed, check your details.<br/><a href='/'>Back to homepage</a>")                

class NYTimesTodaysPaperHandler(PageHandler):
    def get_page_body(self, path):
        response = urlfetch.fetch(
            url='http://www.nytimes.com/pages/todayspaper/index.html'
        )
        soup = BeautifulSoup.BeautifulSoup(response.content)
        status_code = response.status_code
        return soup, status_code      

    def get_links(self, soup):
        return soup.findAll('div', {'class': re.compile('story$|story headline')})

    def get_heading(self, soup):
        return soup.findAll('div', {'id':'columnistNameHdrInfo'})[0].h3.string.replace('\n',' ')

    def parse_story(self, story):
        link = story.a
        linktext = link.string
        url = link['href']
        if story and linktext:
            try:
                #works for most things in the main block
                byline = link.nextSibling.nextSibling.string.strip()
            except AttributeError:
                try:
                    #works for the front page block
                    byline = story.find('div', {'class':'byline'}).string
                except AttributeError:
                    byline = ""
            if byline:
                byline = self.trim_by(byline)
            return {
                'url': url,
                'byline': byline,
                'linktext': linktext,
            }

    def trim_by(self, string):
        if string.startswith('By'):
            string = string[3:]
        return string
       
class BreakfastPoliticsHandler(PageHandler):
    def get_page_body(self, path):
        response = urlfetch.fetch(
            url='http://www.breakfastpolitics.com'
        )
        soup = BeautifulSoup.BeautifulSoup(response.content)
        status_code = response.status_code
        return soup, status_code  

    def get_links(self, soup):
        return soup.findAll('div', {'class':'entry-content'})[0].findAll('a')

    def get_heading(self, soup):
        return "Breakfast Politics for " + soup.findAll('h2', {'class':'date-header'})[0].string

    def parse_story(self, story):
        if story.string:
            linktext = self.trim_commas(story.string)
            url = story['href']
            byline = unicode(self.trim_commas(story.nextSibling)).strip()
            return {
                'url': url,
                'byline': byline,
                'linktext': linktext,
            }

    def trim_commas(self, string):
        logging.info(string)
        if string != None:
            if string.startswith(','):
                string = string[2:]
            if string.endswith(','):
                string = string[:-1]
            return string
        else:
            return string

class GuardianHandler(PageHandler):
    def get_page_body(self, path):
        response = urlfetch.fetch(
            url='http://www.guardian.co.uk/theguardian'
        )
        soup = BeautifulSoup.BeautifulSoup(response.content)
        status_code = response.status_code
        return soup, status_code    

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
        instapaper_response = urlfetch.fetch(
            url= "https://www.instapaper.com/api/add",
            method= urlfetch.POST,
            payload= form_data
        )
        logging.info("Lodged %s with instapaper. Reponse = %d" % (article_url, instapaper_response.status_code,))

class InstapaperValidationHandler(webapp.RequestHandler):
    def post(self):
        instapaper_response = validate_instapaper_account(self.request.get('username'),self.request.get('password'))
        return self.response.out.write("%d" % (instapaper_response.status_code,))
    
class DeliciousHandler(PageHandler):
    def get_page_body(self, path):
        response = urlfetch.fetch(
            url='http://feeds.delicious.com/v2/rss/%s?count=50' % path
        )
        soup = BeautifulSoup.BeautifulStoneSoup(response.content)
        status_code = response.status_code
        return soup, status_code

    def get_links(self, soup):
        return soup.findAll('item')

    def get_heading(self, soup):
        return "Delicious: " + soup.findAll('description')[0].string

    def parse_story(self, story):
        linktext = story.title.string
        url = story.link.string
        byline = story.find('dc:creator').string
        return {
            'url': url,
            'byline': byline,
            'linktext': linktext,
        }
        
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
        ('/delicious/(.*)', DeliciousHandler),
        ('/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', LoadWorkerHandler),
        ('/', IndexHandler), 
        ],
        debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()

