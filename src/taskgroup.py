
import prettytable
require task

class TaskGroup:
	def __init__(self,tasks=[]):
		self.__tasks = []
		for task in tasks:
			self.task_add(task)

	def __add__(self,other):
		return isinstance(other,self.__class__) and \
			self.__class__( self.task_list() + other.task_list() )

	def task_list(self):
		return self.__tasks

	def task_add(self,task):
		if isinstance(task,Task) and not any(t==task for t in self.__tasks):
			self.__tasks.append(task)

	def task_delete(self,task):
		if isinstance(task,Task) and task in self.__tasks:
			self.__tasks.remove(task)

	def tabulate(self,heading=None):
		fields = ["ID","Task","Tags"]
		table = prettytable.PrettyTable(fields, padding_width=1)
		for i in fields: table.align[i] = "l"
		index = 0
		for task in self.__tasks:
			if "#hidden" in task.tag_list(): continue
			else: index = index+1
			table.add_row([index, task.text(), ", ".join(task.tag_list()) ])
		table, prefix = table.get_string(), ""
		if heading:
			x = table.find("\n")-len(heading)
			prefix = "\n"+"="*(x/2-1)+" "+heading+" "+"="*(x-x/2-1)
		return prefix+"\n"+table+"\n"

	def select(self,words):
		return self.__class__( self.__tasks if len(words)==0 else \
			[task for task in self.__tasks if any(word in task for word in words)] )

exports["TaskGroup"] = TaskGroup