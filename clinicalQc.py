#!/srv/gs1/software/python/python-2.7/bin/python

import sys
import os
import json
import sjm_writer
from argparse import ArgumentParser
import jsonschema
import subprocess


def rmComments(dico):
	"""
	Function : Given a dict, removes keys that start with a "#", which are taken to be a comment.
	Args     : dico - dict
	"""
	for i in prog.keys():
		val = prog[i]
		if i.startswith("#"):
			print("REMOVING {0}".format(i))
			prog.pop(i)	

		elif type(val) == dict:
			rmComments(val)

def expandVars(prog):
	"""
	Function : Given the dict 'prog' (a dictionary with program information), look at all setting values and find any variables (words beginning with '$') 
		         and check if a parameter with the same name (omitting the '$') exists in the global resources dict or as a command-line option.
						 Together, resources include the global resoruce dict and the command-line (CL) args, where a CL arg overrides all. If such a resource
						 exists, then in 'prog' replace the variable with the resource value.  Works recursivly for a dict within a dict.

	Args     : prog - dict structured as an 'analyses' object in the json schema
	"""
  for i in prog:
    j = prog[i]
    jtype = type(j)
    if jtype == str or jtype == unicode:
      if j.startswith("$"):
        j = j.lstrip("$")
        path = j.split("/",1) #could be an environment variable at the begining of a path 
        if len(path) == 2:
          j = path[0]
          path = path[1]
        else:
          path = False

        cmdArg = False
        try: 
          cmdArg = args.__getattribute__(j)
        except AttributeError,err:
          pass
        if cmdArg:
          val = cmdArg
        elif j in resources:
          val = resources[j]

        else:
          raise ValueError("In configuration file, varible {j} does not contain a resource and doens't match a command-line option.".format(j=j))

        originalVal = val
        if path:
          val = os.path.join(val,path)

        prog[i] = val
        print("Updating {j} to {val}".format(j=j,val=originalVal))
        
    elif jtype == dict:
      expandVars(j)		



def makeCmd(progName,prog):	
	"""
	Function : String together a command and it's arguments from the input dictionary.
	Args     : progName - str. Name of the program (i.e. the executable)
						 prog - dict structured as an 'analyses' object in the json schema.
	"""
	cmd = ""

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

	progArgs = prog['params']
	for arg in progArgs:
		val = progArgs[arg] #val can be empty string if boolean option
		val = str(val)
		if val:
			cmd += arg + " " + val + " "
		else:
			cmd += arg + " "


	qsub = prog['qsub']

	jobname = qsub['name']

	job = sjm_writer.Job(jobname)
	job.setSjmFile(sjmfile)
	job.setCmd(cmd)


	try:
		job.setCwd(qsub['cwd'])
	except KeyError:
		#poperty not required
		pass

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

	try:
		job.setCwd(qsub['cwd'])
	except KeyError:
		#property not required
		pass


	qsub_other = ""
	for arg in qsub:
		if arg not in coreQsubArgs:
			qsub_other += arg + " " + qsub[arg] + "  "

	if qsub_other:
		job.setOtherOpts(qsub_other)


	modules = False
	try:
		modules = prog['modules']
		job.setModules(modules)
	except KeyError:
		pass

	job.write() #closes the file too






coreQsubArgs = ["time","mem","slots","pe","host","queue", "project","cwd","name"]

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-s','--schema',default="/srv/gs1/software/gbsc/clinical_qc/schema.json", help="The JSON schema that will be used to validate the JSON configuration file. Default is %(default)s.")
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('-b','--bam-file',help="Mappings file in BAM format")
parser.add_argument('--vcf',help="Varicant Call File in VCF format")
parser.add_argument('-r','--reference',help="Reference genome in FASTA format")
parser.add_argument('--out-dir',help="Output folder")
parser.add_argument('-o','--outfile',required=True,help="Output SJM file. Appends to it by default.")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")
parser.add_argument('--run',action="store_true",help="Don't just generate the sjm file, run it too.")

args = parser.parse_args()

run = args.run
sjmfile = args.outfile
if os.path.exists(sjmfile):
	os.remove(sjmfile)

cfh = open(args.conf_file,'r')
jconf = json.load(cfh)

rmComments(jconf)

schema = args.schema
sfh = open(schema,'r')
jschema = json.load(sfh)

jsonschema.validate(jconf,jschema)
#
resources = False #such as reference, dbsnp, ...
try:
	resources = jconf['resources']
except KeyError:
	pass

for programName in jconf['analyses']:
#	print (jconf['analyses'][programName])
	pdico = jconf['analyses'][programName]
	enable = pdico['enable']
	if not enable:
		continue
	expandVars(pdico) #replace resoruce variables with their resource values
	cmd = makeCmd(programName,pdico)

if run:
	subprocess.call("sjm {sjmfile}".format(sjmfile=sjmfile),shell=True)


#from jsonschema import validate
#import json
#cfh = open("Conf/gatk.json",'r')
#conf = json.load(cfh)
#sfh = open("test_schema.json",'r')
#schema = json.load(sfh)

#python clinicalQc.py -s schema.json -c Conf/gatk.json -o TEST/sjm.txt  2>stderr.txt 
