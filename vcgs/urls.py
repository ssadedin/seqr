'''
Created on 14Feb.,2017

@author: simon.sadedin@mcri.edu.au
'''

from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
import vcgs.files

admin.autodiscover()

urlpatterns = [
    # Breakpoint search
    url(r'^vcgs/filesearch', vcgs.files.views.index, name='files-page'),
    url(r'^vcgs/files', vcgs.files.views.get_files, name='files'),
    url(r'^vcgs/addfiles', vcgs.files.views.post_files, name='files'),
]
