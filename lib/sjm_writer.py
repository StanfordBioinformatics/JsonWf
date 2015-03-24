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

class Job:
	"""
	By default, a job will get 1 slot and 10G mem, and a time limit of 7 days.
	"""
	tab = "\t"	
	queue = ""
	mem = "10G"
	pe = "shm"

	@staticmethod
	def setDefaultSlots(num):
		slots = num

	@staticmethod
	def setDefaultMem(num):
		mem = num

	def __init__(self,name):
		self.setName(name)
#		self.queue = False
		self.outfile = False
		self.logfile = False
		self.host = False
		self.wdir = False
		self.modules = False
		self.project = False
		self.time = False
		self.slots = False
		self.workdir = False
		self.jobLogDir = False
		self.additionalOpts = ""
		self.dependencies = []

	def setAdditionalOpts(self,opts):
		"""
		Function : 
		Args     : opts - sting of additional qsub options that aren't supported by existing specific class methods"
		"""
		self.additionalOpts = opts

	def addAdditionalOpts(self,opt):
		"""
		Args : opt - str. of options and their values
		"""
		ads = self.getAdditionalOpts()
		ads += " " + opt
		self.setAdditionalOpts(ads)

	def setResource(self,resource,val):
		"""
		Function : Sets cluster resource attributes.
		Args     : resource - str. Currenlty can be one of "slots", "mem", or "time". Raises a ValueError if resources isn't a recognized keyword.
		"""
		if resource == "slots":
			self.slots = val
		elif resource == "mem":
			self.mem = val
		elif resource == "time":
			self.time = val 
		else:
			raise ValueError("Unrecognized resource {resource}".format(resource=resource))
	

	def setHost(self,host):
		self.host = host

	def setLogfile(self,logfile):
		self.logfile = logfile

	def setSjmFile(self,sjmfile):
		self.sjmfile = sjmfile

	def setJobLogDir(self,jobLogDir):
		"""
		Function : Sets the job log directory to which GE stdout and stderr files will be written. This calls setAdditionalOpt().
		Args     : jobLogDir - str. specifying the job log directory 
		"""
		self.jobLogDir = jobLogDir
		newOpt = "-e {0} -o {0}".format(jobLogDir)
		self.addAdditionalOpts(newOpt)

	def setName(self,name):
		"""
		Set job name
		"""
		self.name = name
	
	def setCmd(self,cmd):
		self.cmd = cmd

	def setWorkDir(self,dir):
		self.workdir = dir

	def setModules(self,modules):
		self.modules = modules

	def setQueue(self,queue):
		self.queue = queue	

	def setMem(self,mem):
		self.mem = mem
	
	def setPe(self,pe):
		"""
		Parallel Environment
		"""
		self.pe = pe

	def setSlots(self,slots):
		self.slots = slots
	
	def setTime(self,time):
		self.time = time
	
	def setProject(self,project):
		self.project = project

	def addDependency(self,dependency):
		self.setDependencies(self.getDependencies().append(dependency))

	def setDependencies(self,dependencies):
		"""
		Args : dependencies - list of jobnames that the current jobs depends on completing before running.
		"""
		self.dependencies = dependencies

	def getAdditionalOpts(self):
		return self.additionalOpts

	def getHost(self):
		return self.host

	def getLogfile(self):
		return self.logfile

	def getSjmFile(self):
		return self.sjmfile

	def getWorkDir(self):
		return self.workdir

	def getJobLogDir(self):
		return self.jobLogDir

	def getName(self):
		return self.name

	def getCmd(self):
		return self.cmd

	def getModules(self):
		return self.modules

	def getQueue(self):
		return self.queue

	def getMem(self):
		return self.mem


	def getPe(self):
		return self.pe

	def getSlots(self):
		return self.slots

	def getTime(self):
		return self.time

	def getProject(self):
		return self.project

	def getDependencies(self):
		return self.dependencies

	def write(self):
		"""
		Opens the SJM file in append mode.
		"""
		fout = open(self.getSjmFile(), 'a')
		logfile = self.getLogfile()
		if logfile:
			fout.write("log_dir " + logfile + "\n")
		fout.write("job_begin\n")
		fout.write(self.tab + "name " + self.getName() + "\n")
		fout.write(self.tab + "cmd " + self.getCmd() + "\n")
		modules = self.getModules()
		if modules:
			for mod in modules:
				fout.write(self.tab + "module " +  mod + "\n")
		mem = self.getMem()
		fout.write(self.tab + "memory " + mem + "\n")
		slots = self.getSlots()
		if slots:
			fout.write(self.tab + "slots " + str(slots) + "\n")

		time = self.getTime()
		if time:
			fout.write(self.tab + "time " + time + "\n")

		queue = self.getQueue()
		if queue:
			fout.write(self.tab + "queue " +  queue + "\n")
		host = self.getHost()
		if host:
			fout.write(self.tab + "host " + host + "\n")
		project = self.getProject()
		if project:
			fout.write(self.tab + "project " + project + "\n")


		workdir = self.getWorkDir()
		if workdir:
			fout.write(self.tab + "directory " + workdir + "\n") 

		additionalOpts = self.getAdditionalOpts()
		if additionalOpts:
			fout.write(self.tab + "sched_options " + additionalOpts + "\n")

		fout.write("job_end\n\n")
		fout.close()

def writeDependencies(dico,sjmfile):
	"""
	Function : Writes job dependencies to an SJM file.
	Args     : dico - dict where keys are jobnames and each value is a list of jobnames. Each key depends on the completion of all jobs in it's value before it can run.
						 sjmfile - a file in SJM format
	"""
	fout = open(sjmfile,'a')
	for jobname in dico:
		for dependency in dico[jobname].dependencies:
			fout.write("order {jobname} after {dependency}\n".format(jobname=jobname,dependency=dependency))
	fout.close()
