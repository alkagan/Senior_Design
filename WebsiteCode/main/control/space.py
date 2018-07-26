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

# Only one parameter to input for spaces as they absorb lot parameters
class NewSpace(flask_wtf.FlaskForm):
	numSpaces = wtforms.IntegerField('Number of Spaces', [wtforms.validators.required()])

class UpdateSpace(flask_wtf.FlaskForm):
	towerId = wtforms.StringField('Tower ID')
	permissions = wtforms.StringField('Permissions')

# Create space(s) for individual lot 
@app.route('/space/<campus_id>/<lot_id>/create/', methods=['GET', 'POST'])
@auth.login_required
def space_create(lot_id, campus_id):
	form = NewSpace()
	parse = []
	if form.validate_on_submit():
		space_db = model.space()
		space_db.log.append("I201801020304")

		# Iterate through and create as many spaces as inputted into the field.
		for i in range(1, form.numSpaces.data+1):
			space_db.key = ndb.Key('campus', campus_id, 'lot', lot_id, 'space', str(i))
			space_parent = space_db.key.parent().id()
			lot_parent = space_db.key.parent().parent()

			# Increment lot and campus information upon creation
			par_obj = model.lot.get_by_id(space_parent, parent=lot_parent)
			par_obj.totalSpaces += 1
			par_obj.emptySpaces += 1
			lot_par_obj = model.campus.get_by_id(lot_parent.id())
			lot_par_obj.totalSpaces += 1
			lot_par_obj.emptySpaces += 1

			# Grab permissions from parent lot
			space_db.permissions = par_obj.defaultPermissions

			# Write values to datastore
			lot_par_obj.put()
			par_obj.put()
			space_db.put()

		flask.flash('New Space was created successfully!', category='success')
		return flask.redirect(flask.url_for('space_list', order='-created'))

	return flask.render_template(
		'space_create.html',
		html_class='space-create',
		title = 'Create Space',
		form = form,
		lot_id=lot_id,
		campus_id=campus_id,
		)

# View all spaces 
@app.route('/space/')
@auth.login_required
def space_list():
	space_dbs, space_cursor = model.space.get_dbs()

	spaceNames = []
	lotNames = []
	campusNames = []

	# Iterate through space parent and lot parent to ensure proper ancestry
	# relations and display relations. 
	for space in space_dbs:
		parent = space.key.parent().get(use_cache=False, use_memcache=False)
		lotParent = space.key.parent().parent().get(use_cache=False, use_memcache=False)
		
		if parent is not None:
			lotNames.append(parent.key.id())
		else:
			lotNames.append("Failed to get lot")

		if lotParent is not None:
			campusNames.append(lotParent.key.id())
		else:
			campusNames.append("Failed to get campus")

		cast_to_int = int(space.key.id())
		print(cast_to_int)
		spaceNames.append(int(cast_to_int))

	return flask.render_template(
		'space_list.html',
		html_class = 'space-list',
		title = 'Space List',
		space_dbs=space_dbs,
		next_url=util.generate_next_url(space_cursor),
		spaceNames=spaceNames,
		lotNames=lotNames,
		campusNames=campusNames,
		)

# Individual space viewing
@app.route('/space/<campus_id>/<lot_id>/<space_id>/')
@auth.login_required
def space_view(campus_id, lot_id, space_id):
	space_db = ndb.Key('campus', campus_id, 'lot', lot_id, 'space', space_id).get(use_cache=False, use_memcache=False)
	if not space_db:
		flask.abort(404)

	length = len(space_db.log)
	# # Get log information from Datastore, parse it and create analytics
	if length:
		for i in range(0, length):
			parse = space_db.log[i]
			parsedString = parse[1:5] + '-' + parse[5:7] + '-' + parse[7:9] + '-' + parse[9:11]
			space_db.log[i] = [parsedString]

	return flask.render_template(
		'space_view.html',
		html_class = 'space-view',
		title=space_db.key.id(),
		space_db=space_db,
		length=length,
		)

# Update individual space for a lot, useful for permission changes
@app.route('/space/<campus_id>/<lot_id>/<space_id>/update/', methods=['GET', 'POST'])
@auth.login_required
def space_update(campus_id, lot_id, space_id):
	space_db = ndb.Key('campus', campus_id, 'lot', lot_id, 'space', space_id).get(use_cache=False, use_memcache=False)
	if not space_db:
		flask.abort(404)

	form = UpdateSpace(obj=space_db)
	if form.validate_on_submit():
		form.populate_obj(space_db)
		space_db.put()
		return flask.redirect(flask.url_for('space_list', order='-modified'))

	return flask.render_template(
		'space_update.html',
		html_class = 'space-update',
		form=form,
		space_db=space_db,
		)