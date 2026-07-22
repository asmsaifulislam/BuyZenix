import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'buyzenix.settings')
django.setup()
from core.models import Product, Category, ProductImage
from dashboard.models import Banner, Coupon, SiteSettings, Promotion, APIKey
from orders.models import Order
from django.contrib.auth.models import User
print('=== USERS ===')
for u in User.objects.all():
    print(' ', u.username, '| staff:', u.is_staff, '| superuser:', u.is_superuser)
print()
print('=== CATEGORIES ===')
for c in Category.objects.all():
    print(' ', c.name, '| slug:', c.slug, '| image:', bool(c.image))
print()
print('=== PRODUCTS ===')
for p in Product.objects.all():
    print(' ', p.name[:50], '| cat:', p.category, '| price:', p.price, '| sale:', p.sale_price, '| stock:', p.stock, '| featured:', p.featured, '| avail:', p.available, '| image:', bool(p.image), '| supplier:', p.supplier)
print()
print('=== BANNERS ===')
for b in Banner.objects.all():
    print(' ', b.title, '| active:', b.is_active, '| image:', bool(b.image))
print()
print('=== COUPONS ===')
for c in Coupon.objects.all():
    print(' ', c.code, '| type:', c.discount_type, '| value:', c.discount_value, '| active:', c.is_active)
print()
print('=== PROMOTIONS ===')
for p in Promotion.objects.all():
    print(' ', p.title, '| pos:', p.position, '| active:', p.is_active)
print()
print('=== API KEYS ===')
for k in APIKey.objects.all():
    print(' ', k.name, '| cat:', k.category, '| active:', k.is_active)
print()
print('=== ORDERS ===')
print('Count:', Order.objects.count())
print()
print('=== PRODUCT IMAGES ===')
print('Count:', ProductImage.objects.count())
print()
print('=== SITE SETTINGS ===')
for s in SiteSettings.objects.all():
    print(' ', s.site_name, '| email:', s.contact_email, '| phone:', s.contact_phone)