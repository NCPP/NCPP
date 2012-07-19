DESCRIPTION

Python/Django application for executing NCPP data tasks


DEPENDENCIES

o django.contrib.auth - for user authentication
o django.contrib.staticfiles - to serve the application static content
o OWSLib - for WPS request submission

INSTALLATION INSTRUCTIONS

o Unpack the "ncpp" application under your top-level project, for example:
	<MYSITE>/ncpp
	
o Edit the global settings file <MYSITE>/settings.py and add 'ncpp' to the list of INSTALLED_APPS
	INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.staticfiles',
    'ncpp',
)

o Make sure the file <MYSITE>/settings.py contains values for STATIC_URL and STATIC_ROOT, for example:
	STATIC_URL = "/static/"
	STATIC_ROOT = "./static"
	
o Run the static files utilities to copy the static files to the target STATIC_ROOT directory:
	python manage.py collectstatic

o Edit your top-level urls file <MYSITE>/urls.py and include the ncpp-specific urls file:
	(r'^ncpp/', include('ncpp.urls')),
	
o Add the ncpp tables to the database:
	python manage.py syncdb
	
o Optionally, enable the django 'admin' application to provide some basic management of user accounts:
	- add ''django.contrib.admin' to the list of INSTALLED_APPS in <MYSITE>/settings.py
	- enable the admin urls in <MYSITE>/urls.py
	
o Optionally, edit the global <MYSITE>/settings.py and define the target URL for user login, and for default redirection. For example:

LOGIN_URL = '/ncpp/login/'
LOGIN_REDIRECT_URL='/ncpp/'

If no values are found, the ncpp specific defaults will be used.

	
APPLICATION URLS

Assuming deployment into the standard django development environment, these are the top-level application URLs:

o http://localhost:8000/ncpp/
Top-level application URL, for now redirecting to climate indexes workflow

o http://localhost:8000/ncpp/climate_indexes/
Starting point for Climate Indexes workflow

o http://localhost:8000/ncpp/jobs/<username>/
Job listing for user <username>

o http://localhost:8000/ncpp/job/<job_id>/
Details for job <job_id>