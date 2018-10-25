import os, logging, wsgiref.handlers, datetime, random, math, string, urllib, csv, json, time, hashlib

from google.appengine.ext import webapp, db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from gaesessions import get_current_session
from google.appengine.api import urlfetch

LengthOfData = 48
LengthOfPractice=30
NumScenarios=2
rewardAmount = 6 # number of cents added/subtracted for a good/bad outcome

# test test
# session variables:
# account
# BonusOne
# BonusTwo
# scenario
# testOrder
# trialGuesses
# userkey
# usernum
# trialNumber
# reloads
# v1_Data
# v2_Data
# frequency1
# frequency2
# position2
# var1_Names
# var2_Names
# condition
# drugColors
# diseaseNames


###############################################################################
###############################################################################
######################## Data Classes for Database ############################
###############################################################################
###############################################################################

class User(db.Model):
	usernum =			db.IntegerProperty()
	account = 			db.StringProperty()
	browser =			db.StringProperty()
	sex =				db.IntegerProperty()
	ethnicity =			db.IntegerProperty()
	race =				db.IntegerProperty()
	age = 				db.IntegerProperty()
	Bonuses =			db.IntegerProperty()
	testOrder =			db.IntegerProperty()
	reloads =			db.IntegerProperty()
	v1_Data =			db.ListProperty(int)
	v2_Data =			db.ListProperty(int)
	frequency1 =		db.IntegerProperty()
	frequency2 =		db.ListProperty(int)
	position2 =			db.IntegerProperty()
	var1_Names =		db.ListProperty(str)
	var2_Names =		db.ListProperty(str)
	condition =			db.StringProperty() #gain/loss
	storyCondition =	db.StringProperty() # story/monetary/combined
	drugColors =		db.ListProperty(str)
	diseaseNames =		db.ListProperty(str)
	progress =			db.IntegerProperty()
	totalTrials = 		db.IntegerProperty()
	testAttempts = 		db.ListProperty(int)
	Completion_Code = 	db.IntegerProperty()



class ScenarioData(db.Model):
	# user/scenario stuff
	user  =				db.ReferenceProperty(User)
	account = 			db.StringProperty()
	usernum =			db.IntegerProperty()
	scenario = 			db.IntegerProperty()

	# visuals
	var1_Left = 		db.StringProperty()
	var1_Right = 		db.StringProperty()

	var2_Left =			db.StringProperty()
	var2_Right =		db.StringProperty()

	# attention variables
	trialTime = 		db.IntegerProperty()
	attentionFails =	db.IntegerProperty()
	reloads = 			db.IntegerProperty()

	# actual data
	trialNumber = 		db.IntegerProperty()
	trialGuess = 		db.StringProperty()
	profitImpact = 		db.IntegerProperty()
	valence = 			db.StringProperty() # within-subs valence condition; 0 means rare-positive, 1 means rare-negative
	storyCondition =	db.StringProperty() # constant storyCondition; monetary, story, combined
	condition = 		db.StringProperty() # gain/loss
	var1_value = 		db.StringProperty()
	var2_value =		db.StringProperty()
	frequency1 =		db.IntegerProperty()
	frequency2 = 		db.IntegerProperty()
	position2 = 		db.IntegerProperty()






class FinalJudgmentData(db.Model):
	user  =				db.ReferenceProperty(User)
	account = 			db.StringProperty()
	usernum =			db.IntegerProperty()
	scenario = 			db.IntegerProperty()
	valence = 			db.StringProperty() # 0 means rare-positive
	storyCondition = 	db.StringProperty() # monetary, story, combined
	condition = 		db.StringProperty() # gain/loss

	# visuals
	# in the story storyConditions these are drug names
	# in the monetary storyConditions, they are shapes
	var1_Left = 		db.StringProperty()
	var1_Right = 		db.StringProperty()

	# in the story storyConditions these are faces
	# in the monetary storyCondition they are shapes
	var2_Left =			db.StringProperty()
	var2_Right =		db.StringProperty()

	drugColor_Left =	db.StringProperty()
	drugColor_Right =	db.StringProperty()

	frequency1 =		db.IntegerProperty() # which var1 value is common (left or right)
	frequency2 =		db.IntegerProperty() # which var2 value is common (left or right)
	position2 =			db.IntegerProperty() # more of a sanity check than anything

	# given var1, estimates of var2
	var2a_given_var1a = 	db.IntegerProperty()
	var2b_given_var1a = 	db.IntegerProperty()
	var2a_given_var1b =		db.IntegerProperty()
	var2b_given_var1b =		db.IntegerProperty()

	# given var2, estimates of var1
	var1a_given_var2a =		db.IntegerProperty()
	var1b_given_var2a =		db.IntegerProperty()
	var1a_given_var2b =		db.IntegerProperty()
	var1b_given_var2b =		db.IntegerProperty()

	# causal judgment; this is changing for E1
	# which var1 would you prefer? lower outcomes are preferences for left value
	causalJudgment =	db.IntegerProperty()
	testOrder =			db.IntegerProperty()


#This stores the current number of participants who have ever taken the study.
#see https://developers.google.com/appengine/docs/pythondatastore/transactions
#could also use get_or_insert
#https://developers.google.com/appengine/docs/pythondatastore/modelclass#Model_get_or_insert
class NumOfUsers(db.Model):
	counter = db.IntegerProperty(default=0)


#Increments NumOfUsers ensuring strong consistency in the datastore
@db.transactional
def create_or_increment_NumOfUsers():
	obj = NumOfUsers.get_by_key_name('NumOfUsers', read_policy=db.STRONG_CONSISTENCY)
	if not obj:
		obj = NumOfUsers(key_name='NumOfUsers')
	obj.counter += 1
	x=obj.counter
	obj.put()
	return(x)



