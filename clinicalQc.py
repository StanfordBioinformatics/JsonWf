#!/srv/gs1/software/python/python-2.7/bin/python

import json
import sjm_writer
from argparse import ArgumentParser
import jsonschema
import subprocess


def makeCmd(progName,prog,sjmfile):	
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
		cmd += "java " + javavm + "-jar " + jar + " "
	else:
		cmd += progName + " "

	progArgs = prog['params']
	for arg in progArgs:
		val = progArgs[arg] #val can be empty string if boolean option
		if val.startswith("$"): #then it's a reference to a resources in the json file
			val = val.lstrip("$")
			val = resources[val] 
		cmd += arg + " " + val + " "

	job = sjm_writer.Job()
	job.setSjmFile(sjmfile)


	job.setCmd(cmd)


	modules = False
	try:
		modules = prog['modules']
		job.setModules(modules)
	except KeyError:
		pass

	qsub = prog['qsub']

	job.setName(qsub['name'])

	try:
		job.setResource(qsub['mem'])
	except KeyError:
		#property not required
		pass

	try:
		job.setResource(qsub['slots'])
	except KeyError:
		#property not required
		pass

	try:
		job.setResource(qsub['time'])
	except KeyError:
		#property not required
		pass


	try:
		job.setPe(qsub['pe'])
	except KeyError:
		#property not required

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

	job.write()






coreQsubArgs = ["time","mem","slots","pe","host","queue", "project","cwd","name"]

description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-s','--schema',default="/srv/gs1/software/gbsc/clinical_qc/schema.json", help="The JSON schema that will be used to validate the JSON configuration file. Default is %(default)s.")
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('-b','--bam-file',help="Mappings file in BAM format")
parser.add_argument('--vcf-file',help="Varicant Call File in VCF format")
parser.add_argument('-r','--reference',required=True,help="Reference genome in FASTA format")
parser.add_argument('--out-dir',help="Output folder")
parser.add_argument('-o','--outfile',required=True,help="Output SJM file.")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")
parser.add_argument('--no-run',action="store_true",help="Don't run the jobs, just generate sjm file.")

args = parser.parse_args()

sjmfile = args.outfile

cfh = open(args.conf_file,'r')
jconf = json.load(cfh)

schema = args.schema
print (schema)
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
	cmd = makeCmd(programName,pdico,sjmfile)
#print ("hi")




#from jsonschema import validate
#import json
#cfh = open("Conf/gatk.json",'r')
#conf = json.load(cfh)
#sfh = open("test_schema.json",'r')
#schema = json.load(sfh)
