'''
Created on 14Feb.,2017

@author: simon.sadedin@mcri.edu.au
'''
from django.db import models

# class SequencingSample(models.Model):
#     
#     sample_id = models.TextField(max_length=256, null=False, blank=False, unique=False)
#     
#     sex = models.TextField(max_length=256, null=True, blank=False, unique=False)
# 
# class SequencingLibrary(models.Model):
#     
#     library_id = models.TextField(max_length=256, null=False, blank=False, unique=False)
#     
#     created_date = models.DateTimeField(null=True, blank=True)
#     
#     library_date = models.DateTimeField(null=True, blank=True)
#     
#     sample = models.ForeignKey(SequencingSample)
#     
#     library_type = models.TextField(max_length=60, null=False, blank=False, unique=False)

class SequencingRun(models.Model):
    
    run_id = models.TextField(max_length=120, null=False, blank=False, unique=True) 
    
    # When this entry was created
    created_date = models.DateTimeField(null=True, blank=True)
    
    # When the sequencing run occurred
    run_date = models.DateTimeField(null=True, blank=True)

class SequencingFile(models.Model):
    
    path = models.TextField(max_length=512, null=False, blank=False, unique=False)
    
    file_name = models.TextField(max_length=256, null=False, blank=False, unique=False)
    
    file_size = models.BigIntegerField(null=False)
    
    created_date = models.DateTimeField(null=True, blank=True)
    
    content_type = models.TextField(max_length=60)
    
#    library = models.ForeignKey(SequencingLibrary)
    
    run = models.ForeignKey(SequencingRun)
    
    def toJSON(self):
        return {
            "path" : self.path,
            "file_name" : self.file_name,
            "file_size" : self.file_size,
            "content_type" : "text/fastq",
            "created_date" : "2017-02-17 10:11:13"
        }
    