###############################################################################
###############################################################################
########################### From Book Don't Touch #############################
###############################################################################
###############################################################################
# One line had to be updated for Python 2.7
#http://stackoverflow.com/questions/16004135/python-gae-assert-typedata-is-stringtype-write-argument-must-be-string
# A helper to do the rendering and to add the necessary
# variables for the _base.htm template
def doRender(handler, tname = 'index.htm', values = { }):
	temp = os.path.join(
			os.path.dirname(__file__),
			'templates/' + tname)
	if not os.path.isfile(temp):
		return False
	# Make a copy of the dictionary and add the path and session
	newval = dict(values)
	newval['path'] = handler.request.path
#   handler.session = Session()
#   if 'username' in handler.session:
#      newval['username'] = handler.session['username']

	outstr = template.render(temp, newval)
	handler.response.out.write(unicode(outstr))  #### Updated for Python 2.7
	return True


###############################################################################
###############################################################################
###################### Handlers for Individual Pages ##########################
###############################################################################
###############################################################################

###############################################################################
################################ Ajax Handler #################################
###############################################################################

class AjaxHandler(webapp.RequestHandler):
	def get(self):
		que=db.Query(ScenarioData)
		que.order("usernum").order("trialNumber")
		d=que.fetch(limit=10000)
		doRender(self, 'ajax.htm',{'d':d})

	def post(self):
		self.session=get_current_session()

		scenario = self.session['scenario']

  		trialTime = int(self.request.get('timeInput'))
  		attentionFails = int(self.request.get('attentionFailsInput'))
		trialNumber = int(self.request.get('trialInput'))
		trialGuess = str(self.request.get('guessInput'))
		profitImpact = int(self.request.get('profitImpactInput'))
		
		# trials = int(self.request.get('totalTrialInput')) 
		# total number of trials (in the experiment), to track refreshes

		self.session['runningBonuses'] = int(self.request.get('runningBonusInput'))
		
		valence = self.request.get('valenceInput')
		var1_value = str(self.request.get('var1_value'))
		var2_value = str(self.request.get('var2_value'))

		self.session['trialNumber'] = int(self.request.get('trialNumberInput'))
		self.session['reloads'] = int(self.request.get('reloadsInput'))

		var1_Left = self.session['var1_Names'][2*scenario]
		var1_Right = self.session['var1_Names'][2*scenario+1]
		var2_Left = self.session['var2_Names'][2*scenario]
		var2_Right = self.session['var2_Names'][2*scenario+1]
		

		# how to check if there are example rows in the datastore
		que = db.Query(ScenarioData).filter('usernum =', self.session['usernum']).filter('scenario =', self.session['scenario']).filter('trialNumber =', trialNumber)
		results = que.fetch(limit=1000)

		# make all of the data items into 3-value arrays, then make a loop to put them in the datastore
		if (len(results) == 0):
			newajaxmessage = ScenarioData(
				user=self.session['userkey'],
				usernum = self.session['usernum'],
				account = self.session['account'],
				scenario = self.session['scenario'],
				var1_Left = var1_Left,
				var1_Right = var1_Right,
				var2_Left = var2_Left,
				var2_Right = var2_Right,
				trialTime = trialTime,
				attentionFails = attentionFails,
				trialNumber = trialNumber,
				reloads		= self.session['reloads'],
				trialGuess = trialGuess,
				# trialCorrect = trialCorrect,
				profitImpact = profitImpact,
				valence = valence,
				condition = self.session['condition'],
				var1_value = str(var1_value),
				var2_value = str(var2_value),
				frequency1 = self.session['frequency1'],
				frequency2 = self.session['frequency2'][scenario],
				position2 = self.session['position2']); # this is the match between position2 and frequency2; sent to this handler as 'rare-positive' or 'rare-negative'


			newajaxmessage.put()
			self.response.out.write({}) # not sure what this does?

		else:

			obj = que.get()
			obj.user=self.session['userkey']
			obj.usernum = self.session['usernum']
			obj.account = self.session['account']
			obj.scenario = self.session['scenario']

			obj.var1_Left = var1_Left
			obj.var1_Right = var1_Right
			obj.var2_Left = var2_Left
			obj.var2_Right = var2_Right

			obj.trialTime = trialTime
			obj.attentionFails = attentionFails
			obj.trialNumber = trialNumber
			obj.reloads = self.session['reloads']
			obj.trialGuess = trialGuess
			# obj.trialCorrect = trialCorrect
			obj.profitImpact = profitImpact
			obj.valence = valence
			obj.var1_value = var1_value
			obj.var2_value = var2_value
			obj.condition = self.session['condition']

			obj.frequency1 = self.session['frequency1']
			obj.frequency2 = self.session['frequency2'][scenario]
			obj.position2 = self.session['position2']

			obj.put()
			self.response.out.write({}) # ?

		que2 = db.Query(User).filter('usernum =', self.session['usernum'])
		obj = que2.get()

		obj.Bonuses = self.session['runningBonuses']
		obj.reloads = self.session['reloads']
		obj.totalTrials += 1
		obj.put()
		self.response.out.write({}) # ?

		

