from google.appengine.api import urlfetch
from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util
from google.appengine.api import users
from models import InstapaperLogin
import BeautifulSoup
import logging
import os
import urllib
import re
import datetime

class PageHandler(webapp.RequestHandler):
    def get(self, path=None):
        soup, status_code = self.get_page_body(path)
        links = self.get_links(soup)
        if status_code == 200 and links:
            heading = self.get_heading(soup, path)
            self.send_response(links, heading)
        else:            
            self.error(404)
            self.render_to_response(self.response, '404.html', {})
    
    def get_page_body(self, path=None):
        pass        
    def get_links(self, soup):
        pass
    def get_heading(self, soup, path):
        pass
    def parse_story(self, story):
        pass

    def get_instapaper_login(self):
        user = users.get_current_user()
        instapaper_login = InstapaperLogin.gql("WHERE owner = :owner", owner=user)
        return instapaper_login.get()

    def save_instapaper_login(self, username, password, articles):
        instapaper_login = self.get_instapaper_login()
        if not instapaper_login:
            user = users.get_current_user()
            if user:
                instapaper_login = InstapaperLogin(
                    username=username, 
                    password=password,
                    article_count=0,
                    owner=users.get_current_user()
                )
                instapaper_login.put()
                logging.info("created new account for %s" % user.email())
        else:
            instapaper_login.article_count = instapaper_login.article_count + len(articles)
            instapaper_login.username = username
            instapaper_login.password = password
            instapaper_login.put()
            logging.info("updated account for %s, total articles: %s" % (instapaper_login.owner.email(), instapaper_login.article_count) )

    def send_response(self, links, heading):
        articles = []
        for link in links:
            article = self.parse_story(link)
            if article:
                articles.append(article)
                
        user = users.get_current_user()
        instapaper_login = self.get_instapaper_login()
        if user and instapaper_login:
            greeting = ("Welcome, %s! (<a href=\"%s\">sign out</a>)" %
                        (user.nickname(), users.create_logout_url("/")))
            username = instapaper_login.username
            password = instapaper_login.password
        else:
            greeting = ("<a href=\"%s\">Sign in with your google account to save your instapaper details</a>." %
                        users.create_login_url("/"))
            username = ""
            password = ""

        self.render_to_response(self.response, 'list.html', {
            'heading': heading, 
            'articles': articles, 
            'greeting': greeting,
            'username': username,
            'password': password
        })
        
    def post(self):
        articles = self.request.get_all("articles")
        if not articles:
            return self.response.out.write("You didn't select any articles.<br/><a href='/'>Back to homepage</a>")                
            
        instapaper_login = self.get_instapaper_login()
        username = self.request.get('username')
        password = self.request.get('password')
        response = InstapaperValidationHandler().validate_instapaper_account(username, password)
        
        if response.status_code == 200:
            self.save_instapaper_login(username, password, articles)
            for url in articles:
               taskqueue.add(
                   url='/load-worker-dfsgylsdfgkjdfhlgjkdfdfgjfdslg', 
                   params={'url': url, 'username': username, 'password': password}
               )
            self.response.out.write("Sent %d articles to instapaper <br/><a href='/'>Back to homepage</a>" % len(articles))
        else:
            self.response.out.write("Instapaper login failed, check your details.<br/><a href='/'>Back to homepage</a>")                

    def render_to_response(self, response, template_path, context):
        path = os.path.join(os.path.dirname(__file__), template_path)
        response.out.write(template.render(path, context))

class InstapaperValidationHandler(webapp.RequestHandler):
    def post(self):
        instapaper_response = self.validate_instapaper_account(self.request.get('username'),self.request.get('password'))
        return self.response.out.write("%d" % (instapaper_response.status_code,))

    def validate_instapaper_account(self, username, password):
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