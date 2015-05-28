# This application interacts with the user to collect asset info and 
# inputs into the webportal using selenium


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sys import stdin
import time
import datetime
import calendar


##################################################
################ log thread ######################
##################################################

from collections import deque
import threading

active = 1
log = deque([])

def logStackListener():
	while(active):
		if len(log)>0:
			print(log.popleft())

t = threading.Thread(target=logStackListener)
t.start()

##################################################
############## end log thread ####################
##################################################

login = []
email = []

log.append('Please answer the following questions to submit assets')

# browser = webdriver.Firefox()
# browser = webdriver.PhantomJS('C:\phantomjs-2.0.0-windows\\bin\phantomjs.exe')

with open('url','r') as u:
	url = u.read().strip()
	log.append('URL read')

with open('credentials','r') as c:
	login = c.read().strip().split('\n')
	log.append('Credentials read')

def waitForPageById(element, seconds=15):
	try:
		element = WebDriverWait(browser, seconds).until(
			EC.presence_of_element_located((By.ID, element))
		)
		return 1;
	except:
		return 0;

# asset generation data values
assets = []

assetkeys = []
with open('assetkeys','r') as ak:
	for line in ak.readlines():
		assetkeys.append(line.strip())

articles = []
with open('articles','r') as a:
	for line in a.readlines():
		section = line.split(',')
		articles.append(dict([('key',section[0]),('model',section[1]),('manufacturer',section[2]),('type',section[3])]))	

procurements = dict([('leased',1),('purchased',1)])

locations = []
with open('locations','r') as l:
	for line in l.readlines():
		section = line.split(',')
		locations.append(dict([('code',section[0]),('name',section[1])]))

# recursive asset generation
def assetPrompt():
	
	print 'Collecting information on assets:'

	# generate newAsset dictionary to append to assets list
	newAsset = dict.fromkeys(assetkeys)
	print newAsset.keys()

	newAsset['serialnumber'] = raw_input('Serial Number? ').strip('\n')
	
	for idx,item in enumerate(articles):
		print(str(idx) + ': ' + item['model'])
	hwsel = int(raw_input('Select one of the devices by index: ').strip())
	newAsset['article'] = articles[hwsel]['key']
	newAsset['manufacturer'] = articles[hwsel]['manufacturer']
	if(articles[hwsel]['type']=='laptop'):
		newAsset['computername'] = 'L'+newAsset['serialnumber']
	elif(articles[hwsel]['type']=='desktop'):
		newAsset['computername'] = 'W'+newAsset['serialnumber']
	else:
		newAsset['computername'] = raw_input('Device name?').strip()

	hwproc = raw_input('Enter procurement type ("leased" or "purchased"): ').strip().lower()
	newAsset['procurement'] = hwproc

	if not procurements.get(hwproc,0):
		newAsset['procurement'] = ''
	
	for idx,item in enumerate(locations):
		print( str(idx) + ': ' + item['code'] + ' - ' + item['name'])
	locsel = int(raw_input('Select from one of the locations by index: '))
	newAsset['location'] = locations[locsel]['code']

	with open('assetdefaults','r') as ad:
		defaults = ad.readlines()
		newAsset['user'] = defaults[0]
		newAsset['group']= defaults[1]
		newAsset['os'] = defaults[2]


	newAsset['installdate']= datetime.datetime.now().strftime('%m/%d/%Y')
	
	td = newAsset['installdate']
	yearCut = len(td)-2
	firstHalfDate = td[:yearCut]
	secondHalfDate= str(int(td[yearCut:]) + 3)
	td = firstHalfDate + secondHalfDate
	expDoM = calendar.monthrange(int(td[6:]),int(td[:2]))[1]
	newAsset['expiredate'] = td[:3] + str(expDoM) + td[5:]

	if(newAsset['procurement'] == 'leased'):
		newAsset['leaseend'] = td
		newAsset['leasestatus'] = 'OK'

	assets.append(newAsset)
	
	# recursive tail call 
	if(raw_input('\nWould you like to add another asset? Y/N\n').strip().lower() == 'y'):
		assetPrompt()

	return 1;

def loginServiceCenter():

	browser.get(url)	
	if not waitForPageById('j_username'):
		browser.get(url+'/maximo')
	log.append('Browser opened to WGA management portal')

	# locate login and password forms
	loginform = browser.find_element_by_id('j_username')
	passwordform = browser.find_element_by_id('j_password')

	# type in user credentials
	loginform.send_keys(login[0])
	passwordform.send_keys(login[1])

	# log in using given credential
	loginbutton = browser.find_element_by_id('loginbutton')
	loginbutton.click() 

	return 1;

def openAssetManager():
	browser.find_element_by_id('mx106_anchor_1').click()
	return 1;

def addAsset(asset=dict.fromkeys(assetkeys)):
	browser.find_element_by_partial_link_text('New Asse').click()
	
	if not waitForPageById('mx746'):
		return 0; 

	# retrieve initial elements (no lease info yet)
	serialNumberForm = browser.find_element_by_id('mx392')
	deviceNameForm = browser.find_element_by_id('mx414')
	articleForm = browser.find_element_by_id('mx422')
	procurmentForm = browser.find_element_by_id('mx555')
	manufacturerForm = browser.find_element_by_id('mx603')
	locationForm = browser.find_element_by_id('mx477')
	osForm = browser.find_element_by_id('mx738')
	installDateForm = browser.find_element_by_id('mx746')
	expireDateForm = browser.find_element_by_id('mx754')

	time.sleep(1)
	
	# submit form
	browser.find_element_by_id('addGuestAccountSubmit').click()

	# back to guest accounts page
	if not waitForPageById('viewGuestAccountCancel'):
		browser.get(url)
	browser.find_element_by_id('viewGuestAccountCancel').click()

	# end account creation function
	return 1;


def queryAsset(asset, loadErr=0):
	if not waitForPageById('BEDEVICENAME@461488'):
		try:
			browser.get(url)
			browser.find_element_by_id('mx106_anchor_1').click()
		except:
			loadErr+=1 
			if(loadErr > 10):
				return 0;
			return queryAsset(asset,loadErr)
	deviceNameQuery = browser.find_element_by_id('BEDEVICENAME@461488')
	deviceNameQuery.send_keys(asset['computername'])
	deviceNameQuery.send_keys(Keys.RETURN)
	
	time.sleep(1)

	try:
		returnedAsset = browser.find_element_by_partial_link_text(asset['computername'])
		return 1;
	except:
		return 0;



##################################################
############### main functionality ###############
##################################################

# prompt user for asset information
if not assetPrompt():
	active = 0
log.append('Assets successfully stored to memory')

# login to service center
if not loginServiceCenter():
	active = 0
log.append('Main portal logged in')

time.sleep(3)

# create new asset for all entered devices
for asset in assets:

	time.sleep(2)

	if queryAsset(asset):
		continue

	time.sleep(3)

# exit browser
time.sleep(1)
active = 0
browser.quit()
