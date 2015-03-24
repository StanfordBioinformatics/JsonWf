#!/srv/gs1/software/python/python-2.7/bin/python

#Copyright 2015 Nathaniel Watson

#This file is part of JsonWf.

#JsonWF is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#JsonWF is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import workflow
import os
import subprocess
from argparse import ArgumentParser

description = "Given a JSON configuration file that abides by the packaged schema.json file, this program will validate the conf file, then build an SJM file. Variable substitution is also supported, whereby any value in the conf file that begins with a '$' may be replaced by a global resource that is specified either on the command-line (CL) as an argument, or in the conf file itself. In the conf file, resources include the global resource and qsub objects.  CL set resources override conf file resources. For help with validating your JSON conf file, copy and past it into the online JSON Schema Validator at http://jsonformatter.curiousconcept.com/.  By default, each analysis in the conf file is executed in the working directory specified by --outdir. This can be overwritten in a given analysis using the 'directory' property of the 'qsub' object.  For each job submitted run on the cluster, its stdout and stderr files will be written a directory called JobStatus, which is a subdirectory of --outdir; this cannot be changed."

parser = ArgumentParser(description=description)
#parser.add_argument('--schema',default="/srv/gs1/software/gbsc/kwality/1.0/schema.json", help="The JSON schema that will be used to validate the JSON configuration file. Default is %(default)s.")
parser.add_argument('--outdir',help="(Required when none of --analyses, --enabled, and --disabled are specified) The directory to output all result files. Can be a relative or absolute directory path. Will be created if it does't exist already. Will be added as a global resource. Serves as the default working directory when jobs are submitted to the cluster, for each analysis that doesn't set the working directory.")
parser.add_argument('-c','--conf-file',required=True,help="Configuration file in JSON format.")
parser.add_argument('resources',nargs="*",help="One or more space-delimited key=value resources that can override or append to the keys of the resoruce object in the JSON conf file. The value of the --outdir option will automatically be added here with the variable name 'outdir'.")
parser.add_argument('-s','--sjmfile',help="(Required when none of --analyses, --enabled, and --disabled are specified) Output SJM file name (w/o directory path). The sjm file will be created in the directory passed to --outdir. If the file already exists, it will be appended to.")
parser.add_argument('-v','--verbose',help="Print extra details to stdout.")
parser.add_argument('--run',action="store_true",help="Don't just generate the sjm file, run it too. By default, the program does not wait for the sjm job to complete; see --wait.")
parser.add_argument('--wait',action="store_true",help="When --run is specified, indicates that the script should wait for the sjm job to complete before exiting.")
showAnalysesGroup = parser.add_mutually_exclusive_group()
showAnalysesGroup.add_argument('--analyses',action="store_true",help="Display a list of availble analyses present in --conf-file.")
showAnalysesGroup.add_argument('--enabled',action="store_true",help="Display a list of enabled analyses present in --conf-file.")
showAnalysesGroup.add_argument('--disabled',action="store_true",help="Display a list of disabled analyses present in --conf-file.")
group = parser.add_mutually_exclusive_group()
group.add_argument('--enable-all-except',help="Comma-delimited list of case-sensitive analysis names from --conf-file to disable. All others will be enabled.")
group.add_argument('--disable-all-except',help="Comma-delimited list of case-sensitive analysis names from --conf-file to enable. All others will be disabled.")


args = parser.parse_args()
if args.wait and not args.run:
	parser.error("Argument --wait cannot be specified w/o --run")

if not args.analyses and not args.enabled and not args.disabled:
	if not args.outdir:
		parser.error("You must supply the --outdir argument!")
	if not args.sjmfile:
		parser.error("You must supply the --sjmfile argument!")

outdir = args.outdir
if not outdir:
	outdir = ""
outdir = os.path.abspath(outdir)
sjmfile = args.sjmfile
resources = {}
for i in args.resources:
	key,val = i.split("=")	
	if os.path.exists(val):
		val = os.path.abspath(val)
	resources[key] = val
wf = workflow.Workflow(conf=args.conf_file,outdir=outdir,resources=resources)

#if the user supplied an analysis category (any of the options --analyses, --enabled, or --disabled)
# recall that only one category can be passed in a given call to the program, then the analyses within the 
# given category will be printed to stdout and then the program will exit:
meta = wf.showAnalyses(all=args.analyses,enabled=args.enabled,disabled=args.disabled)
if meta:
	print("\n" + meta)
	parser.exit()

disableList = args.enable_all_except
if disableList:
	disableList = [x.strip() for x in disableList.split(",")]
	for i in disableList:
		if i not in wf.analysisDict:
			parser.error("Case-sensitive Analysis name {analysis} provided to --enable-all-except doesn't exist in {conf}.".format(analysis=i,conf=args.conf_file))

enableList = args.disable_all_except
if enableList:
	enableList = [x.strip() for x in enableList.split(",")]
	for i in enableList:
		if i not in wf.analysisDict:
			parser.error("Case-sensitive analysis name {analysis} provided to --disable-all-except doesn't exist in {conf}.".format(analysis=i,conf=args.conf_file))

if disableList:
	for analysisName in wf.analysisDict:
		if analysisName in disableList:
			wf.setAnalysisStatus(analysisName,False)
		else:
			wf.setAnalysisStatus(analysisName,True)
elif enableList:
	for analysisName in wf.analysisDict:
		if analysisName in enableList:
			wf.setAnalysisStatus(analysisName,True)
		else:
			wf.setAnalysisStatus(analysisName,False)

run = args.run
sjmfile = os.path.basename(sjmfile)
sjmfile = os.path.join(outdir,sjmfile)
if os.path.exists(sjmfile):
	os.remove(sjmfile)


wf.processAnalyses()
wf.buildSjmFile(sjmfile=sjmfile)

if run:
	if args.wait:
		subprocess.call("sjm -i {sjmfile}".format(sjmfile=sjmfile),shell=True)
	else:
		subprocess.Popen("sjm {sjmfile}".format(sjmfile=sjmfile),shell=True)
