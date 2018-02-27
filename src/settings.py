import os
from os import environ

import dj_database_url

import otree.settings
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# the environment variable OTREE_PRODUCTION controls whether Django runs in
# DEBUG mode. If OTREE_PRODUCTION==1, then DEBUG=False
if environ.get('OTREE_PRODUCTION') not in {None, '', '0'}:
    DEBUG = False
else:
    DEBUG = True

# don't share this with anybody.
SECRET_KEY = 'zu4rrhuye)%8y#yqaxk9!$yianljgjm@_r54bi&-$71_*sl0p&'


DATABASES = {
    'default': dj_database_url.config(
        # Rather than hardcoding the DB parameters here,
        # it's recommended to set the DATABASE_URL environment variable.
        # This will allow you to use SQLite locally, and postgres/mysql
        # on the server
        # Examples:
        # export DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/NAME
        # export DATABASE_URL=mysql://USER:PASSWORD@HOST:PORT/NAME

        # fall back to SQLite if the DATABASE_URL env var is missing
        default='sqlite:///' + os.path.join(BASE_DIR, 'db.sqlite3')
    )
}

# AUTH_LEVEL:
# this setting controls which parts of your site are freely accessible,
# and which are password protected:
# - If it's not set (the default), then the whole site is freely accessible.
# - If you are launching a study and want visitors to only be able to
#   play your app if you provided them with a start link, set it to STUDY.
# - If you would like to put your site online in public demo mode where
#   anybody can play a demo version of your game, but not access the rest
#   of the admin interface, set it to DEMO.

# for flexibility, you can set it in the environment variable OTREE_AUTH_LEVEL
AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL')

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')


# setting for integration with AWS Mturk
AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')


# e.g. EUR, CAD, GBP, CHF, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True



# e.g. en, de, fr, it, ja, zh-hans
# see: https://docs.djangoproject.com/en/1.9/topics/i18n/#term-language-code
LANGUAGE_CODE = 'en'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = [
    'otree',
    'otree_mturk_utils',
    ]

# SENTRY_DSN = ''

DEMO_PAGE_INTRO_TEXT = """
<p>
    This is the administration page for the Supervised Human Neural Network Experiment. For more info see:
</p>
<ul>
    <li>
        <a href="https://github.com/oTree-org/otree" target="_blank">
            oTree on GitHub
        </a>.
    </li>
    <li>
        <a href="http://www.otree.org/" target="_blank">
            oTree homepage
        </a>.
    </li>
</ul>

"""

ROOMS = [
    {
        'name': 'SHNN_pilot',
        'display_name': 'Medical Literature Classifying Task',
        'participant_label_file': '_rooms/shnn_pilot.txt',
    },
    {
        'name': 'live_demo',
        'display_name': 'Room for live demo (no participant labels)',
    },
]


mturk_hit_settings = {
    'keywords': ['easy', 'bonus', 'choice', 'study', 'classification', 'timed'],
    'title': '[start: 9:30AMPST] 10-14 min (timed) Academic Experiment (Classifying Task) with bonus',
    'description': 'Determine the effect of interactions between a food item and a drug compound based on evidence from medical literature',
    'frame_height': 800,
    'preview_template': 'global/MTurkWelcome.html',
    'minutes_allotted_per_assignment': 60,
    'expiration_hours': 1,
    'qualification_requirements': []
}


# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 0.25,
    'participation_fee': 1.25,
    'doc': "",
    'mturk_hit_settings': mturk_hit_settings,
}

SESSION_CONFIGS = [
    {
        'name': 'SHNN',
        'display_name': "SHNN",
        'num_demo_participants': 40,
        'app_sequence': ['shnn', 'payment_info'],
        'time_of_experiment': datetime.strptime('2017-12-20 17:32:00', '%Y-%m-%d %H:%M:%S'),
    }
]

# anything you put after the below line will override
# oTree's default settings. Use with caution.
otree.settings.augment_settings(globals())
{
'MTURK_NUM_PARTICIPANTS_MULTIPLE':1
}
