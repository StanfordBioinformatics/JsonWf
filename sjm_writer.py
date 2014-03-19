
class Sjm:
	tab = "\t"	
	def __init__(self,outfile):
		self.out = outfile
		self.logfile = False
		self.host = False
		self.queue = False
		self.wdir = False
		self.modules = False
		self.mem = False
		self.time = False
		self.slots = False
		self.project = False

	def setHost(self,host):
		self.host = host

	def setLogfile(self,logfile):
		self.logfile = logfile

	def setWDir(self,wdir):
		self.wdir = wdir
	
	def setName(self,name):
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
		fout = open(self.out,'a')
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
		if mem:
			fout.write(self.tab + "memory " + mem + "\n")
		queue = self.getQueue()
		slots = self.getSlots()
		if slots:
			fout.write(tab + "slots " + slots + "\n")
		time = self.getTime()
		if time:
			fout.write(tab + "time " + time + "\n")
		if queue:
			fout.write(self.tab + "queue " +  queue + "\n")
		host = self.getHost()
		if host:
			fout.write(tab + "host " + host + "\n")
		project = self.getProject()
		if project:
			fout.write(tab + "project " + project + "\n")
		wdir = self.getWDir()
		if wdir:
			fout.write(tab + "directory" + wdir + "\n") 
		fout.write("job_end\n")
		for dependency in self.getOrders():
			fout.write("order {jobname} after {dependency}\n".format(jobname=self.getName(),dependency=dependency))
		fout.close()
