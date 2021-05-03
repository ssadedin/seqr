/**
 * @GrabConfig (systemClassLoader =true)
 */

import groovy.json.JsonSlurper
import groovy.transform.Field
import groovyx.net.http.FromServer
import picocli.CommandLine

@Grab('info.picocli:picocli-groovy')
@Grab('io.github.http-builder-ng:http-builder-ng-core')
@picocli.groovy.PicocliScript
@picocli.CommandLine.Command(name = "reconcile_es_indices",
        mixinStandardHelpOptions = true,  // add --help and --version options
        version = "0.0.1",
        description = """
This script compares two instances of Seqr Elasticsearch and ensures all their indices have the same document counts.
It also compares the first 1000 documents and ensure all contents (hits) are identical.
Requires access to Seqr DB, Seqr source ES and the other Seqr ES service to compare with.

To run this script locally, create SSH tunnel as follows:
seqrDb: ssh -L 0.0.0.0:15432:localhost:5432 seqr@seqr-test-gcp
sourceEsUrl: ssh -L 0.0.0.0:19200:\$(gcloud compute addresses list --filter='name=seqr-prod-b-es' --format='value(address)'):30100 seqr@seqrprodb
targetEsUrl: ssh -L 0.0.0.0:29200:\$(gcloud compute addresses list --filter='name=seqr-prod-a-es' --format='value(address)'):30100 seqr@seqrproda

then run script as follows:
groovy reconcile_es_indices.groovy "jdbc:postgresql://localhost:15432/seqrdb?user=postgres&password=\$DB_PASSWORD" http://localhost:9200 elastic \$PASSWORD http://localhost:19200 elastic \$PASSWORD
""")
import static groovyx.net.http.ContentTypes.JSON
import static groovyx.net.http.HttpBuilder.configure

@CommandLine.Parameters(index = '0', arity = '1', paramLabel = 'sourceIndex', description = 'Source index name')
@Field String sourceIndex
@CommandLine.Parameters(index = '1', arity = '1', paramLabel = 'sourceEsUrl', defaultValue = 'http://localhost:19200', description = 'Source Elasticsearch URL')
@Field String sourceEsUrl
@CommandLine.Parameters(index = '2', arity = '1', paramLabel = 'sourceEsUsername', defaultValue = 'elastic', description = 'Source Elasticsearch username')
@Field String sourceEsUsername
@CommandLine.Parameters(index = '3', arity = '1', paramLabel = 'sourceEsPassword', defaultValue = 'password', description = 'Source Elasticsearch password')
@Field String sourceEsPassword
@CommandLine.Parameters(index = '4', arity = '1', paramLabel = 'targetIndex', description = 'Target index name')
@Field String targetIndex
@CommandLine.Parameters(index = '5', arity = '1', paramLabel = 'targetEsUrl', defaultValue = 'http://localhost:29200', description = 'Target Elasticsearch URL')
@Field String targetEsUrl
@CommandLine.Parameters(index = '6', arity = '1', paramLabel = 'targetEsUsername', defaultValue = 'elastic', description = 'Target Elasticsearch username')
@Field String targetEsUsername
@CommandLine.Parameters(index = '7', arity = '1', paramLabel = 'targetEsPassword', defaultValue = 'password', description = 'Target Elasticsearch password')
@Field String targetEsPassword

@CommandLine.Option(arity = '1', names = ['-n', '--docCount'], defaultValue = '1000', description = 'number of documents to compare')
@Field Integer docCount

def projectIndices = ["${sourceIndex}": "${targetIndex}"]

def ES_QUERY = """
{    
    "_source": {
        "exclude": ["_index", "_type"]
    },
    "query": {
        "match_all": {}
    },
    "track_total_hits": true,
    "from": 0,
    "size": $docCount,
    "sort": {
      "variantId": "asc"
    }
}
"""

projectIndices.each { source, target ->
    println "Comparing sourceIndex=$source to targetIndex=$target"

    def body = new JsonSlurper().parseText(ES_QUERY)

    def sourceResult = configure {
        request.auth.basic sourceEsUsername, sourceEsPassword
        request.uri = sourceEsUrl
        request.contentType = JSON[0]
    }.get {
        request.uri.path = "/$source/_search"
        request.body = body
        response.failure { FromServer fs, def respBody ->
            println "Not found in sourceIndex, skipping... sourceIndex=$source, statusCode=${fs.statusCode}, message=${fs.message}"
        }
    }

    if (sourceResult) {
        Long sourceDocCount = sourceResult.hits.total.value
        def sourceDocSources = sourceResult.hits.hits._source

        def targetResult = configure {
            request.auth.basic targetEsUsername, targetEsPassword
            request.uri = targetEsUrl
            request.contentType = JSON[0]
        }.get {
            request.uri.path = "/$target/_search"
            request.body = body
            response.failure { FromServer fs, def respBody ->
                println "ERROR: Elasticsearch targetIndex=$target found in source but not in target."
            }
        }

        if (targetResult) {
            Long targetDocCount = targetResult.hits.total.value
            def targetDocSources = targetResult.hits.hits._source

            assert sourceDocCount == targetDocCount

            sourceDocSources.eachWithIndex { sourceDoc, docIdx ->
                println "Comparing sourceDoc[$docIdx]"
                sourceDoc.keySet().each { k ->
                    def sourceDocProp = sourceDoc[k]
                    def targetDocProp = targetDocSources[docIdx][k]

                    if (k in ['mainTranscript_hgvs', 'mainTranscript_hgvsc', 'mainTranscript_protein_id', 'mainTranscript_gene_id', 'mainTranscript_gene_symbol', 'mainTranscript_cdna_start', 'mainTranscript_cdna_end', 'mainTranscript_transcript_id', 'sortedTranscriptConsequences']) {
                        return
                    } else if (sourceDocProp instanceof Collection) {
                        assert sourceDocProp?.sort(false) == targetDocProp?.sort(false), "$k not equal"
                    } else {
                        assert sourceDocProp == targetDocProp, "$k not equal"
                    }
                }
            }
        }
    }
}