class AjaxMemoryHandler(webapp.RequestHandler):
	def get(self):
		que=db.Query(FinalJudgmentData)
		que.order("usernum").order("scenario").order("judgmentNumber")
		d=que.fetch(limit=10000)
		doRender(self, 'ajaxTest.htm',{'d':d})

	def post(self):
		self.session=get_current_session()

		# testOrder = 0: memory first
		# memOrder = 0: ask about outcomes given drug first

		# TO = 0, MO = 0: E|C, C|E, Causal
		# TO = 0, MO = 1: C|E, E|C, Causal
		# TO = 1, MO = 0: Causal, E|C, C|E
		# TO = 1, MO = 1: Causal, C|E, E|C

		if (int(self.session['testOrder']) == 0) & (int(self.session['memOrder']) == 0):
			judgmentOrder = 0 # E|C, C|E, Causal
		elif (int(self.session['testOrder']) == 0) & (int(self.session['memOrder']) == 1):
			judgmentOrder = 1 # C|E, E|C, Causal
		elif (int(self.session['testOrder']) == 1) & (int(self.session['memOrder']) == 0):
			judgmentOrder = 2 # Causal, E|C, C|E
		elif (int(self.session['testOrder']) == 1) & (int(self.session['memOrder']) == 1):
			judgmentOrder = 3 # Causal, C|E, E|C
		else:
			judgmentOrder = 100

  		usernum = self.session['usernum']
  		scenario = self.session['scenario']

  		valence = str(self.request.get('valence')) # this is the match between position2 and frequency2; sent to this handler as 'rare-positive' or 'rare-negative'
		condition = str(self.request.get('condition')) # gain/loss
  		leftDrugName = str(self.request.get('leftDrugName'))
  		rightDrugName = str(self.request.get('rightDrugName'))
  		leftDrugRarity = str(self.request.get('leftDrugRarity'))
  		rightDrugRarity = str(self.request.get('rightDrugRarity'))
		leftDrugColor = str(self.request.get('leftDrugColor'))
  		rightDrugColor = str(self.request.get('rightDrugColor'))
  		leftNumberBad = int(self.request.get('leftNumberBad'))
  		rightNumberBad = int(self.request.get('rightNumberBad'))
  		goodOutcomesLeft = int(self.request.get('goodOutcomesLeft'))
  		goodOutcomesRight = int(self.request.get('goodOutcomesRight'))
  		badOutcomesLeft = int(self.request.get('badOutcomesLeft'))
  		badOutcomesRight = int(self.request.get('badOutcomesRight'))

  		logging.info("usernum: " + str(usernum))
  		logging.info('account: ' + str(self.session['account']))
  		logging.info("valence: "+ str(valence))
		logging.info("condition: "+ str(condition))
  		logging.info("leftDrugName: "+ str(leftDrugName))
  		logging.info("rightDrugName: "+ str(rightDrugName))
  		logging.info("leftDrugRarity: "+ str(leftDrugRarity))
  		logging.info("rightDrugRarity: "+ str(rightDrugRarity))
		logging.info("leftDrugColor: "+ str(leftDrugColor))
  		logging.info("rightDrugColor: "+ str(rightDrugColor))
  		logging.info("leftNumberBad: "+ str(leftNumberBad))
  		logging.info("rightNumberBad: "+ str(rightNumberBad))
  		logging.info("goodOutcomesLeft: "+ str(goodOutcomesLeft))
  		logging.info("goodOutcomesRight: "+ str(goodOutcomesRight))
  		logging.info("badOutcomesLeft: "+ str(badOutcomesLeft))
  		logging.info("badOutcomesRight: "+ str(badOutcomesRight))
  		logging.info("memOrder: " + str(self.session['memOrder']))
  		logging.info("testOrder: " + str(self.session['testOrder']))
  		logging.info("judgmentOrder: "+ str(judgmentOrder))


  		judgmentOrder = judgmentOrder




		que = db.Query(FinalJudgmentData).filter('usernum =', self.session['usernum']).filter('scenario =', scenario)
		results = que.fetch(limit=1000)


		# make all of the data items into 3-value arrays, then make a loop to put them in the datastore
		if (len(results) == 0):
			logging.info('NEW ENTRY')
			newajaxmessage = FinalJudgmentData(
				# user properties
				user=self.session['userkey'],
				usernum = usernum,
				account = self.session['account'],
				# scenario properties
				scenario = scenario,
				valence = valence,
				condition = condition,
				# drug properties
				leftDrugName = leftDrugName,
				rightDrugName = rightDrugName,
				leftDrugRarity = leftDrugRarity, # DO THESE
				rightDrugRarity = rightDrugRarity,
				leftDrugColor = leftDrugColor,
				rightDrugColor = rightDrugColor,
				leftNumberBad = leftNumberBad,
				rightNumberBad = rightNumberBad,
				goodOutcomesLeft = goodOutcomesLeft,
				goodOutcomesRight = goodOutcomesRight,
				badOutcomesLeft = badOutcomesLeft,
				badOutcomesRight = badOutcomesRight,
				# causalJudgment = causalJudgment, Not this handler
				judgmentOrder = judgmentOrder);

			newajaxmessage.put()
			self.response.out.write({}) # not sure what this does?

		else:
			logging.info('UPDATING CURRENT')
			obj = que.get()

			# user properties
			obj.user=self.session['userkey']
			obj.usernum = usernum
			obj.account = self.session['account']

			# scenario properties
			obj.scenario = scenario
			obj.condition = condition
			obj.valence = valence

			# drug properties
			obj.leftDrugName = leftDrugName
			obj.rightDrugName = rightDrugName
			obj.leftDrugRarity = leftDrugRarity # DO THESE
			obj.rightDrugRarity = rightDrugRarity
			obj.leftDrugColor = leftDrugColor
			obj.rightDrugColor = rightDrugColor
			obj.leftNumberBad = leftNumberBad
			obj.rightNumberBad = rightNumberBad
			obj.goodOutcomesLeft = goodOutcomesLeft
			obj.goodOutcomesRight = goodOutcomesRight
			obj.badOutcomesLeft = badOutcomesLeft
			obj.badOutcomesRight = badOutcomesRight
			# causalJudgment = causalJudgment, Not this handler
			obj.judgmentOrder = judgmentOrder

			obj.put()
			self.response.out.write({}) # ?


