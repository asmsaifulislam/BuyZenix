import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buyzenix.settings')
django.setup()
from core.models import Product
f = Product.objects.filter(available=True, featured=True)
print('COUNT:', f.count())
for p in f:
    print(p.name, bool(p.image))

from dashboard.models import Promotion
pl = Promotion.objects.filter(is_active=True, position='hero_left')
pr = Promotion.objects.filter(is_active=True, position='hero_right')
print('Hero left:', pl.count())
print('Hero right:', pr.count())