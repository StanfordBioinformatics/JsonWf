#!/srv/gs1/software/python/python-2.7/bin/python

import sys
import os
import json
import sjm_writer
from argparse import ArgumentParser
import jsonschema
import subprocess
import re


###varReg finds variables of the type $var and ${var} and ${var%%.txt}, ... variables can be mixed in with some string, such as a file path.
varReg = re.compile(r'(\${(?P<brace>[\d\w]+))|(\$(?P<dollar>[\d\w]+))')
numReg = re.compile(r'\d$')

def addToEnvironment(key=False,value=False,dico={}):
	"""
   Function : Adds environment variables that are passed in as a dict or key and value, or both.
	 Args     : key,value - str.
							dico - dict of variables to add to the environment, where each key and value are strings.
	 Returns  : 
	"""
	#os.environ internally calls os.putenv, which will also set the environment variables at the outter shell level.
	if key and not value:
		raise ValueError("kwality.addToEnvironment() must have argument 'value' set when argument 'key' is set.")
	elif value and not key:
		raise ValueError("kwality.addToEnvironment() must have argument 'key' set when argument 'value' is set.")	

	if key:
		key = str(key)
		value = str(value)
		if key not in resdico:
			resdico[key] = value
			os.environ[key] = value
		else:
			raise Exception("Found duplicate key {key} in your resources")
	
	for key in dico:
		value = dico[key]
		if type(value) is dict:
			addToEnvironment(dico=value)
		key = str(key)
		value = str(dico[key])
		if key not in resdico:
			resdico[key] = value
			os.environ[key] = value
		else:
			raise Exception("Found duplicate key {key} in your resources")

def enabled(dependency):
	"""
	Function : Checks whether an analysis is enabled or not.
	Args     : dependency - str. An analysis name.
	"""
	return jconf['analyses'][dependency]['enable']

def rmComments(dico):
	"""
	Function : Given a dict, removes keys that start with a "#", which are taken to be a comment.
	Args     : dico - dict
	"""
	for i in dico.keys():
		val = dico[i]
		if i.startswith("#"):
			print("REMOVING {0}".format(i))
			dico.pop(i)	

		elif type(val) == dict:
			rmComments(val)

def expandVars(prog):
	"""
	Function : Given the dict 'prog' (a dictionary with program information), look at all setting values and find any variables (words beginning with '$') 
             and check if a parameter with the same name (omitting the '$') exists in the global resdico dict.
             Works recursivly for a dict within a dict.

	Args     : prog - dict structured as an 'analyses' object in the json schema
	"""
	for key in prog:
		val = prog[key]
		valType = type(val)
		if valType == str or valType == unicode:
			if val.startswith("#"):
				origVal = val
				val = resolveJsonPointer(val)
				print ("Resolved {origVal} to {val}".format(origVal=origVal,val=val))
			resourceValue = checkResource(val)
			prog[key] = resourceValue
   
		elif valType == list or valType == tuple:
			count = -1
			for part in val:
				count += 1
				if part.startswith("#/"):
					origPart = part
					part = resolveJsonPointer(part)
					print ("Resolved {origPart} to {part}".format(origPart=origPart,part=part))
				resourceValue= checkResource(part)
				prog[key][count] = resourceValue
					
		elif valType == dict:
			expandVars(val)		

def resolveJsonPointer(txt):
	"""
	Function :
	Args     :
	Returns  :
	"""
	origTxt = txt
	txt = txt.lstrip("#/")
	num = None
	if numReg.search(txt):
		num = int(txt[-1])
		txt = txt[:-2] #2, b/c 1 for number and 1 for /
	txt = txt.split("/")
	exCode = "jconf"
	for key in txt:
		exCode += "['{0}']".format(key)
	if num:
		exCode += "[{0}]".format(num)
	print ("evalCode is {0}".format(exCode))
	try:
		dereferenced =  eval(exCode)
	except KeyError:
		raise KeyError("Failed to dereference JSON pointer {p} in conf file'{c}'. Verify that the path exists in the conf file.".format(p=origTxt,c=args.conf_file))
	
	return dereferenced

