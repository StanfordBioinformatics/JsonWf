
class Job:
	"""
	By default, a job will get 1 slot and 10G mem, and a time limit of 7 days.
	"""
	tab = "\t"	
	slots = 1
	mem = "10G"
	queue = "seq_pipeline" #by default, soft and hard time=7d, no limit on mem
	pe = "shm"

	@staticmethod
	def setDefaultSlots(num):
		slots = num

	@staticmethod
	def setDefaultMem(num):
		mem = num

	def __init__(self,name):
		self.setName(name)
		self.outfile = False
		self.logfile = False
		self.host = False
		self.wdir = False
		self.modules = False
		self.project = False


	def setOtherOpts(opts):
		self.otherOpts = opts

	def addOtherOpt(opt):
		others = self.getOtherOpts()
		others += " " + opt
		self.setOtherOpts(others)

	def setResource(resource,val):
		if resource == "slots":
			self.slots = val
		elif resource == "mem":
			self.mem = val
		elif resource == "time":
			self.time = val 
	

	def setHost(self,host):
		self.host = host

	def setLogfile(self,logfile):
		self.logfile = logfile

	def setSjmFile(self,sjmfile):
		self.sjmfile = sjmfile

	def setCwd(self,cwd):
		self.cwd = cwd
	
	def setName(self,name):
		"""
		Set job name
		"""
		self.name = name
	
	def setCmd(self,cmd):
		self.cmd = cmd

	def setWorkDir(self,dir):
		self.dir = dir

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

	def setOrder(self,order):
		self.order = order

	def getOtherOpts(self0:
		return self.otherOpts

	def getHost(self):
		return self.host

	def getLogfile(self):
		return self.logfile

	def getSjmFile(self):
		return self.sjmfile

	def getCwd(self):
		return self.cwd

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

	def getOrder(self):
		return self.order

	def write(self):
		"""
		Opens the SJM file in append mode.
		"""
		fout = open(self.getSjmFile(),'a')
		logfile = self.getLogfile()
		if logfile:
			fout.write("log_dir " + logfile + "\n")
		fout.write("job begin\n")
		fout.write(self.tab + self.getName() + "\n")
		fout.write(self.tab + self.getCmd() + "\n")
		modules = self.getModules()
		for mod in modules:
			fout.write(self.tab + "module " +  mod + "\n")
		mem = self.getMem()
		fout.write(self.tab + "memory " + mem + "\n")
		slots = self.getSlots()
		fout.write(self.tab + "slots " + str(slots) + "\n")
		time = self.getTime()
		fout.write(self.tab + "time " + time + "\n")
		queue = self.getQueue()
		fout.write(self.tab + "queue " +  queue + "\n")
		host = self.getHost()
		if host:
			fout.write(self.tab + "host " + host + "\n")
		project = self.getProject()
		if project:
			fout.write(self.tab + "project " + project + "\n")

		try:
			cwd = self.getCwd()
			fout.write(self.tab + "directory " + cwd + "\n") 
		except AttributeError:
			pass

		otherOpts = self.getOtherOpts()
		if otherOpts:
			fout.write(self.tab + "sched_options " + otherOpts + "\n")

		fout.write("job_end\n")
#		for dependency in self.getOrders():
#			fout.write("order {jobname} after {dependency}\n".format(jobname=self.getName(),dependency=dependency))
		fout.close()
