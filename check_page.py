import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buyzenix.settings')
django.setup()
from django.test import RequestFactory
from core.views import home
rf = RequestFactory()
req = rf.get('/')
resp = home(req)
html = resp.content.decode()
idx = html.find('hero-marquee')
print(html[max(0,idx-100):idx+500] if idx != -1 else 'NO MARQUEE FOUND')