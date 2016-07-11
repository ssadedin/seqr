from collections import defaultdict
import datetime
import gzip
import json
import random
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from pretty_times import pretty
from xbrowse import Cohort as XCohort
from xbrowse import Family as XFamily
from xbrowse import FamilyGroup as XFamilyGroup
from xbrowse import Individual as XIndividual
from xbrowse import vcf_stuff
from xbrowse.core.variant_filters import get_default_variant_filters
from xbrowse_server.mall import get_datastore, get_coverage_store


class UserProfile(models.Model):

    user = models.OneToOneField(User)
    display_name = models.CharField(default="", blank=True, max_length=100)
    set_password_token = models.CharField(max_length=40, blank=True, default="")

    def __unicode__(self):
        return self.display_name if self.display_name else self.user.email

    def get_set_password_link(self):
        """
        Absolute URL of set password link, without leading slash
        """
        return 'set-password?token=' + self.set_password_token

User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])


class VCFFile(models.Model):

    file_path = models.CharField(max_length=500, default="", blank=True)

    def __unicode__(self):
        return self.file_path

    def path(self):
        return self.file_path

    def file_handle(self):
        if self.file_path.endswith('.gz'):
            return gzip.open(self.file_path)
        else:
            return open(self.file_path)

    def sample_id_list(self):
        return vcf_stuff.get_ids_from_vcf_path(self.path())


class ReferencePopulation(models.Model):
    slug = models.SlugField(default="", max_length=50)
    name = models.CharField(default="", max_length=100)
    file_type = models.CharField(default="", max_length=50)
    file_path = models.CharField(default="", max_length=500)
    is_public = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    def to_dict(self):
        return {
            'slug': self.slug,
            'name': self.name,
            'file_type': self.file_type,
            'file_path': self.file_path,
        }


COLLABORATOR_TYPES = (
    ('manager', 'Manager'),
    ('collaborator', 'Collaborator'),
)


class ProjectCollaborator(models.Model):
    user = models.ForeignKey(User)
    project = models.ForeignKey('base.Project')
    collaborator_type = models.CharField(max_length=20, choices=COLLABORATOR_TYPES, default="collaborator")


