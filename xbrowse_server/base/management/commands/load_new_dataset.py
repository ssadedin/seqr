from optparse import make_option
from xbrowse_server import xbrowse_controls
from django.core.management.base import BaseCommand
from xbrowse_server.base.models import Project, Family
from xbrowse_server.xbrowse_controls import load_project_variants_from_vcf
from datetime import datetime, date

import os
import sys

import signal, traceback
def quit_handler(signum,frame):
    traceback.print_stack()
signal.signal(signal.SIGQUIT,quit_handler)


class Command(BaseCommand):

    def add_arguments(self, parser):
        # django adds a --version arg by default, so remove it first
        for i, action in enumerate(parser._actions):
            if action.dest == "version":
                parser._handle_conflict_resolve(None, [('--version',parser._actions[i])])
                break

        parser.add_argument('project_id', metavar="project_id", help="Project ID for which to add the dataset", nargs=1)
        parser.add_argument('vcf_path', help="VCF file path", nargs=1)
        parser.add_argument('--version', help="Dataset version (eg. 1)", required=True)
        parser.add_argument('--datatype', help="Dataset type", choices=("WGS", "WES", "RNA"), required=True)
        parser.add_argument('-t', '--dry-run', help="Only test the command, don't run it yet.", action="store_true")


    def handle(self, *args, **options):
        # validate args
        project_id = options.get('project_id')[0]
        vcf_path = options.get('vcf_path')[0]
        version = options.get('version')
        datatype = options.get('datatype')

        if not os.path.isfile(vcf_path):
            sys.exit("ERROR: VCF file not found: %s" % vcf_path)

        try:
            version = str(float(version))
        except ValueError:
            sys.exit("ERROR: Version %s couldn't be converted to a decimal number." % version)

        try:
            project = Project.objects.get(project_id=project_id)
        except Exception as e:
            sys.exit("ERROR: Invalid project id: %s" % project_id)

        # get existing versions

        # type, version, vcf file path
        print(project_id)
        print(vcf_path)
        print(version)
        print(datatype)

        load_project_variants_from_vcf(project_id, vcf_files=vcf_files, version = version) #, start_from_chrom=start_from_chrom, end_with_chrom=end_with_chrom)

        print(date.strftime(datetime.now(), "%m/%d/%Y %H:%M:%S  -- load_project: " + project_id + " is done!"))

        # update the analysis status from 'Waiting for data' to 'Analysis in Progress'
        for f in Family.objects.filter(project__project_id=project_id):
            if f.analysis_status == 'Q':
                f.analysis_status = 'I'
                f.save()


        #[p.project_id for p in Project.objects.all().order_by('-last_accessed_date')]

        #xbrowse_controls.clean_project(project_id)
        #xbrowse_controls.load_project(project_id, force_annotations=force_annotations, start_from_chrom=options.get("start_from_chrom"))
