import logging
import os
import random
import string
from pymongo import MongoClient


logger = logging.getLogger(__name__)

SEQR_VERSION = 'v1.0'

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ADMINS = [
    ('Ben Weisburd', 'weisburd@broadinstitute.org'),
    ('Hana Snow', 'hsnow@broadinstitute.org'),
]

MANAGERS = ADMINS

# Password validation - https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'hijack',
    'compat',
    'corsheaders',
    'guardian',
    'anymail',
    'seqr',
    'reference_data',
    'xbrowse_server.base',
    'xbrowse_server.gene_lists',
    'breakpoint_search'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'seqr.utils.middleware.JsonErrorMiddleware',
]

# django-hijack plugin
HIJACK_DISPLAY_WARNING = True
HIJACK_LOGIN_REDIRECT_URL = '/dashboard'

CORS_ORIGIN_WHITELIST = (
    'localhost:3000',
    'localhost:8000',
)
CORS_ALLOW_CREDENTIALS = True

# django-debug-toolbar settings
ENABLE_DJANGO_DEBUG_TOOLBAR = False
if ENABLE_DJANGO_DEBUG_TOOLBAR:
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INSTALLED_APPS = ['debug_toolbar'] + INSTALLED_APPS
    INTERNAL_IPS = ['127.0.0.1']
    SHOW_COLLAPSED = True
    DEBUG_TOOLBAR_PANELS = [
        'ddt_request_history.panels.request_history.RequestHistoryPanel',
        #'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        #'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        #'debug_toolbar.panels.cache.CachePanel',
        #'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
    DEBUG_TOOLBAR_CONFIG = {
        'RESULTS_CACHE_SIZE': 100,
    }


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

STATIC_URL = '/static/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s: %(message)s     (%(name)s.%(funcName)s:%(lineno)d)',
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s:  %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'INFO',
            'filters': ['require_debug_false'],
            'class': 'logging.FileHandler',
            'filename': 'django.info.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'formatter': 'verbose',
            'propagate': True,
        },
    }
}

ELASTICSEARCH_SERVICE_HOSTNAME = os.environ.get('ELASTICSEARCH_SERVICE_HOSTNAME', 'localhost')
ELASTICSEARCH_PORT = os.environ.get('ELASTICSEARCH_SERVICE_PORT', "9200")
ELASTICSEARCH_SERVER = "%s:%s" % (ELASTICSEARCH_SERVICE_HOSTNAME, ELASTICSEARCH_PORT)

DEPLOYMENT_TYPE_DEV = "dev"
DEPLOYMENT_TYPE_PROD = "prod"
DEPLOYMENT_TYPES = set([DEPLOYMENT_TYPE_DEV, DEPLOYMENT_TYPE_PROD])
DEPLOYMENT_TYPE = os.environ.get("DEPLOYMENT_TYPE", DEPLOYMENT_TYPE_DEV)
assert DEPLOYMENT_TYPE in DEPLOYMENT_TYPES, "Invalid deployment type: %(DEPLOYMENT_TYPE)s" % locals()

# set the secret key
SECRET_FILE = os.path.join(os.path.dirname(__file__), 'django_key')
try:
    SECRET_KEY = open(SECRET_FILE).read().strip()
except IOError:
    try:
        SECRET_KEY = ''.join(random.SystemRandom().choice(string.printable) for i in range(50))
        with open(SECRET_FILE, 'w') as f:
            f.write(SECRET_KEY)
    except IOError as e:
        logger.warn('Unable to generate {}: {}'.format(os.path.abspath(SECRET_FILE), e))
        SECRET_KEY = os.environ.get("DJANGO_KEY", "-placeholder-key-")

if DEPLOYMENT_TYPE == DEPLOYMENT_TYPE_PROD:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
else:
    DEBUG = True

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

# optional - slack token for sending matchmaker alerts to Slack
SLACK_TOKEN = os.environ.get("SLACK_TOKEN")

BASE_URL = os.environ.get("BASE_URL", "/")

# ===========================================================
# ===========================================================
# legacy settings that need to be reviewed

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.dirname(os.path.realpath(__file__)) + '/ui/dist/',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.request",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ROOT_URLCONF = 'seqr.urls'

WSGI_APPLICATION = 'wsgi.application'

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

MONGO_SERVICE_HOSTNAME = os.environ.get('MONGO_SERVICE_HOSTNAME', 'localhost')

FROM_EMAIL = "\"seqr\" <seqr@broadinstitute.org>"


FAMILY_LOAD_BATCH_SIZE = 25000

# defaults for optional local settings
CONSTRUCTION_TEMPLATE = None

VARIANT_QUERY_RESULTS_LIMIT = 2500

