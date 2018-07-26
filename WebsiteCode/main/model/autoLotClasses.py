'''
This file contains the classes from which we create our Datastore entities.
They each have properties appropriate to their specific fields and default values.
'''

from google.appengine.ext import ndb
from google.appengine.api import search
import model

class campus(model.Base):
	totalLots = ndb.IntegerProperty(default = 0)
	totalSpaces = ndb.IntegerProperty(default = 0)
	emptySpaces = ndb.IntegerProperty(default = 0)
	dateTime = ndb.DateTimeProperty(auto_now_add=True)

class lot(model.Base):
 	defaultPermissions = ndb.StringProperty(default = '')
	currentPermissions = ndb.StringProperty(default = '')
	totalSpaces = ndb.IntegerProperty(default = 0)
	emptySpaces = ndb.IntegerProperty(default = 0)
	latitude = ndb.FloatProperty(default = 1.0)
	longitude = ndb.FloatProperty(default = 1.0)
	log = ndb.StringProperty(repeated=True) # Creates list of strings with 'repeated'

class space(model.Base):
	towerId = ndb.StringProperty(required=True, default = '-1')
	occupied = ndb.BooleanProperty(default = False)
	permissions = ndb.StringProperty(default = '')
	battery = ndb.IntegerProperty(default = 0)
	errors = ndb.StringProperty(default = 'None')
	dateTime = ndb.DateTimeProperty(auto_now_add=True)	
	log = ndb.StringProperty(repeated=True)