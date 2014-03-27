
class Job:
	"""
	By default, a job will get 1 slot and 10G mem, and a time limit of 7 days.
	"""
	tab = "\t"	
	slots = 1
	mem = "10G"
	time = "7d"
	queue = "seq_pipeline" #by default, soft and hard time=7d, no limit on mem

	@staticmethod
	def setDefaultSlots(num):
		slots = num

	@staticmethod
	def setDefaultMem(num):
		mem = num

	def __init__(self):
		self.outfile = False
		self.logfile = False
		self.host = False
		self.queue = False
		self.wdir = False
		self.modules = False
		self.time = False
		self.project = False

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

	def setCwd(self,wdir):
		self.wdir = wdir
	
	def setName(self,name):
		"""
		Name of the job.
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

	def setSlots(self,slots):
		self.slots = slots
	
	def setTime(self,time):
		self.time = time
	
	def setProject(self,project):
		self.project = project

	def setOrder(self,order):
		self.order = order

	def getHost(self):
		return self.host

	def getLogfile(self):
		return self.logfile

	def getSjmFile(self):
		return self.sjmfile

	def getWorkDir(self):
		return self.dir

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

	def getSlots(self):
		return self.getSlots()

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
		fout.write(tab + "slots " + slots + "\n")
		time = self.getTime()
		fout.write(tab + "time " + time + "\n")
		queue = self.getQueue()
		fout.write(self.tab + "queue " +  queue + "\n")
		host = self.getHost()
		if host:
			fout.write(tab + "host " + host + "\n")
		project = self.getProject()
		if project:
			fout.write(tab + "project " + project + "\n")
		wdir = self.getCwd()
		if wdir:
			fout.write(tab + "directory" + wdir + "\n") 
		fout.write("job_end\n")
		for dependency in self.getOrders():
			fout.write("order {jobname} after {dependency}\n".format(jobname=self.getName(),dependency=dependency))
		fout.close()
