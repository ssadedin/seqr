import datetime
import pymongo
import sys
from xbrowse import Variant
from population_frequency_store import PopulationFrequencyStore
from xbrowse.annotation import vep_annotations
from xbrowse.core import constants
import vcf


class VariantAnnotator():

    def __init__(self, settings_module, custom_annotator=None):
        self._db = pymongo.MongoClient()[settings_module.db_name]
        self._population_frequency_store = PopulationFrequencyStore(
            db_conn=self._db,
            reference_populations=settings_module.reference_populations,
        )
        self._custom_annotator = custom_annotator
        self.reference_populations = settings_module.reference_populations
        self.reference_population_slugs = [pop['slug'] for pop in settings_module.reference_populations]

    def _ensure_indices(self):
        self._db.variants.ensure_index([('xpos', 1), ('ref', 1), ('alt', 1)])

    def _clear(self):
        self._db.drop_collection('variants')
        self._db.drop_collection('vcf_files')
        self._ensure_indices()

    def get_annotator_datastore(self):
        """Returns the mongo database object for the xbrowse_annotator database. This database contains the
        'variants' and 'pop_variants' collections."""
        return self._db

    def get_population_frequency_store(self):
        """Returns the PopulationFrequencyStore used to store the system-wide reference populations available on all
        projects.
        """
        return self._population_frequency_store

    def load(self):
        self._clear()
        self._ensure_indices()
        self._population_frequency_store.load()

    def get_variant(self, xpos, ref, alt):
        variant = Variant(xpos, ref, alt)
        self.annotate_variant(variant)
        return variant

    def get_annotation(self, xpos, ref, alt, populations=None):
        doc = self._db.variants.find_one({'xpos': xpos, 'ref': ref, 'alt': alt})
        if doc is None:
            raise ValueError("Could not find annotations for variant: " + str((xpos, ref, alt)))
        annotation = doc['annotation']
        if populations is None:
            populations = self.reference_population_slugs
        if populations is not None:
            freqs = {}
            for p in populations:
                freqs[p] = annotation['freqs'].get(p, 0.0)
            annotation['freqs'] = freqs
        return annotation

    def add_preannotated_vcf_file(self, vcf_file_path, force=False):
        """
        Add the variants in vcf_file_path to annotator
        Convenience wrapper around add_variants_to_annotator
        """
        if not force and self._db.vcf_files.find_one({'vcf_file_path': vcf_file_path}):
            print "VCF %(vcf_file_path)s already loaded into db.variants cache" % locals()
            return

        r = vcf.VCFReader(filename=vcf_file_path)
        if "CSQ" not in r.infos:
            raise ValueError("ERROR: CSQ field not found in %s. Was this VCF annotated with VEP?" % vcf_file_path)

        expected_csq_fields = set("Allele|Gene|Feature|Feature_type|Consequence|cDNA_position|CDS_position|Protein_position|Amino_acids|Codons|Existing_variation|ALLELE_NUM|DISTANCE|STRAND|SYMBOL|SYMBOL_SOURCE|HGNC_ID|BIOTYPE|CANONICAL|TSL|CCDS|ENSP|SWISSPROT|TREMBL|UNIPARC|SIFT|PolyPhen|EXON|INTRON|DOMAINS|HGVSc|HGVSp|MOTIF_NAME|MOTIF_POS|HIGH_INF_POS|MOTIF_SCORE_CHANGE|LoF_info|LoF_flags|LoF_filter|LoF|Polyphen2_HVAR_pred|CADD_phred|MutationTaster_pred|MetaSVM_pred|SIFT_pred|FATHMM_pred".split("|"))
        actual_csq_fields_string = str(r.infos["CSQ"].desc).split("Format:")[1].strip()
        actual_csq_fields = set(actual_csq_fields_string.split("|"))
        if len(expected_csq_fields - actual_csq_fields) > 0:
            raise ValueError("ERROR: VEP did not add all expected CSQ fields to the VCF. The VCF's CSQ = %s and is missing these fields: %s" % (actual_csq_fields_string, expected_csq_fields - actual_csq_fields))

        print("Loading pre-annotated VCF file: %s into db.variants cache" % vcf_file_path)
        for variant, vep_annotation in vep_annotations.parse_vep_annotations_from_vcf(open(vcf_file_path)):
            variant_t = variant.unique_tuple()

            annotation = {
                'vep_annotation': vep_annotation,
                'freqs': self._population_frequency_store.get_frequencies(variant_t[0], variant_t[1], variant_t[2]),
                }

            add_convenience_annotations(annotation)

            if self._custom_annotator:
                custom_annotations = self._custom_annotator.get_annotations_for_variants([variant_t])
                annotation.update(custom_annotations[variant_t])

            self._db.variants.update(
                {
                    'xpos': variant_t[0],
                    'ref': variant_t[1],
                    'alt': variant_t[2]
                }, {
                    '$set': {'annotation': annotation}
                }, upsert=True)

        self._db.vcf_files.update({'vcf_file_path': vcf_file_path},
            {'vcf_file_path': vcf_file_path, 'date_added': datetime.datetime.utcnow()}, upsert=True)

    def _get_missing_annotations(self, variant_t_list):
        ret = []
        for variant_t in variant_t_list:
            if not self._db.variants.find_one(
                {'xpos': variant_t[0],
                 'ref': variant_t[1],
                 'alt': variant_t[2]}):
                ret.append(variant_t)
        return ret

    def annotate_variant(self, variant, populations=None):
        try:
            annotation = self.get_annotation(variant.xpos, variant.ref, variant.alt, populations)
        except ValueError, e:
            sys.stderr.write("WARNING: " + str(e) + "\n")
            variant.annotation = None
            return

        variant.annotation = annotation

        # todo: gotta remove one
        # ...or actually maybe both
        variant.gene_ids = [g for g in annotation['gene_ids']]
        variant.coding_gene_ids = [g for g in annotation['coding_gene_ids']]


def add_convenience_annotations(annotation):
    """
    Add a bunch of convenience lookups to an annotation.
    This is kind of a historical relic - should try to remove as many as we can
    TODO: yeah let's aim to get rid of this completely
    """
    vep_annotation = annotation['vep_annotation']
    annotation['gene_ids'] = vep_annotations.get_gene_ids(vep_annotation)
    annotation["coding_gene_ids"] = vep_annotations.get_coding_gene_ids(vep_annotation)
    annotation['worst_vep_annotation_index'] = vep_annotations.get_worst_vep_annotation_index(vep_annotation)
    annotation['worst_vep_index_per_gene'] = {}
    annotation['annotation_tags'] = list({a['consequence'] for a in vep_annotation})
    for gene_id in annotation['gene_ids']:
        annotation['worst_vep_index_per_gene'][gene_id] = vep_annotations.get_worst_vep_annotation_index(
            vep_annotation,
            gene_id=gene_id
        )

    per_gene = {}
    for gene_id in annotation['coding_gene_ids']:
        per_gene[gene_id] = vep_annotations.get_worst_vep_annotation_index(vep_annotation, gene_id=gene_id)
    annotation['worst_vep_index_per_gene'] = per_gene

    worst_vep_annotation = vep_annotation[annotation['worst_vep_annotation_index']]

    annotation['vep_consequence'] = None
    if worst_vep_annotation:
        annotation['vep_consequence'] = worst_vep_annotation['consequence']

    annotation['vep_group'] = None
    if worst_vep_annotation:
        annotation['vep_group'] = constants.ANNOTATION_GROUP_REVERSE_MAP[annotation['vep_consequence']]

