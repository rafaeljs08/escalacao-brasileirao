from django.contrib import admin
from django.urls import include, path

admin.site.site_header = 'Escalação Brasileirão'
admin.site.site_title = 'Escalação Brasileirão'
admin.site.index_title = 'Administração'
admin.site.site_url = '/'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('futebol.urls')),
]
