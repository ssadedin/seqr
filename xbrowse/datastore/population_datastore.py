from xbrowse.datastore import MongoDatastore
from xbrowse import Individual, Cohort
from xbrowse.parsers import vcf_stuff


class PopulationDatastore(MongoDatastore):

    def __init__(self, db, annotator, custom_population_store, cohorts):
        custom_populations_map = {c['slug']: c['custom_populations'] for c in cohorts if c.get('custom_populations')}
        super(PopulationDatastore, self).__init__(
            db,
            annotator=annotator,
            custom_population_store=custom_population_store,
            custom_populations_map=custom_populations_map,
        )
        self.cohorts = cohorts

    def get_control_cohort(self, population):
        indiv_id_list = self.get_individuals_for_family(population, 'control_cohort')
        individuals = [Individual(indiv_id, affected_status='affected') for indiv_id in indiv_id_list]
        cohort = Cohort('control_cohort', individuals, project_id=population)
        return cohort

    def get_control_cohort_size(self, population):
        return len(self.get_individuals_for_family(population, 'control_cohort'))