KIBANA_HOSTNAME = os.environ.get('KIBANA_SERVICE_HOSTNAME', 'localhost')
KIBANA_PORT = os.environ.get('KIBANA_SERVICE_PORT', 5601)
KIBANA_SERVER = "%s:%s" % (KIBANA_HOSTNAME, KIBANA_PORT)

PHENOTIPS_PORT = os.environ.get('PHENOTIPS_SERVICE_PORT', 8080)
PHENOTIPS_SERVICE_HOSTNAME = os.environ.get('PHENOTIPS_SERVICE_HOSTNAME', 'localhost')
PHENOTIPS_SERVER = "%s:%s" % (PHENOTIPS_SERVICE_HOSTNAME, PHENOTIPS_PORT)
PHENOPTIPS_BASE_URL = 'http://%s:%s' % (os.environ.get('PHENOTIPS_SERVICE_HOSTNAME', 'localhost'), PHENOTIPS_PORT)
PHENOPTIPS_ALERT_CONTACT = 'harindra@broadinstitute.org'
_client = MongoClient(MONGO_SERVICE_HOSTNAME, 27017)
_db = _client['phenotips_edit_audit']
PHENOTIPS_EDIT_AUDIT = _db['phenotips_audit_record']
PHENOTIPS_ADMIN_UNAME = 'Admin'
PHENOTIPS_ADMIN_PWD = 'admin'
PHENOTIPS_UPLOAD_EXTERNAL_PHENOTYPE_URL = "http://"+PHENOTIPS_SERVICE_HOSTNAME+":"+str(PHENOTIPS_PORT)+"/rest/patients/eid"

# when set to None, this *disables* the PhenoTips interface for all projects. If set to a list of project ids, it will
# enable the PhenoTips interface for *all* projects except those in the list.
PROJECTS_WITHOUT_PHENOTIPS = []


REDIS_SERVICE_HOSTNAME = os.environ.get('REDIS_SERVICE_HOSTNAME', 'localhost')


#-----------------Matchmaker constants-----------------

#########################################################
MME_DEFAULT_CONTACT_NAME = 'Samantha Baxter'
MME_DEFAULT_CONTACT_INSTITUTION = "Broad Center for Mendelian Genomics"
MME_DEFAULT_CONTACT_HREF = "mailto:matchmaker@broadinstitute.org"

#########################################################
# Activates searching in external MME nodes
#########################################################
SEARCH_IN_EXTERNAL_MME_NODES=True

MME_NODE_ADMIN_TOKEN=os.environ.get("MME_NODE_ADMIN_TOKEN", "abcd")
MME_NODE_ACCEPT_HEADER='application/vnd.ga4gh.matchmaker.v1.0+json'
MME_CONTENT_TYPE_HEADER='application/vnd.ga4gh.matchmaker.v1.0+json'
MME_HEADERS = {
    'X-Auth-Token': MME_NODE_ADMIN_TOKEN,
    'Accept': MME_NODE_ACCEPT_HEADER,
    'Content-Type': MME_CONTENT_TYPE_HEADER
}
MATCHBOX_SERVICE_HOSTNAME = os.environ.get('MATCHBOX_SERVICE_HOSTNAME', 'localhost')
MME_SERVER_HOST='http://%s:9020' % MATCHBOX_SERVICE_HOSTNAME
#adds a patient to MME
MME_ADD_INDIVIDUAL_URL = MME_SERVER_HOST + '/patient/add'
#deletes a patient from MME
MME_DELETE_INDIVIDUAL_URL = MME_SERVER_HOST + '/patient/delete'
#matches in local MME database ONLY, won't search in other MME nodes
MME_LOCAL_MATCH_URL = MME_SERVER_HOST + '/match'
#matches in EXTERNAL MME nodes ONLY, won't search in LOCAL MME database/node
MME_EXTERNAL_MATCH_URL = MME_SERVER_HOST + '/match/external'
#privileged/internal metrics URL
MME_MATCHBOX_METRICS_URL= MME_SERVER_HOST + '/metrics'
#Public metrics URL
MME_MATCHBOX_PUBLIC_METRICS_URL= MME_SERVER_HOST + '/metrics/public'
#set this to None if you don't have Slack
MME_SLACK_EVENT_NOTIFICATION_CHANNEL='matchmaker_alerts'
MME_SLACK_MATCH_NOTIFICATION_CHANNEL='matchmaker_matches'
MME_SLACK_SEQR_MATCH_NOTIFICATION_CHANNEL='matchmaker_seqr_match'

MONARCH_MATCH_URL = 'https://mme.monarchinitiative.org/match'

#This is used in slack post to add a link back to project
SEQR_HOSTNAME_FOR_SLACK_POST='https://seqr.broadinstitute.org/project'


PROJECT_IDS_TO_EXCLUDE_FROM_DISCOVERY_SHEET_DOWNLOAD = []

