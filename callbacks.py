'''
Use callbacks to trigger custom action like notifying Slack, Discord, Telegram, ...

THIS IS THE DEFAULTS FILE!

Please copy the needed callbacks to a new file called
user_callbacks.py
This makes upgrading to newer versions easy by simply calling git pull.
'''

def credit_too_low(uid, name, **kwargs):
	''' Called on scanning tag with too low credit to start a session '''
	pass

def credit_low_warning(uid, name, **kwargs):
	''' Called when logged in and remaining time is <= LOW_CREDIT_MINUTES '''
	pass

def credit_runout(uid, name, **kwargs):
	''' Called when user gets logged out due to insufficient credit '''
	pass

def credit_runout_interrupt(uid, name, job_time, **kwargs):
	''' Called when user gets logged out due to insufficient credit and a job was running '''
	pass

def machine_turn_on(**kwargs):
	''' Called on turning the machines power on '''
	pass

def machine_turn_off(**kwargs):
	''' Called on turning the machines power off '''
	pass

def card_scan(uid, **kwargs):
	''' Called on scanning a card '''
	pass

def card_unkown(uid, **kwargs):
	''' Called on scanning an (to the database) unkown card '''
	pass

def card_unauthorized(uid, name, **kwargs):
	''' Called on scanning an unauthorized card '''
	pass

def card_authorized(uid, name, **kwargs):
	''' Called on scanning a valid (authorized) card '''
	pass

def user_logout(uid, name, **kwargs):
	''' Called on manual logout '''
	push_rocket('Der Lasercutter ist wieder frei.')
	pass

def user_login(uid, name, **kwargs):
	''' Called on login '''
	pass

def job_start(uid, name, **kwargs):
	''' Called on starting an job '''
	pass

def job_resume(uid, name, **kwargs):
	''' Called on login with currently stopped/interrupted job '''
	pass

def job_end(uid, name, job_time, **kwargs):
	''' Called on ending an job '''
	pass
