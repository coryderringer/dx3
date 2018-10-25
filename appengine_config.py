from gaesessions import SessionMiddleware

# suggestion: generate your own random key using os.urandom(64)
# WARNING: Make sure you run os.urandom(64) OFFLINE and copy/paste the output to
# this file.  If you use os.urandom() to *dynamically* generate your key at
# runtime then any existing sessions will become junk every time you start,
# deploy, or update your app!
import os
COOKIE_KEY = '\xa9\xab@\xb3\xcet\xf1x\xd1\xc2\xde\xf9\x10\xc3\x0e\xa2\x03Nu\xa7z`\xc1\xc0\xe4\xac*\xa7\xf3`w\xd7\xba$\xa0+KE*F\xae\xd7\xe4y\xc4):\xe5yqiu\x06\x94xi\xe1SKMi\x0e\xdf\xc5'

def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
  app = recording.appstats_wsgi_middleware(app)
  return app
