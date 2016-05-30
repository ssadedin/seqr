import json

from django.core.management.base import BaseCommand

from xbrowse_server.base.models import Project


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='*')

    def handle(self, *args, **options):

        # collect all the data first
        project = Project.objects.get(project_id=args[0])
        individuals = project.get_individuals()
        families = project.get_families()

        # populate data dict
        d = dict()

        # detailed individual data
        d['individuals'] = [indiv.to_dict() for indiv in individuals]

        d['families'] = [family.toJSON() for family in families]

        print json.dumps(d)