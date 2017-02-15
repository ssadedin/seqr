'''
Created on 14Feb.,2017

@author: simon.sadedin@mcri.edu.au
'''

import sys
import json
import settings
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


from xbrowse_server.decorators import log_request
from xbrowse_server.mall import get_reference 
from django.conf import settings
from django.core.exceptions import PermissionDenied

from xbrowse_server.base.models import Project

import logging
from vcgs.models import *
from django.core import serializers

log = logging.getLogger('vcgs')

@login_required
@log_request('vcgs/index')
def index(request):
    
    log.info("Showing VCGS file search page")
    
    project = Project.objects.get(project_id='vcgs')
    if not project.can_view(request.user):
        raise PermissionDenied
    
    return render(request, 'file_search.html', {
    })

@login_required
@log_request('vcgs/files')
def get_files(request):

    if request.method != 'GET':
        raise Exception("Unexpected method type : %s" % request.method)
    
    log.info("Returning list of files")
        
    project = Project.objects.get(project_id='vcgs')
    if not project.can_view(request.user):
        raise PermissionDenied
    
    files = []
    for f in SequencingFile.objects.all():
        m = f.toJSON()
        m.update({"run_id":f.run.run_id}) 
        files.append(m)
    
#     return HttpResponse("""{
#         "files": %s,
#     }""" % serializers.serialize("json",files), content_type='application/json') 
#     
    return HttpResponse(json.dumps({"files": files}), content_type='application/json')
    
            
@log_request('vcgs/post_files')
@csrf_exempt
def post_files(request):
    
    if request.method != 'POST':
        raise Exception("Unexpected method type : %s" % request.method)
    
    log.info("Adding files to project")
    print("Adding files to project")
    
    # For now support only FASTQ
    data = json.loads(request.body)
        
    for file_json in data:
            
        run_id = file_json['run_id']
        try:
            run = SequencingRun.objects.get(run_id=run_id)
        except SequencingRun.DoesNotExist:
            run = SequencingRun()
            run.run_id = run_id
            run.created_date = datetime.now()
            run.save()
            
        file = SequencingFile()
        file.path = file_json['path']
        file.file_name = file_json['file_name']
        file.content_type = file_json['content_type']
        file.file_size = file_json['file_size']
        file.run = run
        file.save()
        
    return HttpResponse(json.dumps(
    {
        'status': 'ok'
    }), content_type='application/json') 
    return render()
     