def checkResource(txt):
	"""
	Function : Given a string, looks for variables with the syntax ${var}, where var is the variable name.
						 Finds each such variable in the string and checks to see if the variable name exists in the global
						 resource dict called resdico. If it doesn't, a ValueError is raised. If all found variables exist 
						 in resdico, the a variable expansion is performed through the shell on the input string. This relies 
						 on all resources in resdico having been added to the environment (and shell environment) with a call 
						 to os.environ, for example.  
	Args     : txt - str.
	Returns  : str. txt that has undergone variable expansion via the shell.
	"""
	txt = str(txt)
	groupiter = varReg.finditer(txt)	
	for i in groupiter:
		dico = i.groupdict()
		varName = dico['brace']
		if not varName:
			varName = dico['dollar']
		try: 
			replace = resdico[varName]
		except KeyError:
			raise ValueError("Error: In configuration file, varible {varName} is not resource.".format(varName=varName))

		##Hold off on update below, let all updates happen simultaneously though shell expansion with the call the subprocess below
		#txt = re.sub(r'\${{{varName}}}'.format(varName=varName),replace,txt) 
		print("Updating {varName} to {replace}".format(varName=varName,replace=replace))
	txt = subprocess.Popen('echo -n "{txt}"'.format(txt=txt),shell=True,stdout=subprocess.PIPE).communicate()[0]
	return txt
        

def makeCmd(programName,prog):	
	"""
	Function : String together a command and it's arguments from the input dictionary.
	Args     : programName - str. Name of the program (i.e. the executable)
						 prog - dict structured as an 'analyses' object in the json schema.
	"""
	cmd = ""

	jar = False
	try:
		jar = prog['jar']
	except KeyError:
		pass

	javavm = "-Xmx2G"
	try:
		javavm = prog['javavm']
	except KeyError:
		pass

	if jar:
		cmd += "java " + javavm + " " + "-jar " + jar + " "
	else:
		cmd += prog['program'] + " "

	progOptions = False
	try:
		progOptions = prog['params']
	except KeyError:
		pass
		#property not required
	if progOptions:
		for arg in progOptions:
			val = progOptions[arg] #val can be empty string if boolean option
			val = str(val)
			if val:
				if arg.endswith("="):
					cmd += arg + val + " "
				else:
					cmd += arg + " " + val + " "
			else:
				cmd += arg + " "

	progArgs = False
	try:
		progArgs =  prog['args'] 
	except KeyError:
		pass
	if progArgs:
		for arg in progArgs:
			cmd += " " + arg + " "



	qsub = prog['qsub']
	jobname = programName
	job = sjm_writer.Job(jobname)
	job.setSjmFile(sjmfile)

	dependencies = []
	try:
		dependencies = prog['dependencies']
	except KeyError:
		#property not required
		pass

	if dependencies:
		for d in dependencies:
			if enabled(d):
				if jobname not in allDependencies:
					allDependencies[jobname] = []
				allDependencies[jobname].extend(dependencies)

	job.setCmd(cmd)

	job.setCwd(outdir)
	job.setJobLogDir(logdir)

	mem = "mem"
	try:
		job.setResource(mem,qsub[mem])
	except KeyError:
		#property not required
		pass

	slots = "slots"
	try:
		job.setResource(slots,qsub[slots])
	except KeyError:
		#property not required
		pass

	time = "time"
	try:
		job.setResource(time,qsub[time])
	except KeyError:
		#property not required
		pass

	try:
		job.setPe(qsub['pe'])
	except KeyError:
		#property not required
		pass

	try:
		job.setHost(qsub['host'])
	except KeyError:
		#property not required
		pass

	try: 
		queue = qsub['queue']
		job.setQueue(queue)
	except KeyError:
		#property not required
		pass

	try:
		job.setProject(qsub['project'])
	except KeyError:
		#property not required
		pass

	qsub_other = ""
	for arg in qsub:
		if arg not in coreQsubArgs:
			qsub_other += arg + " " + qsub[arg] + "  "

	if qsub_other:
		job.addAdditionalOpts(qsub_other)


	modules = False
	try:
		modules = prog['modules']
		job.setModules(modules)
	except KeyError:
		pass

	job.write() #closes the file too


coreQsubArgs = ["time","mem","slots","pe","host","queue", "project","outdir","-e","-o","cwd","name"]

description = "Given a JSON configuration file that abides by the packaged schema.json file, this program will validate the conf file, then build an SJM file. Variable substitution is also supported, whereby any value in the conf file that begins with a '$' may be replaced by a global resource that is specified either on the command-line (CL) as an argument, or in the conf file itself. In the conf file, resources include the global resource and qsub objects.  CL set resources override conf file resources."

