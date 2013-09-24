
require task, prettytable

class TaskGroup:
	def __init__(self,tasks,name=""):
		self.name = name
		self.__tasks = []
		for task in tasks:
			self.task_add(task)

	def __repr__(self):
		return self.__tasks.__repr__()

	def task_list(self,unhide=False):
		return [task for task in self.__tasks if unhide or not task.tag_check("hidden")]

	def task_add(self,task):
		if isinstance(task,Task) and not any(t==task for t in self.__tasks):
			self.__tasks.append(task)
			self.__tasks.sort(key=lambda x: x.raw().lower())
			self.__tasks.sort(key=lambda x: x.group and x.group.name, reverse=True)

	def task_remove(self,task):
		if isinstance(task,Task) and task in self.__tasks:
			self.__tasks.remove(task)

	def tabulate(self, index=False, heading=None, performance=False):
		data = [Task.table_heading]
		data.extend( task.table_fields() for task in self.task_list() )
		if index:
			for i,row in enumerate(data):
				data[i] = ["Index" if i==0 else str(i-1)]+data[i]
		if performance:
			z = (task.report() for task in self.task_list())
			x, y = map(sum, zip(*z))
			performance = "Performance Index = %d/%d = %.2f%%" % (x,y,100.0*x/y)
		return prettytable(data,heading,performance)

	def select(self,words):
		words = [word for word in words if word!=""]
		if len(words)==0: return self.__class__( self.__tasks )
		tasks = []
		for task in self.__tasks:
			check = 1
			for word in words:
				if not word.startswith("~"): check &= word in task
				elif word.startswith("~~"): check &= word[1:] in task
				else: check &= word[1:] not in task
			if check: tasks.append(task)
		return self.__class__( tasks )
			

exports["TaskGroup"] = TaskGroup