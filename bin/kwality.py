#!/srv/gs1/software/python/python-2.7/bin/python

import sys
import os
import json
import sjm_writer
from argparse import ArgumentParser
import jsonschema
import subprocess
import re


reg = re.compile(r'\${(?P<var>[\d\w]+)}')

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
			resourceValue = checkResource(val)
			if resourceValue:
				prog[key] = resourceValue
				print("Updating {val} to {resourceValue}".format(val=val,resourceValue=resourceValue))
   
		elif valType == list or valType == tuple:
			count = -1
			for part in val:
				count += 1
				resourceValue= checkResource(part)
				if resourceValue:
					prog[key][count] = resourceValue
					print("Updating {val} to {resourceValue}".format(val=prog[key][count],resourceValue=resourceValue))
					
		elif valType == dict:
			expandVars(val)		


def checkResource(txt):
	groupiter = reg.finditer(txt)	
	for i in groupiter:
		varName = i.groupdict()['var']	
		try: 
			replace = resdico[varName]
		except KeyError:
			raise ValueError("In configuration file, varible {varName} does not contain a resource.".format(varName=varName)

		txt = re.sub(r'\${{{varName}}}'.format(varName=varName),replace,txt)
	return txt
        




def makeCmd(progName,prog):	
	"""
	Function : String together a command and it's arguments from the input dictionary.
	Args     : progName - str. Name of the program (i.e. the executable)
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
		cmd += progName + " "

	progOptions = prog['params']
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

	jobname = qsub['name']

	job = sjm_writer.Job(jobname)
	job.setSjmFile(sjmfile)
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


	qsub_other = "-o {logdir} -e {logdir}".format(logdir=logdir) + " "
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
parser.add_argument('--outdir',required=True,help="The directory to output all result files. Can be a relative or absoulte direcotry path. Will be created if it does't exist already.")
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('resources',nargs="*",help="One or more space-delimited key=value resources that can override or append to the keys of the resoruce object in the JSON conf file.")
parser.add_argument('-s','--sjmfile',required=True,help="Output SJM file. Appends to it by default.")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")
parser.add_argument('--run',action="store_true",help="Don't just generate the sjm file, run it too.")

args = parser.parse_args()
outdir = os.path.abspath(args.outdir)
if not os.path.exists(outdir):
	os.mkdir(outdir)
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
resdico = {}
if resources:
	for i in resources:
		key,val = i.split("=")	
		resdico[key] = val

jsonResources = {}
try:
	jsonResources = jconf['resources']
except KeyError:
	pass

#if jsonResources exists, then add it's keys and values to resources dict, but
# only if the key doens't exist already.
for i  in jsonResources:
	if i not in resdico:
		resdico[i] = jsonResources[str(i)]
	

globalQsub = False
try:
	globalQsub = jconf['qsub']
except KeyError:
	pass

globalQsub['outdir'] = outdir
globalQsub_intersect = set(resdico).intersection(globalQsub)	
if globalQsub_intersect:
	for res in globalQsub_intersect:
		sys.stderr.write("Qsub resource {res} in conf file {conf} clashes with a resource by the same name in the conf file's 'resource' object.\n".format(res=res,conf=args.conf_file))		
	raise Exception("Exiting due to resource key clashes.")
else:
	resdico.update(globalQsub)

for programName in jconf['analyses']:
#	print (jconf['analyses'][programName])
	pdico = jconf['analyses'][programName]
	enable = pdico['enable']
	if not enable:
		continue
	if globalQsub: #then add global qsub options to all analyses
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
	

if run:
	subprocess.call("sjm {sjmfile}".format(sjmfile=sjmfile),shell=True)


#from jsonschema import validate
#import json
#cfh = open("Conf/gatk.json",'r')
#conf = json.load(cfh)
#sfh = open("test_schema.json",'r')
#schema = json.load(sfh)

#python clinicalQc.py -s schema.json -c Conf/gatk.json -o TEST/sjm.txt  2>stderr.txt 
