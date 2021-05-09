# MCRI Elasticsearch Deployment

This directory contains instructions and all deployment descriptors required for deploying Seqr's Elasticsearch instance
at MCRI, hosted on Google Kubernetes Engine.

## Prerequisites

* [Google Cloud SDK](https://cloud.google.com/sdk/install) installed.
* [Google Cloud SDK](https://cloud.google.com/sdk/docs/authorizing) initialized and authorized.
* [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) installed, this is the Kubernetes command-line
  tool.

## Creating New GKE Cluster

Use gcloud to create a new cluster.  This command was generated by the GCP web UI.

```bash
ENV_LABEL="test"
CLUSTER_NAME="seqr-es-cluster-test"
BQ_DATASET_NAME="seqr_es_cluster_test"
GCP_ZONE="australia-southeast1-b"

gcloud beta container \
  --project "mcri-01" clusters create "$CLUSTER_NAME" \
  --zone "$GCP_ZONE" \
  --no-enable-basic-auth \
  --cluster-version "1.18.16-gke.502" \
  --release-channel "regular" \
  --machine-type "e2-highmem-2" \
  --image-type "COS_CONTAINERD" \
  --disk-type "pd-standard" \
  --disk-size "10" \
  --node-labels "env=$ENV_LABEL,nodeType=default" \
  --metadata disable-legacy-endpoints=true \
  --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" \
  --num-nodes "3" \
  --enable-stackdriver-kubernetes \
  --enable-ip-alias \
  --network "projects/mcri-01/global/networks/default" \
  --subnetwork "projects/mcri-01/regions/australia-southeast1/subnetworks/default" \
  --default-max-pods-per-node "110" \
  --enable-autoscaling \
  --min-nodes "0" \
  --max-nodes "3" \
  --no-enable-master-authorized-networks \
  --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver,ConfigConnector \
  --enable-autoupgrade \
  --enable-autorepair \
  --max-surge-upgrade 1 \
  --max-unavailable-upgrade 0 \
  --maintenance-window-start "2021-04-13T15:00:00Z" \
  --maintenance-window-end "2021-04-14T15:00:00Z" \
  --maintenance-window-recurrence "FREQ=WEEKLY;BYDAY=SA,SU" \
  --labels "env=$ENV_LABEL" \
  --resource-usage-bigquery-dataset "$BQ_DATASET_NAME" \
  --enable-network-egress-metering \
  --enable-resource-consumption-metering \
  --workload-pool "mcri-01.svc.id.goog" \
  --enable-shielded-nodes \
  --tags "default" \
  --autoscaling-profile optimize-utilization \
  --node-locations "$GCP_ZONE"
```

Above command should have also configured `kubectl` with authentication and use this new cluster as its default context.
Below are some explanation of above options.

* `--image-type "COS_CONTAINERD"` - cos_containerd is recommended Docker runtime for GKE, see [Node
  images](https://cloud.google.com/kubernetes-engine/docs/concepts/node-images)
* `--node-labels nodeType=default` - Used by K8 deployment descriptors to select which node to create Workloads in.
* `--addons GcePersistentDiskCsiDriver` - Required to support expandable disk
* `--network "projects/mcri-01/global/networks/default"` - Ensure internal load balancers created on this cluster can be
  accessed by other GCP services on the same default network
* `--resource-usage-bigquery-dataset "$BQ_DATASET_NAME"` - `$BQ_DATASET_NAME` dataset must already exist in BigQuery
  within same GCP project.  Together with `--enable-network-egress-metering` and
  `--enable-resource-consumption-metering` options, these information are automatically logged to this dataset.
* `--node-locations "australia-southeast1-b"` - Always create nodes in this region

If the cluster already exists, run this command to have `kubectl` authenticate with this cluster.

```bash
gcloud container clusters get-credentials $CLUSTER_NAME
```

If your authentication is already configured with the cluster then simply get `kubectl` to change context to this new
cluster.

```bash
kubectl config use-context $CLUSTER_NAME
```

## Configuring New GKE Cluster

Below instructions are for creating a new GKE Elasticsearch cluster with existing persistent disks.

### Applying Kubernetes Elasticsearch Deployment Descriptors

Before applying below K8 deployment descriptors, please ensure required persistent disks already exists.  See [Using
preexisting persistent disks as
PersistentVolumes](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/preexisting-pd) and [Adding
or resizing zonal persistent disks](https://cloud.google.com/compute/docs/disks/add-persistent-disk).

The required persistent disks can be found in `elasticsearch/es-data-<env>.yaml` and the names of these persistent disks must
match the name in `gcePersistentDisk.pdName` property.

```bash
cd $SEQR/mcri_deploy/kubernetes

kubectl apply -f elasticsearch/all-in-one.yaml
kubectl apply -f standard-expandable-storage-class.yaml
kubectl apply -f elasticsearch/es-data-test.yaml

# For production
# kubectl apply -f elasticsearch/es-data-prod.yaml

# Note that elasticsearch/all-in-one.yaml needs to be applied before this can continue, usually only takes a few seconds
# Before applying, change labels env=test to env=production
kubectl apply -f elasticsearch/elasticsearch.gcloud.yaml

# After 5-10 minutes, all workloads and services should be up and running
kubectl get all

NAME                                       READY   STATUS    RESTARTS   AGE
pod/elasticsearch-es-client-node-0         1/1     Running   0          9m51s
pod/elasticsearch-es-client-node-1         1/1     Running   0          9m50s
pod/elasticsearch-es-data-0                1/1     Running   0          9m50s
pod/elasticsearch-es-data-1                1/1     Running   0          9m49s
pod/elasticsearch-es-data-2                1/1     Running   0          9m49s
pod/elasticsearch-es-data-loading-node-0   1/1     Running   0          9m49s
pod/elasticsearch-es-data-loading-node-1   1/1     Running   0          9m48s
pod/elasticsearch-es-master-node-0         1/1     Running   0          9m52s
pod/elasticsearch-es-master-node-1         1/1     Running   0          9m51s
pod/elasticsearch-es-master-node-2         1/1     Running   0          9m51s

NAME                                         TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)          AGE
service/elasticsearch-es-client-node         ClusterIP      None           <none>        9200/TCP         9m52s
service/elasticsearch-es-data                ClusterIP      None           <none>        9200/TCP         9m51s
service/elasticsearch-es-data-loading-node   ClusterIP      None           <none>        9200/TCP         9m51s
service/elasticsearch-es-http                ClusterIP      10.12.15.184   <none>        9200/TCP         9m55s
service/elasticsearch-es-http-ilb            LoadBalancer   10.12.5.96     10.152.0.6    9200:30760/TCP   10m
service/elasticsearch-es-master-node         ClusterIP      None           <none>        9200/TCP         9m53s
service/elasticsearch-es-transport           ClusterIP      None           <none>        9300/TCP         9m55s
service/kubernetes                           ClusterIP      10.12.0.1      <none>        443/TCP          13m

NAME                                                  READY   AGE
statefulset.apps/elasticsearch-es-client-node         2/2     9m53s
statefulset.apps/elasticsearch-es-data                3/3     9m52s
statefulset.apps/elasticsearch-es-data-loading-node   2/2     9m50s
statefulset.apps/elasticsearch-es-master-node         3/3     9m53s
```

```bash
# Port forward K8 service locally to 19200
kubectl port-forward service/elasticsearch-es-http 19200:9200

# Get ES password
PASSWORD=$(kubectl get secret elasticsearch-es-elastic-user -o go-template='{{.data.elastic | base64decode}}')

# Check version
curl -u "elastic:$PASSWORD" -k "http://localhost:19200"

{
  "name" : "elasticsearch-es-data-2",
  "cluster_name" : "elasticsearch",
  "cluster_uuid" : "n4kbATAESLe-mSAt92q8-w",
  "version" : {
    "number" : "7.8.1",
    "build_flavor" : "default",
    "build_type" : "docker",
    "build_hash" : "b5ca9c58fb664ca8bf9e4057fc229b3396bf3a89",
    "build_date" : "2020-07-21T16:40:44.668009Z",
    "build_snapshot" : false,
    "lucene_version" : "8.5.1",
    "minimum_wire_compatibility_version" : "6.8.0",
    "minimum_index_compatibility_version" : "6.0.0-beta1"
  },
  "tagline" : "You Know, for Search"
}

# Check Elasticsearch reported health, note it's not 100% because some indices are genuinely not healthy
curl -u "elastic:$PASSWORD" -k "http://localhost:19200/_cat/health"

1619167554 08:45:54 elasticsearch red 10 5 422 406 0 0 38 0 - 91.7%

# Check indices count
curl -s -k -u "elastic:$PASSWORD" "http://localhost:19200/_cat/indices?v" | wc -l

88
```

## Increasing Storage Space

To increase disk space, simply increase the value in `volumeClaimTemplates.spec.resources.requests.storage` and run:

```bash
kubectl apply -f elasticsearch/elasticsearch.gcloud.yaml
```

**Note you can only increase disk space.**  If you attempt to decrease disk space, you'll get the following error upon
applying the changes: *decreasing storage size is not supported: an attempt was made to decrease storage size for claim
elasticsearch-data*

## Deployment Descriptors

### standard-expandable-storage-class.yaml

Create storage class using non SSD disk and uses expandable disk driver.  See [Using the Compute Engine persistent disk
CSI Driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/gce-pd-csi-driver)

### all-in-one.yaml

This is the ECK (Elastic Cloud on Kubernetes) custom resource definition that includes extensions of Kubernetes.  These
extensions provide easier setup and management of Elasticsearch clusters using Kubernetes.  See [Elastic Cloud on
Kubernetes](https://www.elastic.co/guide/en/cloud-on-k8s/current/k8s-overview.html) for more details. The file is a copy
from
[https://download.elastic.co/downloads/eck/1.5.0/all-in-one.yaml](https://download.elastic.co/downloads/eck/1.5.0/all-in-one.yaml)

### es-data-\<env>.yaml

This contains all persistence related Kubernetes configurations.  This descriptor assumes required persistent disks
already exists.

### elasticsearch.gcloud.yaml

Contains all components required to run Seqr application.  All components are deployed using StatefulSets (even though
only master-node, data and data-loading-node requires this).  This configuration configures following Kubernetes
[Workloads](https://kubernetes.io/docs/concepts/workloads/) and
[Services](https://kubernetes.io/docs/concepts/services-networking/service/).

* master-node
* client-node
* data
* data-loading-node
* elasticsearch-es-http-ilb

See [Elasticsearch Node](https://www.elastic.co/guide/en/elasticsearch/reference/7.x/modules-node.html) docs for more
details on why dedicated roles for each node are important.

## Operations and Troubleshooting

```bash
# Get Elasticsearch password
PASSWORD=$(kubectl get secret elasticsearch-es-elastic-user -o go-template='{{.data.elastic | base64decode}}')

# Port forward Elasticsearch service on port 9200 to locally on 19200
kubectl port-forward service/elasticsearch-es-http 19200:9200

# Restart all workloads and since `imagePullPolicy` is set to `Always`, all container changes are erased.
kubectl rollout restart statefulset.apps/elasticsearch-es-client-node
kubectl rollout restart statefulset.apps/elasticsearch-es-data-loading-node
kubectl rollout restart statefulset.apps/elasticsearch-es-data
kubectl rollout restart statefulset.apps/elasticsearch-es-master-node
```