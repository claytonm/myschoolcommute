from django.conf.urls import url, include, patterns
from django.conf.urls.i18n import i18n_patterns
from django.views.generic import TemplateView

from django.contrib import admin
admin.autodiscover()

urlpatterns = i18n_patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Translation app
    url(r'^rosetta/', include('rosetta.urls')),

    #Accounts
    url(r'^accounts/', include('accounts.urls')),

    # district/school list on front-page
    url(r'^$', 'survey.views.index', name='home'),

    # static pages
    url(r'^about/$', TemplateView.as_view(template_name='survey/about.html'), name='about'),
    url(r'^resources/$', TemplateView.as_view(template_name='survey/resources.html'), name='resources'),

    # custom admin pages
    url(r'^districts/$', 'survey.views.district_list', name='district_list'),
    url(r'^(?P<district_slug>[-\w]+)/(?P<school_slug>[-\w]+)/edit/$', 'survey.views.school_edit', name='school_edit'),
    url(r'^(?P<district_slug>[-\w]+)/(?P<school_slug>[-\w]+)/batch/$', 'survey.views.batch_form', name='survey_batch_form'),

    # district
    url(r'^(?P<district_slug>[-\w]+)/$', 'survey.views.district', name='school_list'),
    url(r'^(?P<districtid>[-\w]+)/schools/$', 'survey.views.get_schools', name='disctrict_get_schools'),
    url(r'^(?P<districtid>[-\w]+)/streets/$', 'survey.views.get_streets', name='disctrict_get_streets'),

    # school
    url(r'^(?P<district_slug>[-\w]+)/(?P<school_slug>[-\w]+)/$', 'survey.views.form', name='survey_school_form'),
)

urlpatterns += patterns('',
    # Testing
    url(r'^testr/$', 'survey.views.testr'),

    #Typeahead
    url(r'^(?P<school_id>\d+)/streets/(?P<query>[^/]*)/?$', 'survey.views.school_streets'),
    url(r'^(?P<school_id>\d+)/crossing/(?P<street>[^/]+)/(?P<query>[^/]*)/?$', 'survey.views.school_crossing' ),
    url(r'^(?P<school_id>\d+)/intersection/(?P<street1>[^/]+)/(?P<street2>[^/]*)/?$', 'survey.views.intersection' ),

    # admin data
    url(r'^(?P<school_id>\d+)/walkshed.geojson$', 'survey.maps.school_sheds_json', name='sheds_json'),
    url(r'^(?P<school_id>\d+)/walkshed.png$', 'survey.maps.school_sheds', name='school_sheds'),
    url(r'^(?P<school_id>\d+)/walkshed.(?P<format>\w+)$', 'survey.maps.school_sheds', name='school_sheds_format'),
)
