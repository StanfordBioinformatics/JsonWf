#!/srv/gs1/software/python/python-2.7/bin/python

import sys
import os
import json
import sjm_writer
from argparse import ArgumentParser
import jsonschema
import subprocess
import re
import copy


###varReg finds variables of the type $var and ${var} and ${var%%.txt}, ... variables can be mixed in with some string, such as a file path.
varReg = re.compile(r'(\${(?P<brace>[\d\w]+))|(\$(?P<dollar>[\d\w]+))')
numReg = re.compile(r'\d$')


def checkCircDeps(allDependencies):
	for analysis in allDependencies:
		deps = allDependencies[analysis]
		for d in deps:
			try:
				depDeps = allDependencies[d]
			except KeyError:
				depDeps = []
			if analysis in depDeps:
				raise Exception("Error: Circular dependencies found between analyses {analysis1} and {analysis2}".format(analysis1=analysis,analysis2=d))

def getDependencies(analysis):
	try:
		deps = analysis['dependencies']
	except KeyError:
		return []
	enabledDeps = []
	for i in deps:
		if not enabled(i):
			continue
		else:
			enabledDeps.append(i)
	return enabledDeps

def rmDependency(dependency,allDependencies):
	"""
	Function : Given a dict with analysis names that have dependencies as keys, and values as lists of dependency names, removes
             the passed in dependency named from each value.
	"""
	for analysis in allDependencies:
		try:
			index = allDependencies[analysis].index(dependency)
		except ValueError:
			index = -1
		if index >=0:
			allDependencies[analysis].pop(index)

def getDescription(analysis):
	"""
	Function : Retrieves the 'description' of an analysis, if this keyword is present. This is a keyword defined in the JSON Schema draft 4.
	Args     : analysis - str. The name of an analysis.
	"""
	try:
		desc = analysisDict[analysis]['description']
	except KeyError:
		return None
	return desc

def getTitle(analysis):
	"""
	Function : Retrieves the 'title' of an analysis, if this keyword is present. This is a keyword defined in the JSON Schema draft 4.
	Args     : analysis - str. The name of analysis.
	"""
	try:
		title = analysisDict[analysis]['title']
	except KeyError:
		return None
	return title

def getDescriptionOrTitle(analysis):
	"""
	Function : Given an analysis name, tries to return it's description if the 'description' keyword is present.
						 If not, then tries to return it's title if the 'title' keyword is present. If neither is present,
						 returns the None object.
	"""
	desc = getDescription(analysis)	
	if desc:
		return desc
	title = getTitle(analysis)
	return title

def getAllAnalyses():
	"""
	Function : Returns a dict of all analyses present in the JSON conf file as keys and as values as a string being the description
						 if the 'description' keyword is present, else the title if the 'title' keyword is present, else the None object.
	"""
	dico = {}
	for analysis in analysisDict:
		val = getDescriptionOrTitle(analysis)
		dico[analysis] = val
	return dico

def getDisabledAnalyses():
	"""
	Function : Returns a dict of all disabled analyses present in the JSON conf file as keys and as values as a string being the description
						 if the 'description' keyword is present, else the title if the 'title' keyword is present, else the None object.
	"""
	dico = {}
	for analysis in analysisDict:
		if not enabled(analysis):
			val = getDescriptionOrTitle(analysis)
			dico[analysis] = val
	return dico

def getEnabledAnalyses():
	"""
	Function : Returns a dict of all enabled analyses present in the JSON conf file as keys and as values as a string being the description
						 if the 'description' keyword is present, else the title if the 'title' keyword is present, else the None object.
	"""
	dico = {}
	for analysis in analysisDict: 
		if enabled(analysis):
			val = getDescriptionOrTitle(analysis)
			dico[analysis] = val
	return dico

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
			raise Exception("Found duplicate key {key} in your resources".format(key=key))
	
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
			raise Exception("Found duplicate key {key} in your resources".format(key=key))

def enabled(analysis):
	"""
	Function : Checks whether an analysis is enabled or not.
	Args     : analysis - str. An analysis name.
	"""
	return analysisDict[analysis]['enable']

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
					print ("Resolved {origPart} to {part}".fommat(origPart=origPart,part=part))
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
	#build executable code string that consists of a series of dictionary indexing parts, to ultimately index jconf:
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
			raise ValueError("Error: In configuration file, varible {varName} is not a resource.".format(varName=varName))

		##Hold off on update below, let all updates happen simultaneously though shell expansion with the call the subprocess below
		#txt = re.sub(r'\${{{varName}}}'.format(varName=varName),replace,txt) 
		print("Updating {varName} to {replace}".format(varName=varName,replace=replace))
	txt = subprocess.Popen('echo -n "{txt}"'.format(txt=txt),shell=True,stdout=subprocess.PIPE).communicate()[0]
	return txt
        

