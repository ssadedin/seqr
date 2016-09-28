seqr: Loading VCF Data
====================================

Once you have seqr running you probably want to start loading your own sample data into it.
For the simplest typical scenario, this means that you have one or more VCFs, and you want to
put them into seqr. Seqr needs to know some amount of metadata about samples that is not provided
in a VCF file, so it is necessary to provide not just a VCF file, but also some other files and 
a further overall file that points to where all the pieces are. Seqr refers to all this collection
of files as a "project". 

The workflow consists of multiple steps. Currently this is a little complicated because sample data
is maintained in both Seqr itself and also Phenotips. As a result, the samples and results need to be
created in multiple placess. The workflow is described below.

## Generate the VCF(s)

How you do this is up to you, but Seqr does have some expectations about the annotations in the VCF.
In particular:

   * the following genotype format is expected: GT:AD:DP:GQ:PL
   * a specific set of annotations is required, including those provided by the 
     [dbNSFP](http://www.ensembl.info/ecode/loftee/) and [LoFTEE](http://www.ensembl.info/ecode/loftee/) plugins. 
     Once these plugins have been installed, the following command correctly annotates a VCF 
     file (here called my_data.vcf.gz): 
 
   ```perl ./vep/ensembl-tools-release-81/scripts/variant_effect_predictor/variant_effect_predictor.pl --everything --vcf --allele_number --no_stats --cache --offline --dir ./vep_cache/ --force_overwrite --cache_version 81 --fasta ./vep_cache/homo_sapiens/81_GRCh37/Homo_sapiens.GRCh37.75.dna.primary_assembly.fa --assembly GRCh37 --tabix --plugin LoF,human_ancestor_fa:./loftee_data/human_ancestor.fa.gz,filter_position:0.05,min_intron_size:15 --plugin dbNSFP,./reference_data/dbNSFP/dbNSFPv2.9.gz,Polyphen2_HVAR_pred,CADD_phred,SIFT_pred,FATHMM_pred,MutationTaster_pred,MetaSVM_pred -i my_data.vcf.gz -o my_data.vep.vcf.gz```
   
## Create a Project Directory

Projects live under `${SEQR_INSTALL_DIR}/data/projects`, so you need to create a subdirectory there
with the following structure:

```
├── my_project
    ├── my_vcf_file.vcf.gz
    ├── all_samples.txt
    ├── project.yaml
    └── sample_data
        └── my_project.ped
```

Replace all the parts starting with `my_` with files named according to your own preference.

The file `all_samples.txt` should list the samples to be included, one per line. Make sure the identifiers
in here actually match sample ids that are present in your VCF file. Seqr will silently ignore mismatches!

The file my_project.ped should be a standard [PED file](http://pngu.mgh.harvard.edu/~purcell/plink/data.shtml) that
describes the sex, family structure and phenotype of the samples to be imported.

## Add the Project to Seqr

This is done by running the command below:

```
./manage.py add_project test_project 'my test project'
```

## Add the Project to Phenotips

```
./manage.py add_project_to_phenotips test_project 'my test project'
```

## Add the Samples to the Project

```
./manage.py add_individuals_to_project  test_project --ped /Users/simon/work/seqr-run/data/projects/test_project/sample_data/test_project.ped 
```

## Add the Samples to Phenotips

```
./manage.py add_individuals_to_phenotips  test_project --ped /Users/simon/work/seqr-run/data/projects/test_project/sample_data/test_project.ped
```

## Load the VCF File

```
./manage.py load_project_dir test_project /Users/simon/work/seqr-run/data/projects/test_project
```