class Project(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SUBMITTED = "submitted"
    STATUS_ACCEPTED = "accepted"
    NEEDS_MORE_PHENOTYPES = "needs_more_phenotypes"
    ANALYSIS_IN_PROGRESS = "analysis_in_progress"
    DEPRECATED = "deprecated"

    PROJECT_STATUS_CHOICES = (
        (STATUS_DRAFT, STATUS_DRAFT),
        (STATUS_SUBMITTED, STATUS_SUBMITTED),
        (STATUS_ACCEPTED, STATUS_ACCEPTED),
        (NEEDS_MORE_PHENOTYPES, NEEDS_MORE_PHENOTYPES),
        (ANALYSIS_IN_PROGRESS, ANALYSIS_IN_PROGRESS),
        (DEPRECATED, DEPRECATED),
    )

    # these are auto populated from xbrowse
    project_id = models.SlugField(max_length=140, default="", blank=True, unique=True)

    # these are user specified; only exist in the server
    project_name = models.CharField(max_length=140, default="", blank=True)
    description = models.TextField(blank=True, default="")
    project_status = models.CharField(max_length=50, choices=PROJECT_STATUS_CHOICES, null=True)

    created_date = models.DateTimeField(null=True, blank=True)
    # this is the last time a project is "accessed" - currently set whenever one looks at the project home view
    # used so we can reload projects in order of last access
    last_accessed_date = models.DateTimeField(null=True, blank=True)

    private_reference_populations = models.ManyToManyField(ReferencePopulation, blank=True)
    gene_lists = models.ManyToManyField('gene_lists.GeneList', through='ProjectGeneList')

    default_control_cohort = models.CharField(max_length=100, default="", blank=True)

    # users
    collaborators = models.ManyToManyField(User, blank=True, through='ProjectCollaborator')
    is_public = models.BooleanField(default=False)

    def __unicode__(self):
        return self.project_name if self.project_name != "" else self.project_id

    # Authx
    def can_view(self, user):

        if self.is_public:
            return True
        elif user.is_staff:
            return True
        else:
            return ProjectCollaborator.objects.filter(project=self, user=user).exists()

    def can_edit(self, user):
        if user.is_staff:
            return True
        else:
            return ProjectCollaborator.objects.filter(project=self, user=user).exists()

    def can_admin(self, user):
        if user.is_staff or user.is_superuser:
            return True
        else:
            return ProjectCollaborator.objects.filter(project=self, user=user, collaborator_type="manager").exists()

    def set_as_manager(self, user):
        collab = ProjectCollaborator.objects.get_or_create(user=user, project=self)[0]
        collab.collaborator_type = 'manager'
        collab.save()

    def set_as_collaborator(self, user):
        ProjectCollaborator.objects.get_or_create(user=user, project=self)

    def get_managers(self):
        result = []
        for c in ProjectCollaborator.objects.filter(project=self, collaborator_type="manager"):
            try:
                result.append(c.user)
            except:
                print("WARNING: couldn't retrieve User object for %s" % str(c))

        return result

    def get_collaborators(self):
        result = []
        for c in ProjectCollaborator.objects.filter(project=self, collaborator_type="collaborator"):
            try:
                result.append(c.user)
            except:
                print("WARNING: couldn't retrieve User object for %s" % str(c))
        return result

    def get_users(self):
        result = []
        for c in ProjectCollaborator.objects.filter(project=self):
            try:
                result.append((c.user, c.collaborator_type))
            except:
                print("WARNING: couldn't retrieve User object for %s" % str(c))
        return result

    # data / samples
    def has_families(self):
        return self.family_set.filter().exists()

    def num_families(self):
        return self.family_set.filter().count()

    def get_families(self):
        fams = list(self.family_set.all())
        return sorted(fams, key=lambda item: (len(item.family_id), item.family_id))

    def get_active_families(self):
        return [f for f in self.get_families() if f.num_individuals() > 0]

    def has_cohorts(self):
        return self.cohort_set.all().exists()

    def get_cohorts(self):
        return self.cohort_set.all().order_by('cohort_id')

    def num_cohorts(self):
        return self.cohort_set.all().count()

    def has_family_groups(self):
        return self.familygroup_set.all().exists()

    def get_family_groups(self):
        return self.familygroup_set.all().order_by('slug')

    def num_family_groups(self):
        return self.familygroup_set.all().count()

    def families_by_vcf(self):
        families_by_vcf = {}  # map of vcf_file -> list of families from that VCF
        for family in self.family_set.all():
            vcf_files = family.get_vcf_files()
            for vcf_file in vcf_files:
                vcf = vcf_file.path()
                if vcf not in families_by_vcf:
                    families_by_vcf[vcf] = []
                families_by_vcf[vcf].append(family)
        return families_by_vcf

    def cohorts_by_vcf(self):
        by_vcf = {}  # map of vcf_file -> list of families from that VCF
        for cohort in self.cohort_set.all():
            vcf_files = cohort.get_vcf_files()
            for vcf_file in vcf_files:
                vcf = vcf_file.path()
                if vcf not in by_vcf:
                    by_vcf[vcf] = []
                by_vcf[vcf].append(cohort)

        return by_vcf

    # todo: rename to "custom" everywhere
    def get_private_reference_populations(self):
        return self.private_reference_populations.all()

    def private_reference_population_slugs(self):
        return [r.slug for r in self.private_reference_populations.all()]

    def get_reference_population_slugs(self):
        return settings.ANNOTATOR_REFERENCE_POPULATION_SLUGS + self.private_reference_population_slugs()

    def get_options_json(self):
        d = dict(project_id=self.project_id)

        d['reference_populations'] = (
            [{'slug': s['slug'], 'name': s['name']} for s in settings.ANNOTATOR_REFERENCE_POPULATIONS] +
            [{'slug': s.slug, 'name': s.name} for s in self.private_reference_populations.all()]
        )

        d['tags'] = [t.toJSON() for t in self.get_tags()]
        # this is an egrigious hack because get_default_variant_filters returns something other than VariantFilter objects
        filters = self.get_default_variant_filters()
        for f in filters:
            f['variant_filter'] = f['variant_filter'].toJSON()
        d['default_variant_filters'] = filters
        return json.dumps(d)

    def get_gene_lists(self):
        return list(self.gene_lists.all())

    def get_gene_list_map(self):
        d = defaultdict(list)
        for gene_list in self.get_gene_lists():
            for gene_id in gene_list.gene_id_list():
                d[gene_id].append(gene_list)
        return d

    def get_individuals(self):
        return self.individual_set.all().order_by('family__family_id')

    def num_individuals(self):
        return self.individual_set.count()
    
    def get_all_vcf_files(self):
        vcf_files = set()
        for indiv in self.get_individuals():
            for vcf_file in indiv.get_vcf_files():
                vcf_files.add(vcf_file)
        return vcf_files

    def get_xfamilygroup(self, only_combined=True):
        """
        Get an xbrowse FamilyGroup from the families in this project
        only_combined means only consider families that have at least one aff and unaff (with variant data)
        TODO: what is a better name for only_combined?!?!?
        """
        families = [f for f in self.get_families() if f.has_aff_and_unaff()]
        return XFamilyGroup([family.xfamily() for family in families])

    def is_loaded(self):
        for family in self.get_families():
            if not family.is_loaded():
                return False
        for cohort in self.get_cohorts():
            if cohort.is_loaded():
                return False
        return True

    def get_tags(self):
        return self.projecttag_set.all()
    
    def get_notes(self):
        return self.variantnote_set.all()
        
    def get_default_variant_filters(self):
        return get_default_variant_filters(self.get_reference_population_slugs())

    def set_accessed(self):
        self.last_accessed_date = timezone.now()
        self.save()


class ProjectGeneList(models.Model):
    gene_list = models.ForeignKey('gene_lists.GeneList')
    project = models.ForeignKey(Project)


ANALYSIS_STATUS_CHOICES = (
    ('S', ('Solved', 'fa-check-square-o')),
    ('S_kgfp', ('Solved - known gene for phenotype', 'fa-check-square-o')),
    ('S_kgdp', ('Solved - gene linked to different phenotype', 'fa-check-square-o')),
    ('S_ng', ('Solved - novel gene', 'fa-check-square-o')),
    ('Sc_kgfp', ('Strong candidate - known gene for phenotype', 'fa-check-square-o')),
    ('Sc_kgdp', ('Strong candidate - gene linked to different phenotype', 'fa-check-square-o')),
    ('Sc_ng', ('Strong candidate - novel gene', 'fa-check-square-o')),
    ('Rncc', ('Reviewed, no clear candidate', 'fa-check-square-o')),
    ('I', ('Analysis in Progress', 'fa-square-o')),
    ('Q', ('Waiting for data', 'fa-clock-o')),
)


class Family(models.Model):

    project = models.ForeignKey(Project, null=True, blank=True)
    family_id = models.CharField(max_length=140, default="", blank=True)
    family_name = models.CharField(max_length=140, default="", blank=True)  # human-readable family name

    short_description = models.CharField(max_length=500, default="", blank=True)

    about_family_content = models.TextField(default="", blank=True)
    analysis_summary_content = models.TextField(default="", blank=True)

    pedigree_image = models.ImageField(upload_to='pedigree_images', null=True, blank=True,
        height_field='pedigree_image_height', width_field='pedigree_image_width')
    pedigree_image_height = models.IntegerField(default=0, blank=True, null=True)
    pedigree_image_width = models.IntegerField(default=0, blank=True, null=True)

    analysis_status = models.CharField(max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="Q")
    analysis_status_date_saved = models.DateTimeField(null=True)
    analysis_status_saved_by = models.ForeignKey(User, null=True, blank=True)

    causal_inheritance_mode = models.CharField(max_length=20, default="unknown")

    # other postprocessing
    relatedness_matrix_json = models.TextField(default="", blank=True)
    variant_stats_json = models.TextField(default="", blank=True)

    # QC stuff
    has_before_load_qc_error = models.BooleanField(default=False)
    before_load_qc_json = models.TextField(default="", blank=True)

    has_after_load_qc_error = models.BooleanField(default=False)
    after_load_qc_json = models.TextField(default="", blank=True)

    def __unicode__(self):
        return self.family_name if self.family_name != "" else self.family_id

    def toJSON(self):
        """
        Yet another encoder. This is preferred from now on - does not include individual data
        """
        return {
            'project_id': self.project.project_id,
            'family_id': self.family_id,
            'family_name': self.family_name,
            'analysis_status': self.get_analysis_status_json(),
        }

    # REMOVE
    def get_json_obj(self):

        return {
            'project_id': self.project.project_id,
            'family_id': self.family_id,
            'individuals': [i.get_json_obj() for i in self.get_individuals()],
            'family_name': self.family_name,
            'about_family_content': self.about_family_content,
            'analysis_summary_content': self.analysis_summary_content,
            'data_status': self.get_analysis_status_json(),
        }

    def get_meta_json_obj(self):
        return {
            'project_id': self.project.project_id,
            'family_id': self.family_id,
            'about_family_content': self.about_family_content,
            'analysis_summary_content': self.analysis_summary_content,
            'analysis_status': self.get_analysis_status_json(),
        }

    def get_json(self):
        return json.dumps(self.get_json_obj())

    def get_individuals(self):
        return list(self.individual_set.all().order_by('indiv_id'))

    def individual_map(self):
        return {i.indiv_id: i.to_dict() for i in self.individual_set.all()}

    def indiv_id_list(self):
        """
        List of indiv ids for members in family
        """
        return [ i.indiv_id for i in self.individual_set.all()]

    def can_edit(self, user):
        return self.project.can_edit(user)

    def can_view(self, user):
        return self.project.can_view(user)

    def num_individuals(self):
        return self.individual_set.all().count()

    def xfamily(self):
        individuals = [i.xindividual() for i in self.get_individuals_with_variant_data()]
        return XFamily(self.family_id, individuals, project_id=self.project.project_id)

    def get_data_status(self):
        if not self.has_variant_data():
            return 'no_variants'
        elif not get_datastore(self.project.project_id).family_exists(self.project.project_id, self.family_id):
            return 'not_loaded'
        else:
            return get_datastore(self.project.project_id).get_family_status(self.project.project_id, self.family_id)

    def get_analysis_status_json(self):
        return {
            "user" : str(self.analysis_status_saved_by.email or self.analysis_status_saved_by.username) if self.analysis_status_saved_by is not None else None,
            "date_saved": pretty.date(self.analysis_status_date_saved) if self.analysis_status_date_saved is not None else None,
            "status": self.analysis_status,
            "family": self.family_name
        }

    def get_vcf_files(self):
        return list(set([v for i in self.individual_set.all() for v in i.vcf_files.all()]))

    #
    # Data for this family
    #

    def has_variant_data(self):
        """
        Can we do family variant analyses on this family
        So True if any of the individuals have any variant data
        """
        return any(individual.has_variant_data() for individual in self.get_individuals())

    def num_individuals_with_read_data(self):
        """Number of individuals in this family that have bams available"""
        return sum(1 for individual in self.get_individuals() if individual.has_read_data())

    def has_read_data(self):
        """Whether any individuals in this family have bam paths available"""
        return any(individual.has_variant_data() for individual in self.get_individuals())

    def all_individuals_have_variant_data(self):
        return all(individual.has_variant_data() for individual in self.get_individuals())

    def num_individuals_with_variant_data(self):
        return sum(i.has_variant_data() for i in self.get_individuals())

    def get_individuals_with_variant_data(self):
        return [i for i in self.get_individuals() if i.has_variant_data()]

    def indiv_ids_with_variant_data(self):
        return [i.indiv_id for i in self.get_individuals_with_variant_data()]

    def has_coverage_data(self):
        for individual in self.get_individuals():
            if not individual.coverage_file:
                return False
        return True

    def has_cnv_data(self):
        for individual in self.get_individuals():
            if not individual.exome_depth_file:
                return False
        return True

    def is_loaded(self):
        return self.get_data_status() in ['loaded', 'no_variants']

    def num_causal_variants(self):
        return CausalVariant.objects.filter(family=self).count()

    def has_aff_and_unaff(self):
        """
        Does this family contain at least one affected and at least one unaffected individual? (With phenotype data)
        """
        indivs = self.indiv_ids_with_variant_data()
        return any(i for i in indivs if i.affected == 'A') and any(i for i in indivs if i.affected == 'N')

    def has_data(self, data_key):
        """
        Is data for data_key available and fully loaded for this family?
        """
        if data_key == 'variation':
            return self.has_variant_data() and self.get_data_status() == 'loaded'
        elif data_key == 'exome_coverage':
            if self.has_coverage_data() is False:
                return False
            sample_ids = [indiv.get_coverage_store_id() for indiv in self.get_individuals()]
            statuses = set(get_coverage_store().get_sample_statuses(sample_ids).values())

            # must be at least one fully loaded
            if 'loaded' not in statuses:
                return False

            # "there are no statuses other than loaded and None"
            return len(statuses.union({'loaded', None})) == 2

    def get_data_summary(self):
        data_summary = {
            'data_available': []
        }
        if self.has_coverage_data():
            data_summary['data_available'].append('callability')
        if self.has_variant_data():
            data_summary['data_available'].append('variants')
        if self.has_cnv_data():
            data_summary['data_available'].append('cnv')
        return data_summary

    def get_image_slides(self):
        return [{'url': i.image.url, 'caption': i.caption} for i in self.familyimageslide_set.all()]
    
    def get_tags(self):
        return self.project.get_variant_tags(family=self)


class FamilyImageSlide(models.Model):
    family = models.ForeignKey(Family)
    image = models.ImageField(upload_to='family_image_slides', null=True, blank=True)
    order = models.FloatField(default=0.0)
    caption = models.CharField(max_length=300, default="", blank=True)


class Cohort(models.Model):
    project = models.ForeignKey(Project, null=True, blank=True)
    cohort_id = models.CharField(max_length=140, default="", blank=True)
    display_name = models.CharField(max_length=140, default="", blank=True)
    short_description = models.CharField(max_length=140, default="", blank=True)

    individuals = models.ManyToManyField('base.Individual')

    variant_stats_json = models.TextField(default="", blank=True)

    def __unicode__(self):
        return self.display_name if self.display_name != "" else self.cohort_id

    def get_individuals(self):
        return list(self.individuals.all().order_by('indiv_id'))

    # REMOVE
    def get_json_obj(self):

        return {
            'project_id': self.project.project_id,
            'cohort_id': self.cohort_id,
            'individuals': [i.get_json_obj() for i in self.individuals.all()],
        }

    def get_json(self):
        return json.dumps(self.get_json_obj())

    def individual_map(self):
        return {i.indiv_id: i.to_dict() for i in self.individuals.all()}

    def indiv_id_list(self):
        """
        List of indiv ids for members in family
        """
        return [ i.indiv_id for i in self.individuals.all() ]

    def can_edit(self, user):

        return self.project.can_edit(user)

    def can_view(self, user):
        return self.project.can_view(user)

    def num_individuals(self):
        return self.individuals.all().count()

    def xfamily(self):
        individuals = [i.xindividual() for i in self.individuals.all()]
        return XFamily(self.cohort_id, individuals, project_id=self.project.project_id)

    def xcohort(self):
        individuals = [i.xindividual() for i in self.individuals.all()]
        return XCohort(self.cohort_id, individuals, project_id=self.project.project_id)

    def get_vcf_files(self):
        vcf_files = { f for i in self.individuals.all() for f in i.get_vcf_files() }
        return list(vcf_files)

    #
    # Data lookups
    #

    def has_variant_data(self):
        """
        Can we do cohort variant analyses
        So all individuals must have variant data
        """
        return all(individual.has_variant_data() for individual in self.get_individuals())

    def get_data_status(self):
        if not self.has_variant_data():
            return 'no_variants'
        elif not get_datastore(self.project.project_id).family_exists(self.project.project_id, self.cohort_id):
            return 'not_loaded'
        else:
            return get_datastore(self.project.project_id).get_family_status(self.project.project_id, self.cohort_id)

    def is_loaded(self):
        return self.get_data_status() in ['loaded', 'no_variants']


class Individual(models.Model):
    SEX_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('U', 'Unknown'),
    )


    AFFECTED_CHOICES = (
        ('A', 'Affected'),
        ('N', 'Unaffected'),
        ('U', 'Unknown'),
    )

    COVERAGE_STATUS_CHOICES = (
        ('S', 'In Sequencing'),
        ('I', 'Interim'),
        ('C', 'Complete'),
        ('A', 'Abandoned'),
    )

    # global unique id for this individual (<date>_<time_with_millisec>_<indiv_id>)
    guid = models.SlugField(max_length=165, unique=True, db_index=True)
    indiv_id = models.SlugField(max_length=140, default="", blank=True, db_index=True)
    family = models.ForeignKey(Family, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, blank=True)

    sex = models.CharField(max_length=1, choices=SEX_CHOICES, default='U')
    affected = models.CharField(max_length=1, choices=AFFECTED_CHOICES, default='U')
    maternal_id = models.SlugField(max_length=140, default="", blank=True)
    paternal_id = models.SlugField(max_length=140, default="", blank=True)

    nickname = models.CharField(max_length=140, default="", blank=True)
    other_notes = models.TextField(default="", blank=True, null=True)

    mean_target_coverage = models.FloatField(null=True, blank=True)
    coverage_status = models.CharField(max_length=1, choices=COVERAGE_STATUS_CHOICES, default='S')

    coverage_file = models.CharField(max_length=200, default="", blank=True)
    exome_depth_file = models.CharField(max_length=200, default="", blank=True)
    vcf_files = models.ManyToManyField(VCFFile, blank=True)
    bam_file_path = models.CharField(max_length=1000, default="", blank=True)

    phenotips_id = models.SlugField(max_length=165, default="", blank=True)  # PhenoTips 'external id'
    
    vcf_id = models.CharField(max_length=40, default="", blank=True)  # ID in VCF files, if different

    def __unicode__(self):
        ret = self.indiv_id
        if self.nickname:
            ret += " (%s)" % self.nickname
        return ret

    def save(self, *args, **kwargs):
        """Override the default save method so that guid is set whenever a new Individual record is created"""

        if self.pk is None:  # this means the model is being created
            # generate the global unique id for this individual (<date>_<time>_<microsec>_<indiv_id>)
            self.guid = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f" + "_%s" % self.indiv_id)
            print("Adding new-style guid: " + self.guid)
        elif self.guid is None:  # this means the model was previously created, but guid is not yet set
            self.guid = self.indiv_id
            print("Adding old-style guid: " + self.guid)

        super(Individual, self).save(*args, **kwargs)

    def get_family_id(self):
        if self.family:
            return self.family.family_id
        else:
            return None

    def has_variant_data(self):
        return self.vcf_files.all().count() > 0

    def has_read_data(self):
        return bool(self.bam_file_path)

    def sex_display(self):
        return dict(Individual.SEX_CHOICES).get(self.sex, '')

    def affected_status_display(self):  # TODO: rename this to affected_display...that was dumb
        return dict(Individual.AFFECTED_CHOICES).get(self.affected, '')

    def to_dict(self):
        """

        """
        return {
            'indiv_id': str(self.indiv_id),
            'project_id': str(self.project.project_id),
            'family_id': str(self.family.family_id) if self.family else "",
            'nickname': str(self.nickname),
            'sex': str(self.sex),
            'affected': str(self.affected),
            'maternal_id': str(self.maternal_id),
            'paternal_id': str(self.paternal_id),
            'has_variants': self.has_variant_data(),  # can we remove?
            'other_notes': self.other_notes,
        }

    def get_json_obj(self):
        return {
            'project_id': self.project.project_id,
            'indiv_id': self.indiv_id,
            'sex': self.sex,
            'affected': self.affected,
            'nickname': self.nickname,
            'has_variant_data': self.has_variant_data(),
            'has_bam_file_path': bool(self.bam_file_path),
            'family_id': self.get_family_id(),
        }

    def get_json(self):
        return json.dumps(self.get_json_obj())

    def xindividual(self):

        sex = 'unknown'
        if self.sex == 'M':
            sex = 'male'
        elif self.sex == 'F':
            sex = 'female'

        affected_status = 'unknown'
        if self.affected == 'A':
            affected_status = 'affected'
        elif self.affected == 'N':
            affected_status = 'unaffected'

        paternal_id = self.paternal_id
        if not Individual.objects.filter(indiv_id=paternal_id, project=self.project).exists():
            paternal_id = '.'

        maternal_id = self.maternal_id
        if not Individual.objects.filter(indiv_id=maternal_id, project=self.project).exists():
            maternal_id = '.'

        return XIndividual(
            self.indiv_id,
            project_id=self.project_id,
            family_id=self.family_id,
            paternal_id=paternal_id,
            maternal_id=maternal_id,
            sex=sex,
            affected_status=affected_status
        )

    def from_xindividual(self, xindividual):
        """
        Load other fields from xindiviudal object
        Ignores project_id, family_id, indiv_id - those should already be set
        """
        self.paternal_id = xindividual.paternal_id
        self.maternal_id = xindividual.maternal_id
        self.affected = 'A' if xindividual.affected_status == 'affected' else ('N' if xindividual.affected_status == 'unaffected' else 'U')
        self.sex = 'M' if xindividual.sex == 'male' else ('F' if xindividual.sex == 'female' else 'U')
        self.save()

    def get_vcf_files(self):
        """
        List of VCF file (paths) that this individual is in
        """
        return list(self.vcf_files.all())

    def get_cohorts(self):
        """
        List of Cohorts (if any) that this sample belongs to
        """
        return self.cohort_set.all()


    def sample_display(self):
        if self.vcf_files.count() == 0:
            return "No variant data"
        else:
            s = "%d sample" % self.vcf_files.count()
            if self.vcf_files.count() > 1:
                s += "s"
            return s

    def get_notes_plaintext(self):
        return self.other_notes if self.other_notes else ""

    def is_loaded(self):
        return self.family.is_loaded()

    def has_coverage_data(self):
        return bool(self.coverage_file)

    # TODO: rename this to something more generic
    def get_coverage_store_id(self):
        return str(self.pk)

    def data(self):
        return {
            'exome_coverage': self.has_coverage_data(),
            'variants': self.has_variant_data(),
        }