class AjaxCausalHandler(webapp.RequestHandler):
	def get(self):
		# I don't even think I need this handler...
		que=db.Query(FinalJudgmentData)
		que.order("usernum").order("scenario").order("judgmentNumber")
		d=que.fetch(limit=10000)
		doRender(self, 'ajaxCausalTest.htm',{'d':d})

	def post(self):
		self.session=get_current_session()
		# message=str(self.request.get('message'))

		usernum = self.session['usernum']
		scenario = self.session['scenario']

		causalJudgment = int(self.request.get('judgmentInput'))


  		usernum = self.session['usernum']
  		scenario = self.session['scenario']

  		logging.info("usernum: " + str(usernum))
  		logging.info('account: ' + str(self.session['account']))
  		logging.info('scenario: '+str(scenario))



		# how to check if there are example rows in the datastore
		que = db.Query(FinalJudgmentData).filter('usernum =', self.session['usernum']).filter('scenario =', scenario)
		results = que.fetch(limit=1000)

		# make all of the data items into 3-value arrays, then make a loop to put them in the datastore
		if (len(results) == 0):
			logging.info('NEW ENTRY')
			newajaxmessage = FinalJudgmentData(

				user=self.session['userkey'],
				usernum = usernum,
				account = self.session['account'],
				scenario = scenario,
				causalJudgment = causalJudgment);


			newajaxmessage.put()
			self.response.out.write({}) # not sure what this does?

		else:
			logging.info('UPDATING CURRENT')
			obj = que.get()

			obj.user=self.session['userkey']
			obj.usernum = usernum
			obj.account = self.session['account']
			obj.scenario = scenario
			obj.causalJudgment = causalJudgment

			obj.put()
			self.response.out.write({}) # ?


###############################################################################
############################## ScenarioHandler ################################
###############################################################################
# The main handler for all the "scenarios" (e.g., one patient)
class ScenarioHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()

		try:
			scenario = self.session['scenario']
			obj = User.get(self.session['userkey']); # I didn't know you could do it this way!

			if scenario == 0:
				obj.progress = 1
			else:
				obj.progress = 3

			obj.put()

			group = self.session['v1_Data'][scenario]
			data = self.session['v2_Data'][scenario]

			logging.info('BONUS: '+str(self.session['runningBonuses']))

			doRender(self, 'scenario.htm',
				{'usernum':self.session['usernum'],
				'test': 0,
				'bonus': self.session['runningBonuses'],
				'storyCondition': self.session['storyCondition'], # monetary, story, combined
				'condition':self.session['condition'], # gain/loss
				'var1_Names_Left': self.session['var1_Names'][2*scenario],
				'var1_Names_Right': self.session['var1_Names'][2*scenario+1],
				'var2_Names_Left': self.session['var2_Names'][2*scenario],
				'var2_Names_Right': self.session['var2_Names'][2*scenario+1],
				'disease': self.session['diseaseNames'][scenario],
				'drugColor_Left': self.session['drugColors'][2*scenario],
				'drugColor_Right': self.session['drugColors'][2*scenario+1],
				'v1_Data':self.session['v1_Data'][scenario], # var1
				'v2_Data':self.session['v2_Data'][scenario], # var2
				'testOrder':self.session['testOrder'],
				'trialGuesses':self.session['trialGuesses'],
				# 'trialNumber':0, # testing
				'trialNumber': self.session['trialNumber'],
				# 'reloads':0, # testing
				'reloads': self.session['reloads'],
				'frequency1': self.session['frequency1'],
				'frequency2': self.session['frequency2'][scenario],
				'position2': self.session['position2'],
				'rewardAmount':rewardAmount})

		except KeyError:
			doRender(self, 'mturkid.htm',
				{'error':1})

	def post(self):
		self.session = get_current_session()

		scenario = self.session['scenario'] # for readability
		logging.info('SCENARIO: '+str(scenario))

		bonus = int(self.request.get('BonusInput2'))
		# this is the hackiest solution ever but fuck it, it works now.
		# method to this madness: when I was using AJAX to track bonuses I was running into 
		# consistency problems in the session. Still don't know why...bonus would render in final judgment
		# page as being (rewardAmt - bonusAmt) too large. This fixes that even though it's an ugly solution.
		# Side note: I really would like to know why it was doing that...


		u = db.Query(User).filter('usernum =', self.session['usernum'])
		obj = u.get()
		obj.Bonuses = bonus
		obj.testAttempts[self.session['scenario']] += 1
		self.session['testAttempts'] = obj.testAttempts
		obj.put()
		
		# self.session['testAttempts'][self.session['scenario']] += 1 # make sure they're not reloading the test page!
		

		
		doRender(self, 'test.htm',{

			'bonus': bonus,
			'scenario': self.session['scenario'],
			'frequency1': self.session['frequency1'],
			'frequency2': self.session['frequency2'][scenario],
			'storyCondition': self.session['storyCondition'], # combined/story/monetary valence
			'condition': self.session['condition'], # gain/loss
			'testOrder': self.session['testOrder'],
			'disease': self.session['diseaseNames'][scenario],
			'var1_Names_Left': self.session['var1_Names'][2*scenario],
			'var1_Names_Right': self.session['var1_Names'][2*scenario+1],
			'var2_Names_Left': self.session['var2_Names'][2*scenario],
			'var2_Names_Right': self.session['var2_Names'][2*scenario+1],
			'drugColor_Left': self.session['drugColors'][2*scenario],
			'drugColor_Right': self.session['drugColors'][2*scenario+1],
			'position2': self.session['position2'],
			'rewardAmount':rewardAmount}) # this is a global variable set at the very top (is this a bad practice?)

	


class ProgressCheckHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()

		logging.info('HANDLER IS HANDLING')
		o = User.get(self.session['userkey']);
		p = o.progress

		# p = 2
		if (p == 2) | (p == 4):
			p = 2

		logging.info('PROGRESS: '+str(p))

		# create json object to send back as "data"
		data = json.dumps(p)

		# self.response.headers['Content-Type'] = 'application/json; charset=UTF-8'
		self.response.out.write(data) # this is the function you need!



class FinalJudgmentHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()

		doRender(self, 'mturkid.htm',
			{'error':2})
		

	def post(self):

		self.session = get_current_session()

		# write data

		scenario = self.session['scenario']
		logging.info('SCENARIO: '+str(scenario))
		if(scenario >= NumScenarios): # refresh problem
			doRender(self, 'mturkid.htm',
				{'error':2})
		
		else:
			self.session['runningBonuses'] = int(self.request.get('runningBonusInput'))




			# logging.info('valence: '+valence)
			obj = FinalJudgmentData(
				user = self.session['userkey'],
				usernum = self.session['usernum'],
				account = self.session['account'],
				scenario = self.session['scenario'],
				valence = self.request.get('valence'),
				condition = self.session['condition'],

				# testAttempts = self.session['testAttempts'],

				var1_Left = self.request.get('var1a_Name'),
				var1_Right = self.request.get('var1b_Name'),
				var2_Left = self.request.get('var2a_Name'),
				var2_Right = self.request.get('var2b_Name'),

				drugColor_Left = self.request.get('leftDrugColor'),
				drugColor_Right = self.request.get('rightDrugColor'),

				frequency1 = self.session['frequency1'],
				frequency2 = self.session['frequency2'][scenario],
				position2 = self.session['position2'],

				var2a_given_var1a = int(self.request.get('var2a_given_var1a')),
				var2b_given_var1a = int(self.request.get('var2b_given_var1a')),
				var2a_given_var1b = int(self.request.get('var2a_given_var1b')),
				var2b_given_var1b = int(self.request.get('var2b_given_var1b')),
				var1a_given_var2a = int(self.request.get('var1a_given_var2a')),
				var1b_given_var2a = int(self.request.get('var1b_given_var2a')),
				var1a_given_var2b = int(self.request.get('var1a_given_var2b')),
				var1b_given_var2b = int(self.request.get('var1b_given_var2b')),

				causalJudgment = int(self.request.get('causalJudgment')),
				testOrder = int(self.request.get('testOrder')),
				Bonuses = int(self.session['runningBonuses'])
			);

			obj.put()

			self.session['scenario'] += 1
			
			# if self.session['scenario'] > 1:

			# 	self.session['scenario'] = 1 # testing

			scenario=self.session['scenario']

		
			
			if scenario<=NumScenarios-1: #have more scenarios to go
				obj = User.get(self.session['userkey']);
				obj.progress = 2
				obj.put()

				self.session['trialNumber'] = 0
				self.session['reloads']		= 0

				disease = self.session['diseaseNames'][scenario]
				var1_Names_Left = self.session['var1_Names'][2*scenario]
				var1_Names_Right = self.session['var1_Names'][2*scenario+1]
				var2_Names_Left = self.session['var2_Names'][2*scenario]
				var2_Names_Right = self.session['var2_Names'][2*scenario+1]


				condition = self.session['condition'] # gain/loss


				logging.info("PRESCENARIO HANDLER")
				doRender(self, 'prescenario.htm',
					{'disease':disease,
					'var1_Left_Name': var1_Names_Left,
					'var1_Right_Name': var1_Names_Right,
					'var2_Left_Name': var2_Names_Left,
					'var2_Right_Name': var2_Names_Right,
					'frequency1': self.session['frequency1'],
					'frequency2': self.session['frequency2'][scenario],
					'condition':condition,
					'drugColor_Left': self.session['drugColors'][2*scenario],
					'drugColor_Right': self.session['drugColors'][2*scenario+1],
					'position2':self.session['position2'],
					'scenario':self.session['scenario']})


			else:

				obj = User.get(self.session['userkey']);
				obj.progress = 4
				obj.put()
				doRender(self, 'demographics.htm')
			




###############################################################################
############################## Small Handlers #################################
###############################################################################

class TestHandler(webapp.RequestHandler):	# handler that renders a specific page, for testing purposes
	def get(self):
		return

class InstructionsHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()
		doRender(self, 'task.htm',
			{'position2':self.session['position2'],
			'storyCondition': self.session['storyCondition'],
			'condition':self.session['condition']})

class preScenarioHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()
		scenario = self.session['scenario']
		disease = self.session['diseaseNames'][scenario]
		var1_Names_Left = self.session['var1_Names'][2*scenario]
		var1_Names_Right = self.session['var1_Names'][2*scenario+1]
		var2_Names_Left = self.session['var2_Names'][2*scenario]
		var2_Names_Right = self.session['var2_Names'][2*scenario+1]


		storyCondition = self.session['storyCondition'] # monetary, combined, story

		logging.info("PRESCENARIO HANDLER")
		doRender(self, 'prescenario.htm',
			{'disease':disease,
			'scenario':scenario,
			'var1_Left_Name': var1_Names_Left,
			'var1_Right_Name': var1_Names_Right,
			'var2_Left_Name': var2_Names_Left,
			'var2_Right_Name': var2_Names_Right,
			'frequency1': self.session['frequency1'],
			'frequency2': self.session['frequency2'][0],
			'storyCondition':storyCondition,
			'drugColor_Left': self.session['drugColors'][2*scenario],
			'drugColor_Right': self.session['drugColors'][2*scenario+1],
			'position2':self.session['position2']}) # don't need scenario, it's always 0