def makeCmd(analysis,prog):	
	"""
	Function : String together a command and it's arguments from the input dictionary. The analysis objects for java programs should have the properties 'jar' and 'javavm' set. All others should use the 'program' property.
             If both 'jar' and 'program' are set, then 'program' will be ignored.
	Args     : analysis - str. Name of the program (i.e. the executable)
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
	jobname = analysis
	job = sjm_writer.Job(jobname)
	job.setSjmFile(sjmfile)
	job.setCmd(cmd)

	directory = outdir #working directory (dir in which to execute the command)
	try:
		directory = qsub['directory']
		if not os.path.exists(directory):
			raise OSError("Directory {directory} does not exist! Check 'directory' property in the qsub object of analysis {analysis}.".format(directory=directory,analysis=analysis))
	except KeyError:
		pass

	job.setWd(directory)
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

def processAnalysis(analysisConf):
	#check if output direcories are defined, and deal with these first, because it's allowed for
	# the JSON resource dict called 'outfiles' to reference variables in the 'outdirs' JSON resource dict.
	# As a result, any keys in the outdirs object will be added to the environment. Note that the keys in the outfiles
	# object will also be added to the environment.  These two objects are the only cases where  global resources can be defined outside of the "resources" object.
	# This is also the only time in the code that I allow a JSON resource to be able to reference other JSON resources.
	# 
	outdirs = {}
	try:
		outdirs = analysisConf['outdirs'] #outdirs, if defined, is an array of objects
	except KeyError:
		pass
	if outdirs:
		for i in outdirs:
			expandVars(i)
			for key in i:
				path = i[key]
				if not os.path.exists(path):
					os.mkdir(path)
			addToEnvironment(dico=i)
		analysisConf.pop('outdirs')

	outfiles = {}
	try:
		outfiles = analysisConf['outfiles']
	except KeyError:
		pass
	if outfiles:
		for i in outfiles:
			expandVars(i)
			addToEnvironment(dico=i)
		analysisConf.pop('outfiles')

	qsubDico = {}
	try:
		qsubDico = analysisConf['qsub']	
	except KeyError:
		pass
	for i in globalQsub:
		if i not in qsubDico: #don't overwite!
			qsubDico[i] = globalQsub[i]
	expandVars(analysisConf) #replace resource variables with their resource values
	makeCmd(analysis,analysisConf)




coreQsubArgs = ["time","mem","slots","pe","host","queue", "project","outdir","-e","-o","directory","name"]

description = "Given a JSON configuration file that abides by the packaged schema.json file, this program will validate the conf file, then build an SJM file. Variable substitution is also supported, whereby any value in the conf file that begins with a '$' may be replaced by a global resource that is specified either on the command-line (CL) as an argument, or in the conf file itself. In the conf file, resources include the global resource and qsub objects.  CL set resources override conf file resources. For help with validating your JSON conf file, copy and past it into the online JSON Schema Validator at http://jsonformatter.curiousconcept.com/.  By default, each analysis in the conf file is executed in the working directory specified by --outdir. This can be overwritten in a given analysis using the 'directory' property of the 'qsub' object.  For each job submitted run on the cluster, its stdout and stderr files will be written a directory called JobStatus, which is a subdirectory of --outdir; this cannot be changed."

parser = ArgumentParser(description=description)
parser.add_argument('--schema',default="/srv/gs1/software/gbsc/kwality/1.0/schema.json", help="The JSON schema that will be used to validate the JSON configuration file. Default is %(default)s.")
parser.add_argument('--outdir',help="(Required when none of --analyses, --enabled, and --disabled are specified) The directory to output all result files. Can be a relative or absolute directory path. Will be created if it does't exist already. Will be added as a global resource. Serves as the default working directory when jobs are submitted to the cluster, for each analysis that doesn't set the working directory.")
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('resources',nargs="*",help="One or more space-delimited key=value resources that can override or append to the keys of the resoruce object in the JSON conf file. The value of the --outdir option will automatically be added here with the variable name 'outdir'.")
parser.add_argument('-s','--sjmfile',help="(Required when none of --analyses, --enabled, and --disabled are specified) Output SJM file name (w/o directory path). The sjm file will be created in the directory passed to --outdir. If the file already exists, it will be appended to.")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")
parser.add_argument('--run',action="store_true",help="Don't just generate the sjm file, run it too. By default, the program does not wait for the sjm job to complete; see --wait.")
parser.add_argument('--wait',action="store_true",help="When --run is specified, indicates that the script should wait for the sjm job to complete before exiting.")
parser.add_argument('--analyses',action="store_true",help="Display a list of availble analyses present in --conf-file.")
parser.add_argument('--enabled',action="store_true",help="Display a list of enabled analyses present in --conf-file.")
parser.add_argument('--disabled',action="store_true",help="Display a list of disabled analyses present in --conf-file.")

def outputAnalyses(analysisDict):
	"""
	Function : Prints to stdout all analyses in the passed in dict, one per line.
	"""
	print("{name:<35}{desc}".format(name="Name:",desc="Description:"))
	for i in sorted(analysisDict):
		print("{analysis:<35}{desc}".format(analysis=i,desc=analysisDict[i]))

args = parser.parse_args()
if args.wait and not args.run:
	parser.error("Argument --wait cannot be specified w/o --run")

if not args.analyses and not args.enabled and not args.disabled:
	if not args.outdir:
		parser.error("You must supply the --outdir argument!")
	if not args.sjmfile:
		parser.error("You must supply the --sjmfile argument!")

cfh = open(args.conf_file,'r')
jconf = json.load(cfh)
rmComments(jconf)
schema = args.schema
sfh = open(schema,'r')
jschema = json.load(sfh)
jsonschema.validate(jconf,jschema)

ald = jconf['analyses'] # analysis list dicts - a list of analyses (dicts)
analysisNames = [x['analysis'] for x in ald]
analysisDict = {}
count = -1
for name in analysisNames:
	count += 1
	if name in analysisDict:
		raise ValueError("Duplicate analysis name {}".format(name))
	analysisDict[name] = ald[count]

allAnalyses = getAllAnalyses()
numAllAnalyses = len(allAnalyses)
if args.analyses:
	print("All Analyses ({}):".format(numAllAnalyses))
	outputAnalyses(allAnalyses)
	parser.exit()
elif args.enabled:
	ea = getEnabledAnalyses()
	print("Enabled Analyses ({0}/{1}):".format(len(ea),numAllAnalyses))
	outputAnalyses(ea)
	parser.exit()
elif args.disabled:
	da = getDisabledAnalyses()
	print("Diabled Analyses ({0}/{1}):".format(len(da),numAllAnalyses))
	outputAnalyses(da)
	parser.exit()


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
sjmfile = os.path.basename(args.sjmfile)
sjmfile = os.path.join(outdir,sjmfile)
if os.path.exists(sjmfile):
	os.remove(sjmfile)

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
##I add outdir to globalQsub last to make sure that if the user had specified a variabled by the same name in jsonResources, it won't shodow the command-line arg outdir.
globalQsub['outdir'] = outdir

#create a dict with each analysis name in it as the key, and value i a list.
# even analyses with not dependencies will appear in the dict, and have the empty list.
analyses = getEnabledAnalyses() #only retrieves enabled analyses
allDependencies = {}
for analysis in analyses:
	#getDependencies() only retrieves enabled dependencies
	dependencies = getDependencies(analysisDict[analysis]) 
	allDependencies[analysis] = []
	if dependencies:
		for d in dependencies:
			allDependencies[analysis].append(d)

#create a copy of the allDepencencies dict so that I can use it to write out all
# dependencies in the sjm file. The original dict will be deleted (key-popped) bit by bit
# as I process the analyses.
allDependencies_orig = copy.deepcopy(allDependencies)
checkCircDeps(allDependencies)


analysisNameDico = {}
for i in analyses:
	analysisNameDico[i] = 1
while analysisNameDico:
	for analysis in analysisNameDico.keys():
		if allDependencies[analysis]:
			continue
		print("\n")
		print("Processing Analysis {analysis}".format(analysis=analysis))
		processAnalysis(analysisDict[analysis])
		analysisNameDico.pop(analysis)
		rmDependency(analysis,allDependencies)
	
sjm_writer.writeDependencies(allDependencies_orig,sjmfile)

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