parser = ArgumentParser(description=description)
parser.add_argument('--schema',default="/srv/gs1/software/gbsc/kwality/1.0/schema.json", help="The JSON schema that will be used to validate the JSON configuration file. Default is %(default)s.")
parser.add_argument('--outdir',required=True,help="The directory to output all result files. Can be a relative or absolute directory path. Will be created if it does't exist already. Will be added as a global resource.")
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('resources',nargs="*",help="One or more space-delimited key=value resources that can override or append to the keys of the resoruce object in the JSON conf file. The value of the --outdir option will automatically be added here with the variable name 'outdir'.")
parser.add_argument('-s','--sjmfile',required=True,help="Output SJM file. Appends to it by default.")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")
parser.add_argument('--run',action="store_true",help="Don't just generate the sjm file, run it too. By default, the program does not wait for the sjm job to complete; see --wait.")
parser.add_argument('--wait',action="store_true",help="When --run is specified, indicates that the script should wait for the sjm job to complete before exiting.")

args = parser.parse_args()
if args.wait and not args.run:
	parser.error("Argument --wait cannot be specified w/o --run")

resdico = {} #resource dict

outdir = os.path.abspath(args.outdir)
if not os.path.exists(outdir):
	os.mkdir(outdir)
addToEnvironment(key="outdir",value=outdir)
#outdir will be added to the globalQsub dict below.
logdir = os.path.join(outdir,"JobStatus")
if not os.path.exists(logdir):
	os.mkdir(logdir)


run = args.run
sjmfile = args.sjmfile
if os.path.exists(sjmfile):
	os.remove(sjmfile)

cfh = open(args.conf_file,'r')
jconf = json.load(cfh)

rmComments(jconf)

schema = args.schema
sfh = open(schema,'r')
jschema = json.load(sfh)

jsonschema.validate(jconf,jschema)

resources = args.resources
if resources:
	for i in resources:
		key,val = i.split("=")	
		if os.path.exists(val):
			val = os.path.abspath(val)
		addToEnvironment(key=key,value=val)

jsonResources = {}
try:
	jsonResources = jconf['resources']
except KeyError:
	pass



expandVars(jsonResources)
addToEnvironment(dico=jsonResources)	

globalQsub = {}
try:
	globalQsub = jsonResources['qsub']
except KeyError:
	pass
##I add outdir to globalQsub last to make sure that it's not overwritten by jsonResources
globalQsub['outdir'] = outdir

allDependencies = {}
	
for programName in jconf['analyses']:
#	print (jconf['analyses'][programName])
	pdico = jconf['analyses'][programName]
	enable = pdico['enable']
	if not enable:
		continue

	#check if output direcories are defined, and deal with these first, because it's allowed for
	# the JSON resource dict called 'outfiles' to reference variables in the 'outdirs' JSON resource dict.
	# As a result, any keys in the outdirs objecdt will be added to the environment. Note that the keys in the outfiles
	# object will also be added to the environment.  These two objects are the only cases where  global resources can be defined outside of the "resources" object.
	# This is also the only time in the code that I allow a JSON resource to be able to reference other JSON resources.
	# 
	outdirs = {}
	try:
		outdirs = pdico['outdirs']
	except KeyError:
		pass
	if outdirs:
		expandVars(outdirs)
		for key in outdirs:
			path = outdirs[key]
			if not os.path.exists(path):
				os.mkdir(path)
		addToEnvironment(dico=outdirs)
		pdico.pop('outdirs')

	outfiles = {}
	try:
		outfiles = pdico['outfiles']
	except KeyError:
		pass
	if outfiles:
		expandVars(outfiles)
		addToEnvironment(dico=outfiles)
		pdico.pop('outfiles')

	qsubDico = {}
	try:
		qsubDico = pdico['qsub']	
	except KeyError:
		pass
	for i in globalQsub:
		if i not in qsubDico: #don't overwite!
			qsubDico[i] = globalQsub[i]
	expandVars(pdico) #replace resoruce variables with their resource values
	makeCmd(programName,pdico)
	
sjm_writer.writeDependencies(allDependencies,sjmfile)

if run:
	if args. wait:
		subprocess.call("sjm {sjmfile}".format(sjmfile=sjmfile),shell=True)
	else:
		subprocess.Popen("sjm {sjmfile}".format(sjmfile=sjmfile),shell=True)


#from jsonschema import validate
#import json
#cfh = open("Conf/gatk.json",'r')
#conf = json.load(cfh)
#sfh = open("test_schema.json",'r')
#schema = json.load(sfh)

#python clinicalQc.py -s schema.json -c Conf/gatk.json -o TEST/sjm.txt  2>stderr.txt 