class DataHandler(webapp.RequestHandler):
	def get(self):
		self.session = get_current_session()

		doRender(self, 'datalogin.htm')


	def post(self):
		self.session = get_current_session()

		page = self.request.get('whichPage')

		# much more secure method of password protecting our data
		password=str(self.request.get('password'))
		output = str(hashlib.sha1(password).hexdigest())
		if output == '3fcfd14762bd3087e8563832e048945e50df7f80': # matching password, access data

			# filter usernum so we grab a little bit of data at a time, not all at once. 
			# first round was up to usernum = 70
			que=db.Query(ScenarioData)
			que.filter("usernum <", 70).order("usernum").order("scenario").order("trialNumber")
			d=que.fetch(limit=10000)

			que2=db.Query(User)
			que2.filter("usernum >", 100).order("usernum")
			u=que2.fetch(limit=10000)

			que3 = db.Query(FinalJudgmentData)
			que3.filter("usernum <", 260).order("usernum").order("scenario")
			t = que3.fetch(limit=10000)

			if page == 'scenario':
				doRender(
					self,
					'data.htm',
					{'d':d})

			elif page == 'user':
				doRender(
					self,
					'userData.htm',
					{'u':u})

			else:
				doRender(self, 'ajaxTest.htm',
					{'t':t})

		else:
			doRender(self, 'dataloginfail.htm')




class QualifyHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'qualify.htm')

class DNQHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'do_not_qualify.htm')

##############################################################################
############################ DemographicsHandler #############################
##############################################################################
# This handler is a bit confusing - it has all this code to calculate the
# correct race number

class DemographicsHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'demographics.htm')

	def post(self):
		self.session=get_current_session()
		bonus = self.session['runningBonuses']
		Completion_Code=random.randint(10000000,99999999)
		try:


			sex=int(self.request.get('sex'))
			ethnicity=int(self.request.get('ethnicity'))
			racel=map(int,self.request.get_all('race')) #race list

			age=int(self.request.get('ageInput'))

			logging.info("race list")
			logging.info(racel)

			rl1=int(1 in racel)
			rl2=int(2 in racel)
			rl3=int(3 in racel)
			rl4=int(4 in racel)
			rl5=int(5 in racel)
			rl6=int(6 in racel)
			rl7=int(7 in racel)

	#Amer Indian, Asian, Native Hawaiian, Black, White, More than one, No Report
	#race_num is a number corresponding to a single race AmerInd (1) - White(5)
			race_num=rl1*1+rl2*2+rl3*3+rl4*4+rl5*5

			morethanonerace=0
			for i in [rl1,rl2,rl3,rl4,rl5]:
					if i==1:
							morethanonerace+=1
			if rl6==1:
					morethanonerace+=2

			if rl7==1:  #dont want to report
					race=7
			elif morethanonerace>1:
					race=6
			elif morethanonerace==1:
					race=race_num

			logging.info("race")
			logging.info(race)



			


			obj = User.get(self.session['userkey']);
			obj.Completion_Code = Completion_Code
			obj.sex = sex
			obj.ethnicity = ethnicity
			obj.race = race
			obj.age = age
			
			obj.Bonuses = bonus
			obj.put();



			self.session.__delitem__('account')
			
			self.session.__delitem__('trials')
			self.session.__delitem__('storyCondition')
			self.session.__delitem__('condition')
			self.session.__delitem__('frequency2')
			self.session.__delitem__('diseaseNames')
			self.session.__delitem__('drugColors')
			self.session.__delitem__('drugNames')
			self.session.__delitem__('position2')
			self.session.__delitem__('negGroupData')
			self.session.__delitem__('negParadigmData')
			self.session.__delitem__('posGroupData')
			self.session.__delitem__('posParadigmData')
			self.session.__delitem__('position1')
			self.session.__delitem__('runningBonuses')
			self.session.__delitem__('scenario')
			self.session.__delitem__('testOrder')
			self.session.__delitem__('trialGuesses')
			self.session.__delitem__('userkey')
			self.session.__delitem__('usernum')



			doRender(self, 'logout.htm',
				{'bonus':bonus,
				'code':Completion_Code})
		except:
			doRender(self, 'logout.htm',
				{'bonus':bonus,
				'code': Completion_Code})


###############################################################################
############################### MturkIDHandler ################################
###############################################################################

