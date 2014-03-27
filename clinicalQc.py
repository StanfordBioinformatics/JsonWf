#!/srv/gs1/software/python/python-2.7/bin/python

import json
import sjm_writer
from argparse import ArgumentParser
from jsonschema import validate
import subprocess


def makeCmd(name,prog):	
	cmd = ""

	modules = False
	try:
		modules = prog['modules']
		job.setModules(modules)
	except KeyError:
		pass

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
		cmd += name + " "

	progArgs = prog['params']
	for arg in progArgs:
		val = progArgs[arg] #val can be empty string if boolean option
		if val.startswith("$"): #then it's a reference to a resources in the json file
			val = val.lstrip("$")
			val = resources[val] 
		cmd += arg + " " + val + " "

	job = sjm_writer.Job()
	job.setName(name)

	queue = False
	try: 
		queue = prog['queue']
		job.setQueue(queue)
	except KeyError:
		pass

	cwd = False
	try:
		cwd = prog['cwd']
		job.setCwd(cwd)
	except KeyError:
		pass

	try:
		qsub = prog['qsub']
	except KeyError:
		#property not required
		pass

	if qsub:
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
			job.setHost(qsub['host'])
		except: KeyError:
			#property not required
			pass

		try:
			job.setProject9qsub['project'])
		except: KeyError:
			#property not required
			pass

	job.write




description = ""
parser = ArgumentParser(description=description)
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('-b','--bam-file',help="Mappings file in BAM format")
parser.add_argument('--vcf-file',help="Varicant Call File in VCF format")
parser.add_argument('-r','--reference',required=True,help="Reference genome in FASTA format")
parser.add_argument('--out-dir',help="Output folder")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")
parser.add_argument('--no-run',action="store_true",help="Don't run the jobs, just generate sjm file.")

args = parser.parse_args()

conf = args.conf_file

jconf = json.load(open(conf,'r'))

resources = False #such as reference, dbsnp, ...
try:
	resources = jconf['resources']
except KeyError:
	pass

for programName in jconf['programs']:
	pdico = jconf['programName']
	enable = pdico['enable']
	if not enable:
		continue
	cmd = makeCmd(name,pdico)
print ("hi")




#from jsonschema import validate
#import json
#cfh = open("Conf/gatk.json",'r')
#conf = json.load(cfh)
#sfh = open("test_schema.json",'r')
#schema = json.load(sfh)
