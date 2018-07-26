'''
This file uses the Flask framework to create individual web pages
for our different methods (create, list, view, update). Whenever @app.route
is called a new page is generated and the template returns to the html
files to then display on the website. 
'''

import flask_wtf
import wtforms
import util
import flask
import auth
import model
from main import app
from google.appengine.ext import ndb

# This class only contains the campus name because the other
# properties are defined by the creation of other entities (ex:totalLots).
class NewCampus(flask_wtf.FlaskForm):
	campus = wtforms.StringField('Campus', [wtforms.validators.required()])

# Creates link to campus create page, ensures only administrators have access.
@app.route('/campus/create/', methods=['GET', 'POST'])
@auth.admin_required
def campus_create():
	form = NewCampus()
	if form.validate_on_submit():
		campus_db = model.campus()

		# Manually set ID to campus for proper functionality
		campus_db.key = ndb.Key('campus', form.campus.data)
		campus_db.put() #write to Datastore

		flask.flash('New Campus was created successfully!', category='success')
		return flask.redirect(flask.url_for('campus_list', order='-created'))

	# Pass information to HTML to render on website
	return flask.render_template(
		'campus_create.html',
		html_class='campus-create',
		title = 'Create Campus',
		form = form,
		)

# The link below displays all of the campus entities.
@app.route('/campus/')
@auth.login_required
def campus_list():
	# _dbs suffix is for list of entities, get_dbs() returns database object
	campus_dbs, campus_cursor = model.campus.get_dbs()
	campusNames = []

	for campus in campus_dbs:
		campusNames.append(campus.key.id())

	return flask.render_template(
		'campus_list.html',
		html_class = 'campus-list',
		title = 'Campus List',
		campus_dbs=campus_dbs,
		next_url=util.generate_next_url(campus_cursor),
		campusNames=campusNames,
		)

# This is the individual campus viewing link. Every campus created
# has a unique page that can view their individual properties
@app.route('/campus/<string:campus_id>/')
@auth.login_required
def campus_view(campus_id):
	campus_db = model.campus.get_by_id(campus_id)

	# Grab empty and total spaces then pass in render_template to HTML file
	empty = campus_db.emptySpaces
	total = campus_db.totalSpaces

	# Checker to ensure no divideByZero error occurrs
	percentage = 0
	if (total == 0) or (empty) == 0:
		percentage = 0
	else:
		percentage=(1-(empty/total)) * 100

	if not campus_db:
		flask.abort(404)

	return flask.render_template(
		'campus_view.html',
		html_class = 'campus-view',
		title=campus_db.key.id(),
		campus_db=campus_db,
		percentage=percentage,
		)

# Grabs entity, updates dateTime to show modification time, writes back to Datastore
@app.route('/campus/<campus_id>/update/', methods=['GET', 'POST'])
@auth.login_required
def campus_update(campus_id):
	campus_db = model.campus.get_by_id(campus_id)
	# campus_db = ndb.Key('campus', campus_id).get()
	print(campus_db)
	if not campus_db:
		flask.abort(404)

	form = NewCampus(obj=campus_db)
	new_campus_db = model.campus()
	if form.validate_on_submit():
		form.populate_obj(campus_db)
		campus_db.key.delete()
		new_campus_db.key = ndb.Key('campus', form.campus.data)
		new_campus_db.put()
		return flask.redirect(flask.url_for('campus_list', order='-modified'))

	return flask.render_template(
		'campus_update.html',
		html_class = 'campus-update',
		title=campus_db.key.id(),
		form=form,
		campus_db=campus_db,
		)