GENERATED_FILES_DIR = os.path.join(os.path.dirname(__file__), 'generated_files')
MEDIA_ROOT = os.path.join(GENERATED_FILES_DIR , 'media/')

ALLOWED_HOSTS = ['*']

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "anymail.backends.postmark.EmailBackend")
EMAIL_HOST = os.environ.get("SMTP_EMAIL_HOST", "localhost")
EMAIL_PORT = os.environ.get("SMTP_EMAIL_PORT", "1025")
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "seqr@broadinstitute.org")

ANYMAIL = {
    #"SENDGRID_API_KEY": os.environ.get('SENDGRID_API_KEY', 'sendgrid-api-key-placeholder'),
    "POSTMARK_SERVER_TOKEN": os.environ.get('POSTMARK_SERVER_TOKEN', 'postmark-server-token-placeholder'),
}

DEFAULT_CONTROL_COHORT = 'controls'
CONTROL_COHORTS = [
    {
        'slug': 'controls',
        'vcf': '',
    },
]

READ_VIZ_BAM_PATH = 'https://broad-seqr'
READ_VIZ_CRAM_PATH = 'broad-seqr:5000'

READ_VIZ_USERNAME = "xbrowse-bams"
READ_VIZ_PASSWD = "xbrowse-bams"

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'ui/dist/'),    # this is so django's collectstatic copies ui dist files to STATIC_ROOT
)

ANNOTATOR_REFERENCE_POPULATIONS_IN_ELASTICSEARCH = [
    {"slug": "1kg_wgs_phase3", "name": "1000G v3", "has_hom_hemi": False, "full_name": "1000 Genomes Samples", "description": "Filter out variants that have a higher allele count (AC) in the 1000 Genomes Phase 3 release (5/2/2013), or a higher allele frequency (popmax AF) in any one of these five subpopulations defined for 1000 Genomes Phase 3: AFR, AMR, EAS, EUR, SAS"},
    {"slug": "exac_v3", "name": "ExAC v0.3", "has_hom_hemi": True, "full_name": "ExAC", "description": "Filter out variants that have a higher allele count (AC) or homozygous/hemizygous count (H/H) in ExAC, or a higher allele frequency (popmax AF) in any one of these six subpopulations defined for ExAC: AFR, AMR, EAS, FIN, NFE, SAS"},
    {"slug": "gnomad-genomes2", "name": "gnomAD 15k genomes", "has_hom_hemi": True, "description": "Filter out variants that have a higher allele count (AC) or homozygous/hemizygous count (H/H) among gnomAD genomes, or a higher allele frequency (popmax AF) in any one of these six subpopulations defined for gnomAD genomes: AFR, AMR, EAS, FIN, NFE, ASJ"},
    {"slug": "gnomad-exomes2", "name": "gnomAD 123k exomes", "has_hom_hemi": True, "description": "Filter out variants that have a higher allele count (AC) or homozygous/hemizygous count (H/H) among gnomAD genomes, or a higher allele frequency (popmax AF) in any one of these seven subpopulations defined for gnomAD genomes: AFR, AMR, EAS, FIN, NFE, ASJ, SAS"},
    {"slug": "topmed", "name": "TOPMed", "has_hom_hemi": False, "description": "Filter out variants that have a higher allele count (AC), or a higher allele frequency (AF) in TOPMed"},
    {"slug": "AF", "name": "This Callset", "has_hom_hemi": False, "description": ""},
]

UPLOADED_PEDIGREE_FILE_RECIPIENTS = os.environ.get('UPLOADED_PEDIGREE_FILE_RECIPIENTS', '').split(',')

MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(os.path.dirname(__file__), 'static')

LOGIN_URL = '/login'

LOGOUT_URL = '/logout'

API_LOGIN_REQUIRED_URL = '/api/login-required-error'

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE=True

POSTGRES_DB_CONFIG = {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'HOST': os.environ.get('POSTGRES_SERVICE_HOSTNAME', 'localhost'),
    'PORT': int(os.environ.get('POSTGRES_SERVICE_PORT', '5432')),
    'USER': os.environ.get('POSTGRES_USERNAME', 'postgres'),
    'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
}
DATABASES = {
    'default': dict(NAME='seqrdb', **POSTGRES_DB_CONFIG),
    'reference_data': dict(NAME='reference_data_db', **POSTGRES_DB_CONFIG),
}
DATABASE_ROUTERS = ['reference_data.models.ReferenceDataRouter']

logger.info("MONGO_SERVICE_HOSTNAME: " + MONGO_SERVICE_HOSTNAME)
logger.info("PHENOTIPS_SERVICE_HOSTNAME: " + PHENOTIPS_SERVICE_HOSTNAME)
logger.info("MATCHBOX_SERVICE_HOSTNAME: " + MATCHBOX_SERVICE_HOSTNAME)
