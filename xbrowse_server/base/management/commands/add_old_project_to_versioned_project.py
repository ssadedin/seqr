from django.core.management.base import BaseCommand
from xbrowse_server.base.models import Project, Family, Individual, FamilyGroup, ProjectTag, VariantTag, VariantNote, \
    VariantCallset, VariantCallsetSample, ProjectGeneList
from django.utils import timezone
from xbrowse_server.phenotips.utilities import convert_external_id_to_internal_id, create_user_in_phenotips, \
    get_uname_pwd_for_project, add_user_to_phenotips_patient, PatientNotFoundError, create_patient_record

class Command(BaseCommand):
    """Takes a project like my_project_WGS_v1 and copies the underlying data into a project like
    my_project - which will then have dataset version v1
    """

    def add_arguments(self, parser):
        parser.add_argument('-s', '--source-project', help="project id from which to take the data and metadata", required=True)
        parser.add_argument('-d', '--destination-project', help="project id to which to add the data", required=True)
        parser.add_argument('-n', '--destination-project-name', help="project name", required=True)
        #parser.add_argument('-v', '--version', help="source project version", type=float, required=True)
        parser.add_argument('-t', '--type', help="source project type: WGS or WEX", choices=("WGS", "WEX"), required=True)


    def add_project(self, from_project_id, to_project_id, to_project_name, project_type):
        from_project = Project.objects.get(project_id=from_project_id)

        # create new project if it doesn't exist yet
        to_project, created = Project.objects.get_or_create(
            project_id=to_project_id)
        to_project.project_name = to_project_name
        if created:
            print("Created project: %s" % to_project.project_id)
            to_project.created_date=timezone.now()
        else:
            print("Retrieved project: %s" % to_project.project_id)

        if from_project.description:
            print("Setting description to: " + from_project.description)
            to_project.description = from_project.description

        if from_project.project_status:
            print("Setting project_status to: " + from_project.project_status)
            to_project.project_status = from_project.project_status

        to_project.supports_versions = True  # enable versions
        to_project.save()


        # ProjectCollaborator
        #for c in ProjectCollaborator.objects.filter(project=from_project):
        #    ProjectCollaborator.objects.get_or_create(project=to_project, user=c.user, collaborator_type=c.collaborator_type)

        # Reference Populations - add ones that haven't been added previously
        for from_project_ref_pop in from_project.private_reference_populations.all():
            if any([1 for to_project_ref_pop in to_project.private_reference_populations.all() if to_project_ref_pop.id == from_project_ref_pop.id]):
                continue

            print("Adding private reference population: " + from_project_ref_pop.slug)
            to_project.private_reference_populations.add(from_project_ref_pop)
            to_project.save()

        # GeneLists
        for from_project_gene_list in from_project.gene_lists.all():
            if any([1 for to_project_gene_list in to_project.gene_lists.all() if to_project_gene_list.id == from_project_gene_list.id]):
                continue  # skip if this gene list has already been added

            project_gene_list, created = ProjectGeneList.objects.get_or_create(project=to_project, gene_list=from_project_gene_list)
            if created:
                print("Added gene list: " + from_project_gene_list.slug)

                #project_gene_list.save()

        # Family
        to_family_id_to_family = {}  # maps family_id to the to_family object
        for from_f in Family.objects.filter(project=from_project):
            to_f, created = Family.objects.get_or_create(project=to_project, family_id=from_f.family_id)

            to_family_id_to_family[to_f.family_id] = to_f

            if created:
                print("Created family %s" % (to_f.family_id,))

            to_f.family_name = from_f.family_name
            if from_f.short_description: to_f.short_description = from_f.short_description

            if from_f.about_family_content: to_f.about_family_content = from_f.about_family_content
            if from_f.analysis_summary_content: to_f.analysis_summary_content = from_f.analysis_summary_content

            if from_f.pedigree_image:
                to_f.pedigree_imate = from_f.pedigree_image
                to_f.pedigree_image_height = from_f.pedigree_image_height
                to_f.pedigree_image_width = from_f.pedigree_image_width

            if from_f.analysis_status != "Q" or from_f.analysis_status_date_saved:
                to_f.analysis_status = from_f.analysis_status
                to_f.analysis_status_date_saved = from_f.analysis_status_date_saved
                to_f.analysis_status_saved_by = from_f.analysis_status_saved_by

            if from_f.causal_inheritance_mode != "unknown":
                to_f.causal_inheritance_mode = from_f.causal_inheritance_mode

            to_f.save()

        # FamilyGroup
        for from_fg in FamilyGroup.objects.filter(project=from_project):
            FamilyGroup.objects.get_or_create(project=to_project, slug=from_fg.slug, name=from_fg.name, description=from_fg.description)

        # Create PhenoTips username for this project
        #create_new_phenotips_account = (raw_input("Create new PhenoTips account for %s? [Y/n] " % to_project_id).lower() == 'y')
        #if create_new_phenotips_account:
        #    create_user_in_phenotips(to_project_id, to_project_name)

        # Datasets
        to_dataset, created = VariantCallset.objects.get_or_create(dataset_id=to_project_id, sequencing_type=project_type)
        if created:
            print("Created new VariantCallset: " + to_project_id)

        #to_dataset.mongo_gene_search_coll = ""

        # Individuals
        vcf_files = set()
        for from_family in Family.objects.filter(project=from_project):
            to_family = to_family_id_to_family[from_family.family_id]
            for from_i in Individual.objects.filter(project=from_project, family=from_family):
                try:
                    to_i = Individual.objects.get(project=to_project, family=to_family, indiv_id=from_i.indiv_id)
                except Exception as e:
                    to_i = Individual.objects.create(project=to_project, family=to_family, indiv_id=from_i.indiv_id)

                to_i.indiv_id = from_i.indiv_id
                to_i.family = to_family
                to_i.project = to_project

                to_i.phenotips_id = from_i.phenotips_id
                to_i.vcf_id = from_i.vcf_id

                to_i.sex = from_i.sex
                to_i.affected = from_i.affected
                to_i.maternal_id = from_i.maternal_id
                to_i.paternal_id = from_i.paternal_id

                to_i.nickname = from_i.nickname
                to_i.other_notes = from_i.other_notes

                to_i.mean_target_coverage = from_i.mean_target_coverage
                to_i.coverage_status = from_i.coverage_status

                for vcf_file in from_i.vcf_files.all():
                    vcf_files.add(vcf_file.file_path)

                #to_i.vcf_files = from_i.vcf_files...
                to_i.bam_file_path = from_i.bam_file_path
                to_i.save()


                # set up permissions for the associated record in PhenoTips
                uname, pwd = get_uname_pwd_for_project(to_project_id, read_only=False)
                try:
                    #patient_id = convert_external_id_to_internal_id(to_i.phenotips_id, uname, pwd)
                    pass
                except PatientNotFoundError as e:
                    print("%s: Creating phenotips patient for phenotips_id: %s " % (to_project_id, to_i.phenotips_id))
                    create_patient_record(to_i.phenotips_id, to_project_id, patient_details={'gender': to_i.sex})
                else:
                    # add manager user
                    #add_user_to_phenotips_patient(uname, patient_id, read_only=False)
                    # add read-only user
                    uname, pwd = get_uname_pwd_for_project(to_project_id, read_only=True)
                    #add_user_to_phenotips_patient(uname, patient_id, read_only=True)

                # create dataset sample record
                variant_callset, created = VariantCallsetSample.objects.get_or_create(variant_callset=to_dataset, individual=to_i)
                if created:
                    print("Created new VariantCallsetSample for: " + to_i.indiv_id)
                variant_callset.mean_target_coverage = to_i.mean_target_coverage
                variant_callset.coverage_status = to_i.coverage_status

                variant_callset.bam_file_path = to_i.bam_file_path

        # variant tags
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
                to_family = to_family_id_to_family[from_vtag.family.family_id]
                VariantTag.objects.get_or_create(
                    family=to_family,
                    project_tag=to_ptag,
                    xpos=from_vtag.xpos,
                    ref=from_vtag.ref,
                    alt=from_vtag.alt)



        # FamilyImageSlide
        #for from_family in Family.objects.filter(project=from_project):
        # TODO - need to iterate over image slides of from_family, and link to image slides of to_family
        #        FamilyImageSlide.objects.get_or_create(family=to_family, )

        # Cohort
        #cohorts = list(Cohort.objects.filter(project=project))
        #output_obj += cohorts

    def handle(self, *args, **options):
        source_project_id = options["source_project"]
        destination_project_id = options["destination_project"]
        destination_project_name = options["destination_project_name"]
        #project_version = options["version"]
        project_type = options["type"]

        print("Transferring data from project %s to %s" % (source_project_id, destination_project_id))
        if raw_input("Continue? [Y/n] ").lower() != 'y':
            return

        self.add_project(source_project_id, destination_project_id, destination_project_name, project_type)