class Dataset(models.Model):
    """Parent class for dataset models"""

    guid = models.SlugField(max_length=165, unique=True, db_index=True)
    version = models.CharField(max_length=20, db_index=True)

    added_date = models.DateTimeField(null=True, blank=True)
    original_path = models.TextField(null=True, blank=True)  # file or url from which the data was loaded

    SEQUENCING_TYPE_CHOICES = (
        ('WES', 'Exome'),
        ('WGS', 'Whole Genome'),
    )

    sequencing_type = models.CharField(max_length=3, choices=SEQUENCING_TYPE_CHOICES)


class SequencedSampleInfo(models.Model):
    """Sequenced sample information that's independent of sample version, but does depend on sequencing_type"""

    STATUS_CHOICES = (
        ('s', 'In Sequencing')  # not yet sequenced
        ('i', 'Interim'),       # needs additional sequencing to reach expected (95x) coverage
        ('a', 'Abandoned'),     # sample failed sequencing
        ('c', 'Complete'),      # sample sequencing complete and achieved expected coverage
    )

    status = models.CharField(max_length=3, choices=STATUS_CHOICES, default='s')


class VariantCallsetSample(models.Model):
    """Variant callset sample. One record per sample in a callset."""

    individual = models.ForeignKey('Individual')
    sample_info = models.ForeignKey('SequencedSampleInfo')
    variant_callset = models.ForeignKey('VariantCallset')


