#!/srv/gs1/software/python/python-2.7/bin/python

#Copyright 2015 Nathaniel Watson

#This file is part of JsonWF.

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

import sys
import os
import json
import sjm_writer
import jsonschema
import subprocess
import re
import copy



SCHEMA = os.path.join(os.path.dirname(__file__),"schema.json")

class Duplicate(Exception):
	pass	

class CircularDependency(Exception):
	def __init__(self,msg):
		self.msg = msg

class Workflow:
	###varReg finds variables of the type $var and ${var} and ${var%%.txt}, ... variables can be mixed in with some string, such as a file path.
	varReg = re.compile(r'(\${(?P<brace>[\d\w]+))|(\$(?P<dollar>[\d\w]+))')
	numReg = re.compile(r'\d$')
	coreQsubArgs = ["time","mem","slots","pe","host","queue", "project","outdir","-e","-o","directory","name"]

	def __init__(self,conf,outdir,resources={}):
		"""
		Args : conf - the JSON configuration file
           resources - dict of additional resources
		"""
		self.conf,self.schema = self.validate(conf=conf)
		if not os.path.exists(outdir):
		  os.mkdir(outdir)
		logdir = os.path.join(outdir,"JobStatus")
		if not os.path.exists(logdir):
		  os.mkdir(logdir)
		resources['outdir'] = outdir
		resources['logdir'] = logdir
		self.resources = {}
		self.addToResources(dico=resources) #updates self.resources
	
		jsonResources = {}
		try:
		  jsonResources = self.conf['resources']
		except KeyError:
	 		pass
		self.updateConfVals(jsonResources) #the resources object in the conf file can utilize (reference) the resources supplied to the constructor (including outdir and logdir)
		self.addToResources(dico=jsonResources) 

		self.globalQsub = {}	
		try:
			self.globalQsub = self.conf['globalQsub']
		except KeyError:
			print("Warning - Did not find a globalQsub object in your conf file in the location allowed by the schema; continuing ...")

		self.analysisDict = {}
		for analysisConf in self.conf['analyses']:
			name = analysisConf['analysis']
			if name in self.analysisDict:
				raise ValueError("Duplicate analysis name {}".format(name))
			self.analysisDict[name] = analysisConf

	def __iter__(self):
		return iter(self.conf)

	def validate(self,conf):
		"""
		Function : Validates the JSON configuration file against the JSON schema
		Args     : conf - JSON conf file
		Returns  : two-item tuple containing the configuration and schema as dictionaries
		"""
		cfh = open(conf,'r')
		jconf = json.load(cfh)
		self.rmComments(jconf)
		sfh = open(SCHEMA,'r')
		jschema = json.load(sfh)
		jsonschema.validate(jconf,jschema)
		return jconf,jschema

	def checkCircDeps(self):
		"""
		Function : Checkes for circular dependencies between analyses. If one is found, raises a CircularDependency exception.
		"""
		for analysis in self.analysisDict:
			deps = analysis['dependencies']
			for d in deps:
				depDeps = self.analysisDict[d]['dependencies']
				if name in depDeps:
					raise CircularDependency("Error: Circular dependencies found between analyses {analysis1} and {analysis2}".format(analysis1=analysis,analysis2=d))

	def rmComments(self,dico):
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
				self.rmComments(val)


	def getDependencies(self):
		"""
		Function :
		Args     :
		Returns  :
		"""
		class Dependency:
			def __init__(self,analysis,dependencies):
				self.name = analysis
				self.dependencies = dependencies

		#create a dict with each analysis name in it as the key, and value as list.
		# even analyses with no dependencies will appear in the dict, and have the empty list.
		allDependencies = {}
		for analysis in self.getEnabledAnalyses():
			#getAnalysisDependencies() only retrieves enabled dependencies
			dependencies = self.getAnalysisDependencies(analysis)
			allDependencies[analysis] = Dependency(analysis,dependencies)
		return allDependencies

	def getDepTree(self):
		"""
		Calulates the order in which jobs are to be run
		"""
		allDependencies = self.getDependencies()
		analysisNameDico = {}
		for i in self.getEnabledAnalyses():
			analysisNameDico[i] = 1
		levelDico = {}
		level = 0
		while analysisNameDico:
			level += 1
			levelDico[level] = []
			for name in analysisNameDico.keys():
				analysis = allDependencies[name]
				if analysis.dependencies:
					continue
				levelDico[level].append(analysis)
				analysisNameDico.pop(name)
				for i in allDependencies:
					if name in allDependencies[i].dependencies:
							allDependencies[i].dependencies.remove(name)
		return levelDico

	def enabled(self,analysis):
		"""
		Function : Checks whether an analysis is enabled or not.
		Args     : analysis - str. An analysis name.
		"""
		return self.analysisDict[analysis]['enable']

	def showAnalyses(self,disabled=False,enabled=False,all=False):
		""" 
		Function : Prints to stdout all analyses in the passed in dict, one per line.
		"""
		allAnalyses = self.getAllAnalyses()
		numAllAnalyses = len(allAnalyses)
		returnString = ""
		if all:
			analyses = allAnalyses
			returnString += "All Analyses ({}):\n".format(numAllAnalyses)
		elif enabled:
			analyses = self.getEnabledAnalyses()
			returnString += "Enabled Analyses ({0}/{1}):\n".format(len(analyses),numAllAnalyses)
		elif disabled:
			analyses = self.getDisabledAnalyses()
			returnString += "Diabled Analyses ({0}/{1}):\n".format(len(analyses),numAllAnalyses)
		else:
			return

		returnString += "{name:<35}{desc}\n".format(name="Name:",desc="Description:")
		for i in sorted(analyses):
		  returnString += "{analysis:<35}{desc}\n".format(analysis=i,desc=analyses[i])
		return returnString


	def getDescription(self,analysis):
		"""
		Function : Retrieves the 'description' of an analysis, if this keyword is present. This is a keyword defined in the JSON Schema draft 4.
		Args     : analysis - str. The name of an analysis.
		"""
		try:
			desc = self.analysisDict[analysis]['description']
		except KeyError:
			return None
		return desc
	
	def getTitle(self,analysis):
		"""
		Function : Retrieves the 'title' of an analysis, if this keyword is present. This is a keyword defined in the JSON Schema draft 4.
		Args     : analysis - str. The name of analysis.
		"""
		try:
			title = self.analysisDict[analysis]['title']
		except KeyError:
			return None
		return title
	
	def getDescriptionOrTitle(self,analysis):
		"""
		Function : Given an analysis name, tries to return it's description if the 'description' keyword is present.
							 If not, then tries to return it's title if the 'title' keyword is present. If neither is present,
							 returns the None object.
		"""
		desc = self.getDescription(analysis)	
		if desc:
			return desc
		title = self.getTitle(analysis)
		return title
	
	def getAllAnalyses(self):
		"""
		Function : Returns a dict of all analyses present in the JSON conf file as keys and as values as a string being the description
							 if the 'description' keyword is present, else the title if the 'title' keyword is present, else the None object.
		"""
		dico = {}
		for analysis in self.analysisDict:
			val = self.getDescriptionOrTitle(analysis)
			dico[analysis] = val
		return dico
	
	def getDisabledAnalyses(self):
		"""
		Function : Returns a dict of all disabled analyses present in the JSON conf file as keys and as values as a string being the description
							 if the 'description' keyword is present, else the title if the 'title' keyword is present, else the None object.
		"""
		dico = {}
		for analysis in self.analysisDict:
			if not self.enabled(analysis):
				val = self.getDescriptionOrTitle(analysis)
				dico[analysis] = val
		return dico
	
	def getEnabledAnalyses(self):
		"""
		Function : Returns a dict of all enabled analyses present in the JSON conf file as keys and as values as a string being the description
							 if the 'description' keyword is present, else the title if the 'title' keyword is present, else the None object.
		"""
		dico = {}
		for analysis in self.analysisDict: 
			if self.enabled(analysis):
				val = self.getDescriptionOrTitle(analysis)
				dico[analysis] = val
		return dico

	def setAnalysisStatus(self,analysis,enable=True):
		"""
		Function : Sets analysis to enabled or disabled
		Args     : analysis - str. An analysis name.
							 enable - bool
		"""
		if enable:
			self.analysisDict[analysis]['enable'] = 1
		else:
			self.analysisDict[analysis]['enable'] = 0	
	
	def addToResources(self,key=False,value=False,dico={}):
		"""
	   Function : Adds key and value pairs to self.resources, while creating environment variables from them at the same time. In the function call, a key and value pair may be  passed in, a dict may be passed in,
							  or both. Raises a Duplicate exception if the key already exists in self.resources. If a dict is provided, nested dict objects are supported, but all nesting will be lost when added to self.resources.
		 Args     : key,value - str.
								dico - dict of variables to add to the environment, where each key and value are strings.
		 Returns  : 
		"""
		#os.environ internally calls os.putenv, which will also set the environment variables at the outter shell level.
		if key and not value:
			raise ValueError("kwality.addToResources() must have argument 'value' set when argument 'key' is set.")
		elif value and not key:
			raise ValueError("kwality.addToResources() must have argument 'key' set when argument 'value' is set.")	
	
		if key:
			key = str(key)
			value = str(value)
			if key not in self.resources:
				self.resources[key] = value
				os.environ[key] = value
			else:
				raise Duplicate("Found duplicate key {key} in your resources".format(key=key))
		
		for key in dico:
			value = dico[key]
			if type(value) is dict:
				self.addToResources(dico=value)
			key = str(key)
			value = str(dico[key])
			if key not in self.resources:
				self.resources[key] = value
				os.environ[key] = value
			else:
				msg = "Found duplicate key '{key}' in your resources".format(key=key)	
				raise Duplicate(msg)

	def getAnalysisDependencies(self,analysis):
		"""
		Args : analysis - an Dependency() instance
		"""
		try:
			deps = self.analysisDict[analysis]['dependencies']
		except KeyError:
			return []
		enabledDeps = []
		for i in deps:
			if not self.enabled(i):
				continue
			else:
				enabledDeps.append(i)
		return enabledDeps

	def rmDependency(self,dependency):
		"""
		Function : Given a dict with analysis names that have dependencies as keys, and values as lists of dependency names, removes
	             the passed in dependency named from each value.
		Args     : dependency - an analysis name
		"""
		for name in self.analysisDict:
			deps = self.analysisDict[name]['dependencies']
			if dependency in deps:
				deps.remove(dependency)

	def resolveJsonPointer(self,txt):
		"""
		Function :
		Args     :
		Returns  :
		"""
		origTxt = txt
		txt = txt.lstrip("#/")
		num = None
		if self.numReg.search(txt):
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

	def updateConfVals(self,dico):
		"""
		Function : Given a dict, looks at all setting values and find any variables (words beginning with '$') 
	             and check if a parameter with the same name (omitting the '$') exists in self.resources
	             Works recursivly for a dict within a dict.
	
		Args     : analysisName - the name of an analysis
		"""
		for key in dico:
			val = dico[key]
			valType = type(val)
			if valType == str or valType == unicode:
				if val.startswith("#"):
					origVal = val
					val = self.resolveJsonPointer(val)
					print ("Resolved {origVal} to {val}".format(origVal=origVal,val=val))
				resourceValue = self.expandVariables(val)
				dico[key] = resourceValue
	   
			elif valType == list or valType == tuple:
				count = -1
				for part in val:
					count += 1
					if part.startswith("#/"):
						origPart = part
						part = self.resolveJsonPointer(part)
						print ("Resolved {origPart} to {part}".fommat(origPart=origPart,part=part))
					resourceValue= self.expandVariables(part)
					dico[key][count] = resourceValue
						
			elif valType == dict:
				self.updateConfVals(val)		

	def expandVariables(self,txt):
		"""
		Function : Given a string, looks for variables with BASH syntax.
							 Finds each such variable in the string and checks to see if the variable name exists in the self.resources. 
							 If it doesn't, a ValueError is raised. If all found variables exist, then 
							 variable expansion is performed through the shell on the input string. This relies 
							 on all resources in self.resources having been added to the environment (and shell environment) with a call 
							 to os.environ, for example.  
		Args     : txt - str.
		Returns  : str. txt that has undergone variable expansion via the shell.
		"""
		groupiter = self.varReg.finditer(txt)
		for i in groupiter:
			dico = i.groupdict()
			varName = dico['brace']
			if not varName:
				varName = dico['dollar']
			try: 
				replace = self.resources[varName]
			except KeyError:
				raise ValueError("Error: In configuration file, varible {varName} is not a resource.".format(varName=varName))
	
			##Hold off on update below, let all updates happen simultaneously though shell expansion with the call the subprocess below
			#txt = re.sub(r'\${{{varName}}}'.format(varName=varName),replace,txt) 
			print("Updating {varName} to {replace}".format(varName=varName,replace=replace))
		txt = subprocess.Popen('echo -n "{txt}"'.format(txt=txt),shell=True,stdout=subprocess.PIPE).communicate()[0]
		return txt
        

	def makeCmdLine(self,analysisName):	
		"""
		Function : String together a command and it's arguments from the input dictionary. The analysis objects for java programs should have the properties 'jar' and 'javavm' set. All others should use the 'program' property.
	             If both 'jar' and 'program' are set, then 'program' will be ignored.
		Args     : analysisName - name of an analysis
		"""
		cmd = ""
		conf = self.analysisDict[analysisName]
		jar = False
		try:
			jar = conf['jar']
		except KeyError:
			pass
	
		javavm = "-Xmx2G"
		try:
			javavm = conf['javavm']
		except KeyError:
			pass
	
		if jar:
			cmd += "java " + javavm + " " + "-jar " + jar + " "
		else:
			cmd += conf['program'] + " "
	
		progOptions = False
		try:
			progOptions = conf['params']
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
			progArgs = conf['args'] 
		except KeyError:
			pass
		if progArgs:
			for arg in progArgs:
				cmd += " " + arg + " "

		return cmd


	def sjmBlock(self,sjmfile,cmd,analysisName):	
		"""
		Function :
		Args     : sjmfile - str. the sjmfile the command block will be written to (in append mode).
							 cmd - str. The command to run.
							 analysisName - str. The name of one of the analysis objects in the analyses arrary of the conf file.
		"""
		conf = self.analysisDict[analysisName]
		qsub = conf['qsub']
		#If 'name' key defined in qsub object, then use that as the job name in SJM, otherwise, use the analysisName as the jobname
		try:
			jobname = qsub['name']
		except KeyError:
			jobname = analysisName
		job = sjm_writer.Job(jobname)
		job.setSjmFile(sjmfile)
		job.setCmd(cmd)
	
		directory = self.resources['outdir'] #working directory (dir in which to execute the command)
		try:
			directory = qsub['directory']
			if not os.path.exists(directory):
				raise OSError("Directory {directory} does not exist! Check 'directory' property in the qsub object of analysis {analysis}.".format(directory=directory,analysis=analysis))
		except KeyError:
			pass
	
		job.setWorkDir(directory)
		job.setJobLogDir(self.resources['logdir'])
	
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
			if arg not in self.coreQsubArgs:
				qsub_other += arg + " " + qsub[arg] + "  "
	
		if qsub_other:
			job.addAdditionalOpts(qsub_other)
	
	
		modules = False
		try:
			modules = conf['modules']
			job.setModules(modules)
		except KeyError:
			pass
	
		job.write() #closes the file too

	def buildSjmFile(self,sjmfile):
		"""
		Function: Writes all analyses in SJM format in the passed-in file.
		"""
		for analysisName in self.analysisDict:	
			cmd = self.makeCmdLine(analysisName)
			self.sjmBlock(sjmfile,cmd,analysisName)
	
		sjm_writer.writeDependencies(self.getDependencies(),sjmfile)

	def processAnalysis(self,analysisName):
		"""
		Function :
		Args     : analysis - an analysis name
		"""
		#check if output direcories are defined, and deal with these first, because it's allowed for
		# the JSON resource dict called 'outfiles' to reference variables in the 'outdirs' JSON resource dict.
		# As a result, any keys in the outdirs object will be added to the environment. Note that the keys in the outfiles
		# object will also be added to the environment.  These two objects are the only cases where  global resources can be defined outside of the "resources" object or CL.
		# This is also the only time in the code that I allow a JSON resource to be able to reference other JSON resources.
		# 
		analysisConf = self.analysisDict[analysisName]
		outdirs = {}
		try:
			outdirs = analysisConf['outdirs'] #outdirs, if defined, is an array of objects
		except KeyError:
			pass
		if outdirs:
			for i in outdirs: #i is a dict of one key and a string value
				self.updateConfVals(i)
				for key in i: #should only be a single key, anyways the schema mandates that
					path = i[key]
					if not os.path.exists(path):
						os.mkdir(path)
				self.addToResources(dico=i)
			analysisConf.pop('outdirs')
	
		outfiles = {}
		try:
			outfiles = analysisConf['outfiles']
		except KeyError:
			pass
		if outfiles:
			for i in outfiles:
				self.updateConfVals(i)
				self.addToResources(dico=i)
			analysisConf.pop('outfiles')
	
		qsubDico = {}
		try:
			qsubDico = analysisConf['qsub']	
		except KeyError:
			pass
		for i in self.globalQsub:
			if i not in qsubDico: #don't overwite!
				qsubDico[i] = self.globalQsub[i]
		self.updateConfVals(analysisConf) #replace resource variables with their resource values

	def processAnalyses(self):
		"""
		Calls self.processAnalysis() for each analysis and in the order in which the analyses will be run.
		"""
		levelDico = self.getDepTree()
		for level in sorted(levelDico):
			for analysis in levelDico[level]:
				print("\n")
				print("Processing Analysis {analysis}".format(analysis=analysis.name))
				#The following call to processAnalysis() does this: add outdirs and outfiles as global resources, adds set difference in keys of globalQsub object to analysis's qsub object,
				# and run self.updateConfVals() on the analysis conf
				self.processAnalysis(analysis.name)
