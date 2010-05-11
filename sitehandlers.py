from google.appengine.api import urlfetch
import BeautifulSoup
import datetime
import logging
import re
from pagehandler import PageHandler

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

    def get_heading(self, soup, path):
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

    def get_heading(self, soup, path):
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
        sunday = datetime.datetime.now().weekday() == 6
        paper = "theobserver" if sunday else "theguardian"

        if path:
            url='http://www.guardian.co.uk/%s/%s' % (paper, path)
        else:
            url='http://www.guardian.co.uk/%s' % (paper)
        response = urlfetch.fetch(
            url=url
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

    def get_heading(self, soup, path):
        sunday = datetime.datetime.now().weekday() == 6
        paper = "The Observer" if sunday else "The Guardian"
        if path:
            heading = "%s %s: %s" % (paper, path.title(), soup.findAll('h2')[3].string)
        else:
            heading = "%s %s" % (paper, soup.findAll('h2')[3].string)
        return heading

    def parse_story(self, story):
        linktext = story.string
        url = story['href']
        byline = ""
        return {
            'url': url,
            'byline': byline,
            'linktext': linktext,
        }
    
class DeliciousHandler(PageHandler):
    def get_page_body(self, path):
        if not path:
            path = "popular"
        response = urlfetch.fetch(
            url='http://feeds.delicious.com/v2/rss/%s?count=50' % path
        )
        soup = BeautifulSoup.BeautifulStoneSoup(response.content)
        status_code = response.status_code
        return soup, status_code

    def get_links(self, soup):
        return soup.findAll('item')

    def get_heading(self, soup, path):
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