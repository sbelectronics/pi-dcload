from django.conf.urls import patterns, url

from dcload_ui import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^setDesiredMa$', views.setDesiredMa, name='setDesiredMa'),
    url(r'^setPower$', views.setPower, name='setPower'),
    url(r'^getStatus$', views.getStatus, name='getStatus'),
)
