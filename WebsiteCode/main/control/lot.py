'''
This file uses the Flask framework to create individual web pages
for our different methods (create, list, view, update). Whenever @app.route
is called a new page is generated and the template returns to the html
files to then display on the website. 
'''

import flask_wtf
import wtforms
from google.appengine.ext import ndb
from google.appengine.api import search
import flask
import auth
import model
from main import app
import util
import json

# This class contains lot information that the admin will be able to input.
# The GPS coordinates are optional and they default to 1.0,1.0.
class NewLot(flask_wtf.FlaskForm):
	lot = wtforms.StringField('Lot', [wtforms.validators.required()])
	defaultPermissions = wtforms.StringField('Default Permissions', [wtforms.validators.required()])
	latitude = wtforms.FloatField('Lot Lat', default=1.0)
	longitude = wtforms.FloatField('Lot Long', default=1.0)

class UpdateLot(flask_wtf.FlaskForm):
	defaultPermissions = wtforms.StringField('Default Permissions', [wtforms.validators.required()])
	currentPermissions = wtforms.StringField('Current Permissions', [wtforms.validators.required()])
	latitude = wtforms.FloatField('Lot Lat', default=1.0)
	longitude = wtforms.FloatField('Lot Long', default=1.0)

# We pass the campus_id as a parameter since we cannot create a lot with
# a parent campus. 
@app.route('/lot/<campus_id>/create/', methods=['GET', 'POST'])
@auth.login_required
def lot_create(campus_id):
	form = NewLot()
	if form.validate_on_submit():
		lot_db = model.lot(
			defaultPermissions = form.defaultPermissions.data,
			latitude = form.latitude.data,
			longitude = form.longitude.data,
			)

		lot_db.log.append("I201801020304")

		# Manually setting ID
		lot_db.key = ndb.Key('campus', campus_id, 'lot', form.lot.data)

		# Get the model from the key, increment the total number of lots 
		lot_parent = lot_db.key.parent().id()
		parent_obj = model.campus.get_by_id(lot_parent)
		parent_obj.totalLots += 1
		lot_db.currentPermissions = lot_db.defaultPermissions 

		# Write to Datastore
		lot_db.put()
		parent_obj.put()

		flask.flash('New Lot was created successfully!', category='success')
		return flask.redirect(flask.url_for('lot_list', order='-created'))

	return flask.render_template(
		'lot_create.html',
		html_class='lot-create',
		title = 'Create Lot',
		form = form,
		campus_id=campus_id, 
		)

# Displays all lots
@app.route('/lot/')
@auth.login_required
def lot_list():
	lot_dbs, lot_cursor = model.lot.get_dbs()

	lotNames = []
	campusNames = []

	for lot in lot_dbs:
		parent = lot.key.parent().get(use_cache=False, use_memcache=False)
		if parent is not None:
			campusNames.append(parent.key.id())
		else:
			campusNames.append("Failed to get campus") 
		lotNames.append(lot.key.id())

	totalLots = len(lotNames)

	return flask.render_template(
		'lot_list.html',
		html_class = 'lot-list',
		title = 'Lot List',
		lot_dbs=lot_dbs,
		next_url=util.generate_next_url(lot_cursor),
		campusNames=campusNames,
		lotNames=lotNames,
		totalLots=totalLots,
		)

# Individual lot pages
@app.route('/lot/<campus_id>/<lot_id>/')
@auth.login_required
def lot_view(campus_id, lot_id):
	lot_db = ndb.Key('campus', campus_id, 'lot', lot_id).get(use_cache=False, use_memcache=False)

	if not lot_db:
		flask.abort(404)

	empty = float(lot_db.emptySpaces)
	total = float(lot_db.totalSpaces)

	# Divide by zero error checker
	if (total == 0) or (empty == 0):
		percentage = 0
	else:
		percentage=(1-(empty/total)) * 100

	percentageFormatted = float("{0:.2f}".format(percentage))

	length = len(lot_db.log)

	event = []
	hourMinute = []
	
	# Get log information from Datastore, parse it and create analytics
	if length:
		for i in range(1, length):
			parse = lot_db.log[i]
			parsedString = parse[0:5] + '-' + parse[5:7] + '-' + parse[7:9] + '-' + parse[9:11] + '-' + parse[11:13] + '-' + parse[13:]
			hourMinute.append(float(parse[9:11] + '.' + parse[11:13]))
		
			# Pull-in/Pull-out event indicator
			event.append(parse[0])

			# Update log with parsed string to be more human-friendly
			lot_db.log[i] = [parsedString]

	return flask.render_template(
		'lot_view.html',
		html_class = 'lot-view',
		title=lot_db.key.id(),
		lot_db=lot_db,
		percentage=percentageFormatted,
		length=length,
		event=event,
		hourMinute=hourMinute,
		)

# Update individual campus properties
@app.route('/lot/<campus_id>/<lot_id>/update/', methods=['GET', 'POST'])
@auth.login_required
def lot_update(campus_id, lot_id):
	lot_db = ndb.Key('campus', campus_id, 'lot', lot_id).get(use_cache=False, use_memcache=False)
	if not lot_db:
		flask.abort(404)

	form = UpdateLot(obj=lot_db)
	if form.validate_on_submit():
		form.populate_obj(lot_db)
		lot_db.put()
		return flask.redirect(flask.url_for('lot_list', order='-modified'))

	return flask.render_template(
		'lot_update.html',
		html_class = 'lot-update',
		form=form,
		lot_db=lot_db,
		)