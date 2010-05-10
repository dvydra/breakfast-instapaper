from google.appengine.ext import db

class InstapaperLogin(db.Model):
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=False)
    create_date = db.DateTimeProperty(auto_now_add=True)
    last_use_date = db.DateTimeProperty(auto_now=True)
    article_count = db.IntegerProperty()
    owner = db.UserProperty(required=True)