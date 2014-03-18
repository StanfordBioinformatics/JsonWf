
class Sjm:
	tab = "\t"	
	def __init__(self,outfile,logfile=False):
		self.out = outfile
		self.logfile = logfile
	
	def setName(self,name):
		self.name = name
	
	def setCmd(self,cmd):
		self.cmd = cmd


	def setModules(self,modules):
		self.modules = modules

	def setQueue(self,queue):
		self.queue = queue	
	
	def setMem(self,mem):
		self.mem = mem
	
	def setOrder(self,order):
		self.order = order

	def getLogfile(self):
		return self.logfile

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
		for mod in self.getModules():
			fout.write(self.tab + mod + "\n")
		fout.write(self.tab + self.getQueue() + "\n")
		fout.write(self.tab + self.getMem() + "\n")
		fout.write("job_end\n")
		for dependency in self.getOrders():
			fout.write("order {jobname} after {dependency}\n".format(jobname=self.getName(),dependency=dependency))
		fout.close()
