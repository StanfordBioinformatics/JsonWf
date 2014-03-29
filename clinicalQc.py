#!/srv/gs1/software/python/python-2.7/bin/python

import sys
import os
import json
import sjm_writer
from argparse import ArgumentParser
import jsonschema
import subprocess


	

def expandVars(prog):
  for i in prog:
    j = prog[i]
    jtype = type(j)
    if jtype == str or jtype == unicode:
      if j.startswith("$"):
        j = j.lstrip("$")
        cmdArg = False
        try: 
          cmdArg = args.__getattribute__(j)
        except AttributeError,err:
          pass
        print("#" + j + "#")
        if cmdArg:
          prog[i] = cmdArg
          print("Updating {j} to {cmdArg}".format(j=j,cmdArg=cmdArg))
        elif j in resources:
          prog[i] = resources[j]
          print("Updating {j} to {res}".format(j=j,res=resources[j]))
        else:
          #assume to be an enviroment variable
          print >> sys.stderr, ("Assuming line {line} to contain an environment variable and not a resource".format(line=prog[i]))
        
    elif type(j) == dict:
      expandVars(j)		
			


def makeCmd(progName,prog):	
	print (progName)
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
parser.add_argument('-r','--reference',required=True,help="Reference genome in FASTA format")
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

for programName in jconf['programs']:
#	print (programName)
#	print (jconf['programs'][programName])
	pdico = jconf['programs'][programName]
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

#python clinicalQc.py -s schema.json -c Conf/gatk.json -r conf.json -o TEST/sjm.txt  2>stderr.txt 
