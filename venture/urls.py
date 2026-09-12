from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve as serve_media

from cms.sitemaps import SITEMAPS

admin.site.site_header = "Venture Arabia Administration"
admin.site.site_title = "Venture Arabia Admin"
admin.site.index_title = "Store management"

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("", include("cms.urls")),
    path("", include("catalog.urls")),
    path("shop/", include("shop.urls")),
    path("accounts/", include("accounts.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": SITEMAPS}, name="sitemap"),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
        name="robots",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
elif settings.SERVE_MEDIA:
    urlpatterns += [re_path(r"^media/(?P<path>.*)$", serve_media, {"document_root": settings.MEDIA_ROOT})]

handler404 = "cms.views.error_404"
handler500 = "cms.views.error_500"