class MturkIDHandler(webapp.RequestHandler):
	def get(self):
		doRender(self, 'mturkid.htm',
			{'error':0})

	def post(self):
		self.session = get_current_session()
		usernum = create_or_increment_NumOfUsers()

		browser = self.request.get('browser')
		ID = self.request.get('ID')
		account = ID
		logging.info('BROWSER: '+browser)


		# make sure they qualify

		form_fields = {
			"ID": ID,
			"ClassOfStudies": 'Cory Dissertation',
			"StudyNumber": 2
			}

		form_data = urllib.urlencode(form_fields)
		url="http://www.mturk-qualify.appspot.com"
		result = urlfetch.fetch(url=url,
								payload=form_data,
								method=urlfetch.POST,
								headers={'Content-Type': 'application/x-www-form-urlencoded'})

		if result.content=="0":
			#self.response.out.write("ID is in global database.")
			doRender(self, 'do_not_qualify.htm')

		elif result.content=="1":
			# Check if the user already exists
			que = db.Query(User).filter('account =',ID)
			results = que.fetch(limit=1)

			if (len(results) > 0) & (ID!='ben') & (ID!= 'ben1'):
				doRender(self, 'do_not_qualify.htm')

			# If user is qualified (http://www.mturk-qualify.appspot.com returns 1)
			else:

				# # order of test questions
				# testOrder = random.choice([1,2,3,4,5,6]) # all possible orders, not breaking down by memory vs causal
				testOrder = random.choice([4,6]) 
					# Because the causal task is another trial, it should go last! 
					# Any order effects in the testing questions should affect all groups equally.


				self.session['usernum'] = usernum
				logging.info('USERNUM: '+str(self.session['usernum']))
				# disease names
				self.session['diseaseNames'] = ['Duastea', 'Stectosis']
				random.shuffle(self.session['diseaseNames'])
				# drugColors = ['blue', 'green', 'orange', 'purple']

				self.session['drugColors'] = ['lightblue', 'darkblue', 'orange', 'purple']
				random.shuffle(self.session['drugColors'])
					# names and colors are the randomized visuals for var1 (position1, now randomized in this handler (below), no need to randomized further)

				# position2 (valence)
				self.session['position2'] = random.choice([0,1])
				# self.session['position2'] = 1 # testing
					# if 0, left value of var2 is BAD, right is GOOD
					# if 1, left is GOOD, right is BAD
					# this is position2 (valence)
					# position2 (visual): just randomize the presentation of the stimuli in Python, than read them into JS in the order that they're randomized in.
						# for the story condition this will have to be read in consistently both times.

				# in E2, storyCondition is gain vs loss
					# gain framing: start with $0; each pos outcome adds $0.06
					# loss framing: start with $6; each neg outcome subtracts $0.06
						# Would starting with $5.76 make participants suspicious about the bonus amount?

				if self.session['usernum'] % 2 == 0:
					self.session['condition'] = 'gain'
					self.session['runningBonuses'] = 0
				else:
					self.session['condition'] = 'loss'
					self.session['runningBonuses'] = 576

				self.session['storyCondition'] = 'combined' # constant for E2

				# position1 and position2 (visual)
				if self.session['storyCondition'] == 'monetary':
					a = ['RED', 'BLUE', 'PURPLE', 'GREEN']

					if random.choice([0,1]) == 1:
						colorNames = [a[2], a[3], a[0], a[1]]
					else:
						colorNames = a

					if random.choice([0,1]) == 1:
						temp0 = colorNames[0]
						temp1 = colorNames[1]
						colorNames[0] = temp1
						colorNames[1] = temp0
					if random.choice([0,1]) == 1:
						temp2 = colorNames[2]
						temp3 = colorNames[3]
						colorNames[2] = temp3
						colorNames[3] = temp2

					self.session['var1_Names'] = colorNames
						# this changes it to colors. If I did this right it will always be red vs blue and green vs purple

					# shapes
					shapeNames = ['SQUARE', 'CIRCLE', 'STAR', 'TRIANGLE', 'OVAL', 'DIAMOND', 'RECTANGLE', 'PENTAGON']
					
					random.shuffle(shapeNames) # which shapes they see when. This takes care of position1 and position2 (visual) (commented out for testing)
					self.session['var2_Names'] = shapeNames[0:4] # worked in python 3...we'll see
						# the first two are the var1 shape names for the first scenario, in order (this is position1, no need to randomize further)
					self.session['diseaseNames'] = ['','']
					self.session['drugColors'] = ['','','','']
				else:

					# drug names
					self.session['var1_Names'] = ['XF7', 'BT3', 'GS5', 'PR2']
					random.shuffle(self.session['var1_Names'])
						# names and colors are the randomized visuals for var1 (position1, now randomized in python, no need to randomized further)



					# valence and visual are the same for position2 in this storyCondition
					if self.session['position2'] == 0:
						self.session['var2_Names'] = ['BAD', 'GOOD', 'BAD', 'GOOD']
					else:
						self.session['var2_Names'] = ['GOOD', 'BAD', 'GOOD', 'BAD']

				self.session['frequency1'] = random.choice([0,1])
				self.session['frequency2'] = [0,1] # is the left outcome common (0) or rare (1)

				# in the story storyCondition, if the bad outcome is on the left (position2 == 0) and the left outcome is common (frequency2 == 0), rare_positive valence.

				random.shuffle(self.session['frequency2'])

				#Make the data that this subject will see.
				#It is made once and stored both in self.session and in database

				# dataset 1
				# new data method for E1
				# Data1_var1 is the drug or shape1 in the first scenario: 0 is common, 1 is rare
				if self.session['frequency1'] == 0:
					a = [[0]*36, [1]*12] # 0 is common; 0 is the drug/shape on the left
				else:
					a = [[1]*36, [0]*12] # 1 is common

				a = [item for sublist in a for item in sublist] # flatten the list

				# Data1_var2 is the outcome/face or shape2:
				# frequency2 is whether the *left/right* value is common or rare
				# position2 is whether the *left/right* value is GOOD or BAD
				# to create v2 we need both
				# 0 is ***always bad*** in our datasets
				if self.session['position2'] == 0: # left is bad, right is good
					if self.session['frequency2'][0] == 0: # left is common; if left is bad, more zeroes
						b = [[0]*24, [1]*12, [0]*8, [1]*4] # 0 is common
					else: # left is rare, bad is rare, more 1s
						b = [[1]*24, [0]*12, [1]*8, [0]*4] # 1 is common
				else: # left is good, right is bad
					if self.session['frequency2'][0] == 0: # left is common; if left is good, more ones
						b = [[1]*24, [0]*12, [1]*8, [0]*4] # 1 is common
					else: # left is rare, left is good, more zeroes
						b = [[0]*24, [1]*12, [0]*8, [1]*4] # 0 is common

				b = [item for sublist in b for item in sublist] # flatten the list

				# random data order
				order = list(range(48))
				random.shuffle(order)

				Data1_var1 = []
				Data1_var2 = []

				for i in order:
					Data1_var1.append(a[i])
					Data1_var2.append(b[i])

				# dataset 2 (second scenario)
				# Data1_var1 is the drug or shape1 in the first scenario: 0 is common, 1 is rare
				if self.session['frequency1'] == 0:
					a = [[0]*36, [1]*12] # 0 is common
				else:
					a = [[1]*36, [0]*12] # 1 is common

				a = [item for sublist in a for item in sublist] # unlist

				# Data1_var2 is the outcome/face or shape2
				# frequency2 is whether the *left/right* value is common or rare
				# position2 is whether the *left/right* value is GOOD or BAD
				# to create v2 we need both
				# 0 is ***always bad*** in our datasets
				if self.session['position2'] == 0: # left is bad, right is good
					if self.session['frequency2'][1] == 0: # left is common; if left is bad, more zeroes
						b = [[0]*24, [1]*12, [0]*8, [1]*4] # 0 is common
					else: # left is rare, bad is rare, more 1s
						b = [[1]*24, [0]*12, [1]*8, [0]*4] # 1 is common
				else: # left is good, right is bad
					if self.session['frequency2'][1] == 0: # left is common; if left is good, more ones
						b = [[1]*24, [0]*12, [1]*8, [0]*4] # 1 is common
					else: # left is rare, left is good, more zeroes
						b = [[0]*24, [1]*12, [0]*8, [1]*4] # 0 is common

				b = [item for sublist in b for item in sublist] # flatten the list


				random.shuffle(order)
				Data2_var1 = []
				Data2_var2 = []

				for i in order:
					Data2_var1.append(a[i])
					Data2_var2.append(b[i])

				self.session['v1_Data'] = [Data1_var1, Data2_var1]
				self.session['v2_Data'] = [Data1_var2, Data2_var2]


				# order of test questions
				# self.session['testOrder'] = random.choice([1,2,3,4,5,6]) # all possible orders, not breaking down by memory vs causal
				# because of the way we changed the causal judgment task, we should put that task at the end
				# random 4 or 6 then (makes this easily changeable if we decide that this isn't important for future expts)
				self.session['testOrder'] = random.choice([4,6])


				# running tally of bonuses
				# self.session['runningBonuses'] = 30

				self.session['scenario'] = 0
				

				trialGuesses = [0]*LengthOfData

				# running tally of bonuses
				runningBonuses = 0

				a = self.session['v1_Data']
				a = [item for sublist in a for item in sublist]

				b = self.session['v2_Data']
				b = [item for sublist in b for item in sublist]

				newuser = User(
					usernum=usernum,
					account=account,
					browser=browser,
					sex=0,
					ethnicity=0,
					race=0,
					age=0,
					Bonuses = self.session['runningBonuses'],
					testOrder = testOrder,
					reloads = 0,
					totalTrials = 0, # if they go back through the data again, their total trials will be greater than 96
					v1_Data = a,
					v2_Data = b,
					testAttempts = [0,0],
					frequency1 = self.session['frequency1'],
					frequency2 = self.session['frequency2'],
					position2 = self.session['position2'],
					var1_Names = self.session['var1_Names'],
					var2_Names = self.session['var2_Names'],
					condition = self.session['condition'],
					drugColors = self.session['drugColors'],
					diseaseNames = self.session['diseaseNames'],
					progress = 0);

				# dataframe modeling, but I'm not sure what exactly
				userkey = newuser.put()

				# this stores the new user in the datastore
				newuser.put()

				# store these variables in the session
				self.session=get_current_session() #initialize sessions

				self.session['account']				= account
				
				self.session['scenario']			= 0
				# order of test questions
				self.session['trialGuesses']		= trialGuesses
				self.session['userkey']				= userkey
				self.session['usernum']				= usernum
				self.session['trialNumber']			= 0
				self.session['reloads']				= 0
				


				doRender(self, 'qualify.htm',{
					'storyCondition':self.session['storyCondition']
				})



		# If got no response back from http://www.mturk-qualify.appspot.com
		else:
		  error="The server is going slowly. Please reload and try again."
		  self.response.out.write(result.content)


###############################################################################
############################### MainAppLoop ###################################
###############################################################################

application = webapp.WSGIApplication([
	('/ajax', AjaxHandler),
	# ('/AjaxOutcomeMemoryTest', AjaxOutcomeMemoryHandler),
	('/AjaxMemoryTest', AjaxMemoryHandler),
	('/AjaxCausalTest', AjaxCausalHandler),
	('/preScenario', preScenarioHandler),
	('/instructions', InstructionsHandler),
	('/data', DataHandler),
	('/do_not_qualify', DNQHandler),
	('/scenario', ScenarioHandler),
	('/finalJudgment', FinalJudgmentHandler),
	('/qualify', QualifyHandler),
	('/progressCheck', ProgressCheckHandler),
	('/demographics', DemographicsHandler),
	('/mturkid', MturkIDHandler),
	('/.*',      MturkIDHandler)],  #default page
	# ('/.*',      TestHandler)],  # testing
	debug=True)



def main():
		run_wsgi_app(application)

if __name__ == '__main__':
	main()