class VariantCallset(Dataset):
    """Represents a variant callset. One record per callset."""
    individuals = models.ManyToManyField(Individual, through='VariantCallsetSample')



class FamilySearchFlag(models.Model):

    FLAG_TYPE_CHOICES = (
        ('C', 'Likely causal'),
        ('R', 'Flag for review'),
        ('N', 'Other note'),
    )

    user = models.ForeignKey(User, null=True, blank=True)
    family = models.ForeignKey(Family, null=True, blank=True)

    xpos = models.BigIntegerField()
    ref = models.TextField()
    alt = models.TextField()

    flag_type = models.CharField(max_length=1, choices=FLAG_TYPE_CHOICES)
    suggested_inheritance = models.SlugField(max_length=40, default="")

    # REMOVE
    search_spec_json = models.TextField(default="", blank=True)
    date_saved = models.DateTimeField()
    note = models.TextField(default="", blank=True)

    def search_spec(self):
        return json.loads(self.search_spec_json)

    def to_dict(self):
        return {
            'username': self.user.username,
            'display_name': self.user.profile.display_name,
            'project_id': self.family.project.project_id,
            'family_id': self.family.family_id,
            'xpos': self.xpos,
            'ref': self.ref,
            'alt': self.alt,
            'flag_type': self.flag_type,
            'flag_type_display': dict(FamilySearchFlag.FLAG_TYPE_CHOICES).get(self.flag_type),
            'search_spec_json': self.search_spec_json,
            'note': self.note,
            'date_saved': pretty.date(self.date_saved) if self.date_saved is not None else '',
        }

    def to_json(self):
        return json.dumps(self.to_dict())

    def x_variant(self):
        v = get_datastore(self.family.project.project_id).get_single_variant(self.family.project.project_id, self.family.family_id, self.xpos, self.ref, self.alt)
        return v


