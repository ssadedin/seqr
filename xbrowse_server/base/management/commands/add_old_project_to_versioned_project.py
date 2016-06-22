from django.core.management.base import BaseCommand
from xbrowse_server.base.models import Project, ProjectCollaborator, Project, \
    Family, Individual, FamilyGroup, CausalVariant, ProjectTag, VariantTag, VariantNote, ProjectGeneList
from django.utils import timezone


class Command(BaseCommand):
    """Takes a project like my_project_WGS_v1 and copies the underlying data into a project like
    my_project - which will then have dataset version v1
    """

    def add_arguments(self, parser):
        parser.add_argument('-s', '--source-project', help="project id from which to take the data and metadata", required=True)
        parser.add_argument('-d', '--destination-project', help="project id to which to add the data", required=True)
        parser.add_argument('-n', '--destination-project-name', help="project name", required=True)
        parser.add_argument('-v', '--version', help="source project version", type=float, required=True)
        parser.add_argument('-t', '--type', help="source project type: WGS or WEX", choices=("WGS", "WEX"), required=True)

    def transfer_project(self, from_project_id, to_project_id, to_project_name, project_version, project_type):

        # create new project if it doesn't exist yet
        destination_project, created = Project.objects.get_or_create(
            project_id=to_project_id,
            project_name=to_project_name)

        if created:
            destination_project.created_date=timezone.now()
            destination_project.save()


        # Transfer Family and Individuals


        # Project
        # Family
        # Individual
        # VariantCallset

        #python2.7 -u manage.py add_individuals_to_project %(project_id)s " +  ("--ped %(ped)s" if ped else "--vcf %(vcf)s"),
        #python2.7 -u manage.py add_vcf_to_project %(project_id)s %(vcf)s",
        #"python2.7 -u manage.py add_project_to_phenotips %(project_id)s '%(project_name)s' ",
        #"python2.7 -u manage.py add_individuals_to_phenotips %(project_id)s --ped %(ped)s ",
        #"python2.7 -u manage.py generate_pedigree_images %(project_id)s",
        #"python2.7 -u manage.py load_project %(project_id)s" + (" --force-annotations --force-clean " if opts.force else ""),
        #"python2.7 -u manage.py load_project_datastore %(project_id)s",

        """
        The following models are transfered between projects.

        ProjectCollaborator => user = models.ForeignKey(User), project = models.ForeignKey('base.Project'), collaborator_type = models.CharField(max_length=20, choices=COLLABORATOR_TYPES, default="collaborator")
        Project => (private_reference_populations = models.ManyToManyField(ReferencePopulation), gene_lists = models.ManyToManyField('gene_lists.GeneList', through='ProjectGeneList'))
        Family => Project,
        FamilyGroup => Project   (families = models.ManyToManyField(Family))
        FamilyImageSlide => Family
        Cohort => Project  (individuals = models.ManyToManyField('base.Individual'), vcf_files, bam_file)
        Individual => Project, Family  # vcf_files = models.ManyToManyField(VCFFile, null=True, blank=True), bam_file = models.ForeignKey('datasets.BAMFile', null=True, blank=True)
        CausalVariant => Family
        ProjectTag => Project
        VariantTag => ProjectTag, Family
        VariantNote => User, Project
        """

        # Project
        from_project = Project.objects.get(project_id=from_project_id)
        to_project = Project.objects.get(project_id=to_project_id)
        to_project.description = from_project.description
        to_project.save()

        # ProjectCollaborator
        for c in ProjectCollaborator.objects.filter(project=from_project):
            ProjectCollaborator.objects.get_or_create(project=to_project, user=c.user, collaborator_type=c.collaborator_type)

        # Reference Populations
        for reference_population in from_project.private_reference_populations.all():
            print("Adding private reference population: " + reference_population.slug)
            to_project.private_reference_populations.add(reference_population)
            to_project.save()

        # Family
        to_family_id_to_family = {} # maps family_id to the to_family object
        for from_f in Family.objects.filter(project=from_project):
            try:
                to_f = Family.objects.get(project=to_project, family_id=from_f.family_id)
                print("Matched family ids %s (%s) to %s (%s)" % (from_f.family_id, from_f.short_description, to_f.family_id, to_f.short_description)) 
            except Exception as e:
                print("WARNING - skipping family: " + from_f.family_id + ": " + str(e))
                continue

            to_family_id_to_family[to_f.family_id] = to_f
            to_f.family_name = from_f.family_name
            to_f.short_description = from_f.short_description
            to_f.about_family_content = from_f.about_family_content
            to_f.pedigree_image_height = from_f.pedigree_image_height
            to_f.pedigree_image_width = from_f.pedigree_image_width
            to_f.analysis_status = from_f.analysis_status
            to_f.causal_inheritance_mode = from_f.causal_inheritance_mode
            to_f.relatedness_matrix_json = from_f.relatedness_matrix_json
            to_f.variant_stats_json = from_f.variant_stats_json
            to_f.has_before_load_qc_error = from_f.has_before_load_qc_error
            to_f.before_load_qc_json = from_f.before_load_qc_json
            to_f.has_after_load_qc_error = from_f.has_after_load_qc_error
            to_f.has_after_load_qc_error = from_f.has_after_load_qc_error
            to_f.after_load_qc_json = from_f.after_load_qc_json 
            to_f.save()

        # FamilyGroup
        for from_fg in FamilyGroup.objects.filter(project=from_project):
            FamilyGroup.objects.get_or_create(project=to_project, slug=from_fg.slug, name=from_fg.name, description=from_fg.description)

        # FamilyImageSlide
        #for from_family in Family.objects.filter(project=from_project):
        # TODO - need to iterate over image slides of from_family, and link to image slides of to_family
        #        FamilyImageSlide.objects.get_or_create(family=to_family, )
            
        
        # Cohort
        #cohorts = list(Cohort.objects.filter(project=project))
        #output_obj += cohorts

        # Individual
        for from_family in Family.objects.filter(project=from_project):
            if not from_family.family_id in to_family_id_to_family:
                print("WARNING - skipping family: " + from_family.family_id)
                continue

            to_family = to_family_id_to_family[from_family.family_id]
            for from_i in Individual.objects.filter(project=from_project, family=from_family):
                try:
                    to_i = Individual.objects.get(project=to_project, family=to_family, indiv_id=from_i.indiv_id)
                except:
                    print("WARNING - skipping individual: " + str(from_i.indiv_id) + " in family " + from_family.family_id) 
                    continue
                to_i.nickname = from_i.nickname
                to_i.other_notes = from_i.other_notes
                to_i.save()
            
            for from_v in CausalVariant.objects.filter(family=from_family):
                CausalVariant.objects.get_or_create(
                    family = to_family,
                    variant_type=from_v.variant_type,
                    xpos=from_v.xpos,
                    ref=from_v.ref,
                    alt=from_v.alt)

        for from_vn in VariantNote.objects.filter(project=from_project):
            if from_vn.family.family_id not in to_family_id_to_family:
                print("Skipping note: " + str(from_vn.toJSON()))
                continue
            to_family = to_family_id_to_family[from_vn.family.family_id]
            VariantNote.objects.get_or_create(
                project=to_project,
                family=to_family,
                user=from_vn.user,
                date_saved=from_vn.date_saved,
                note=from_vn.note,
                xpos=from_vn.xpos,
                ref=from_vn.ref,
                alt=from_vn.alt)
            
        for from_ptag in ProjectTag.objects.filter(project=from_project):
            to_ptag, created = ProjectTag.objects.get_or_create(project=to_project, tag=from_ptag.tag, title=from_ptag.title, color=from_ptag.color)
            for from_vtag in VariantTag.objects.filter(project_tag=from_ptag):
                if from_vtag.family.family_id not in to_family_id_to_family:
                    print("Skipping tag: " + str(from_vtag.xpos))
                    continue


                to_family = to_family_id_to_family[from_vtag.family.family_id]
                VariantTag.objects.get_or_create(
                    family=to_family,
                    project_tag=to_ptag,
                    xpos=from_vtag.xpos,
                    ref=from_vtag.ref,
                    alt=from_vtag.alt)


        for project_gene_list in ProjectGeneList.objects.filter(project=from_project):
            project_gene_list, created = ProjectGeneList.objects.get_or_create(project=to_project, gene_list=project_gene_list.gene_list)


    def handle(self, *args, **options):
        source_project_id = options["source"]
        destination_project_id = options["destination"]
        destination_project_name = options["destination_project_name"]
        project_version = options["version"]
        project_type = options["type"]

        print("Transferring data from project %s to %s" % (source_project_id, destination_project_id))
        if raw_input("Continue? [Y/n] ").lower() != 'y':
            return

        self.transfer_project(source_project_id, destination_project_id, destination_project_name, project_version, project_type)
