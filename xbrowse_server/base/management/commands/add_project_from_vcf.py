from django.core.management.base import BaseCommand
from xbrowse_server.base.models import Project
import sys
from django.conf import settings
from django.utils import timezone
from xbrowse_server.base.management.commands import add_project_to_phenotips,\
    add_individuals_to_project, add_individuals_to_phenotips, load_project_dir
import vcf
import csv
import os
import local_settings
import shutil

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='+')

    def handle(self, *args, **options):
        if len(args)<1 or not args[0]:
          print '\n\n'
          print """
          A convenience command that does all the steps to create a project and import data for
          a case where there is a single PED file and multiple VCFs, and these fully describe
          the project.

          print 'Example: python manage.py add_project_from_vcf 1kg "My awesome project" 1kg.ped 1kg_1.vcf 1kg_2.vcf ...\n'

          """
          sys.exit()

        project_id = args[0]
        if "." in project_id:
            sys.exit("ERROR: A '.' in the project ID is not supported")

        if Project.objects.filter(project_id=project_id).exists():
            print '\nSorry, I am unable to create that project since it exists already\n'
            sys.exit()
        
        if len(args) > 1:
            project_name = args[1]
            print('Creating project with id: %(project_id)s with name: %(project_name)s' % locals())
        else: 
            sys.exit("ERROR: Please provide 2 args: the project_id and the project_name")

        vcf_files = args[3:]
        if(len(vcf_files) > 0):
            vcfs = [ vcf.Reader(open(vcf_file,'r')) for vcf_file in vcf_files ]
            samples = [ avcf.samples for avcf in vcfs ].sum()
            print "Found samples in VCF files: " + ",".join(samples)
        else:
            vcfs = []

        ped_file = args[2]
        ped_columns = ['family','sample','father','mother','sex','phenotype']
        with open(ped_file) as ped_file_handle:
            ped = [ dict(zip(ped_columns, row[0:6])) for row in csv.reader(ped_file_handle, delimiter='\t') 
                 ]
        
        self.make_project(project_id, project_name, ped_file, ped, vcf_files)
        
#         sys.exit(0)
        
        try:
            print("Creating Seqr Project ...")
            Project.objects.create(project_id=project_id, project_name=project_name, created_date=timezone.now())
            
            print("Creating Phenotips Project ...")
            add_project_to_phenotips.Command().handle(project_id,project_name)
            
            print("Adding samples to project ...")
            project_dir = os.path.join(local_settings.xbrowse_install_dir,'data','projects',project_id)
            project_ped_file = os.path.join(project_dir, 'sample_data', '%s.ped' % project_id )
            add_individuals_to_project.Command().handle(project_id, 
                                                        ped=project_ped_file,
                                                        vcf=None,
                                                        xls=None)
            
            print("Adding samples to phenotips ...")
            add_individuals_to_phenotips.Command().handle(project_id, 
                                                          ped=project_ped_file,
                                                          vcf=None,
                                                          all=None)
            
            print("Loading project")
            load_project_dir.Command().handle(project_id, project_dir)
            
        except Exception as e:
          print('\nError creating project:', e, '\n')
          sys.exit()

    def make_project(self, project_id, project_name, ped_file, ped, vcf_files):
        
        # First make the folders
        project_dir = os.path.join(local_settings.xbrowse_install_dir,'data','projects',project_id)
        os.makedirs(os.path.join(project_dir, 'sample_data'))
        
        # Put all the samples from PED file into the samples file
        with open(os.path.join(project_dir,'all_samples.txt'),'w') as all_samples_file:
            for sample in ped:
                print >>all_samples_file, sample['sample']
                
        print "Wrote %d samples" % len(ped)
        project_ped_file = os.path.join('sample_data', '%s.ped' % project_id )
        
        # Copy the ped file to the project
        shutil.copyfile(ped_file, os.path.join(project_dir, project_ped_file))
        
        # Create the project.yaml file
        vcf_file_list = ''.join([
            ' - %s\n' % vcf_file for vcf_file in vcf_files
        ])
        
        template_string = """
project_id: '%(project_id)s'

project_name: '%(project_name)s'

sample_id_list: 'all_samples.txt'

ped_files:
  - '%(project_ped_file)s'
""" + ("""
vcf_files: 
%(vcf_file_list)s
""" if len(vcf_files) > 0 else "")
        with open(os.path.join(project_dir, 'project.yaml'), 'w') as project_file:
            project_file.write(template_string % {
                'project_id' : project_id,
                'project_name' : project_name,
                'project_ped_file' : project_ped_file,
                'vcf_file_list' : vcf_file_list
                })

# - 'NA12878_CARDIACM_MUTATED.individual.genotype.soi.vep.vcf.gz'
        