class FamilyGroup(models.Model):
    slug = models.SlugField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField()
    project = models.ForeignKey(Project)
    families = models.ManyToManyField(Family)

    def __unicode__(self):
        return self.name

    def get_families(self):
        return self.families.all().order_by('family_id')

    def num_families(self):
        return self.families.count()

    def xfamilygroup(self):
        return XFamilyGroup([family.xfamily() for family in self.get_families()])

    def toJSON(self):
        return {
            'project_id': self.project.project_id,
            'slug': self.slug,
            'name': self.name,
            'description': self.description,
            'families': {family.family_id: family.get_json_obj() for family in self.get_families()}
        }


class ProjectTag(models.Model):
    project = models.ForeignKey(Project)
    tag = models.CharField(max_length=50)
    title = models.CharField(max_length=300, default="")
    color = models.CharField(max_length=10, default="")

    def save(self, *args, **kwargs):
        if self.color == '':
            self.color = random.choice([
                '#a6cee3',
                '#1f78b4',
                '#b2df8a',
                '#33a02c',
                '#fdbf6f',
                '#ff7f00',
                '#ff0000',
                '#cab2d6',
                '#6a3d9a',
                '#8F754F',
                '#383838',
            ])
        super(ProjectTag, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.title if self.title else self.tag

    def toJSON(self):
        return {
            'project': self.project.project_id,
            'tag': self.tag,
            'title': self.title,
            'color': self.color,
        }

    def get_variant_tags(self, family=None):
        if family is not None:
            return self.varianttag_set.filter(family=family)
        else:
            return self.varianttag_set.all()


class CausalVariant(models.Model):
    family = models.ForeignKey(Family, null=True)
    variant_type = models.CharField(max_length=10, default="")
    xpos = models.BigIntegerField(null=True)
    ref = models.TextField(null=True)
    alt = models.TextField(null=True)


class VariantTag(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    date_saved = models.DateTimeField(null=True)

    project_tag = models.ForeignKey(ProjectTag)
    family = models.ForeignKey(Family, null=True)
    xpos = models.BigIntegerField()
    ref = models.TextField()
    alt = models.TextField()

    search_url = models.TextField(null=True)


    def toJSON(self):
        d = {
            'user': {
                'username': self.user.username,
                'display_name': str(self.user.profile),
             } if self.user else None,
            'date_saved': pretty.date(self.date_saved) if self.date_saved is not None else '',

            'project': self.project_tag.project.project_id,
            'tag': self.project_tag.tag,
            'title': self.project_tag.title,
            'color': self.project_tag.color,
            'xpos': self.xpos,
            'ref': self.ref,
            'alt': self.alt,
            'search_url': self.search_url,
        }

        if self.family:
            d['family'] = self.family.family_id

        return d


class VariantNote(models.Model):
    project = models.ForeignKey(Project)
    note = models.TextField(default="", blank=True)

    xpos = models.BigIntegerField()
    ref = models.TextField()
    alt = models.TextField()

    # these are for context - if note was saved for a family or an individual
    family = models.ForeignKey(Family, null=True, blank=True)
    individual = models.ForeignKey(Individual, null=True, blank=True)

    user = models.ForeignKey(User, null=True, blank=True)
    date_saved = models.DateTimeField()
    search_url = models.TextField(null=True)


    def get_context(self):
        if self.family:
            return 'family', self.family
        elif self.individual:
            return 'individual', self.individual
        else:
            return 'project', self.project

    def toJSON(self):
        d = {
            'user': {
                'username': self.user.username,
                'display_name': str(self.user.profile),
            } if self.user else None,
            'date_saved': pretty.date(self.date_saved) if self.date_saved is not None else '',

            'project_id': self.project.project_id,
            'note_id' : self.id,
            'note': self.note,

            'xpos': self.xpos,
            'ref': self.ref,
            'alt': self.alt,

            'family_id': None,
            'individual_id': None,
        }
        context, obj = self.get_context()
        if context == 'family':
            d['family_id'] = obj.family_id
        elif context == 'individual':
            d['individual_id'] = obj.indiv_id

        return d


class AnalysisStatus(models.Model):
    user = models.ForeignKey(User, null=True, blank=True)
    date_saved = models.DateTimeField(null=True)
    family = models.ForeignKey(Family)
    status = models.CharField(max_length=10, choices=ANALYSIS_STATUS_CHOICES, default="I")

