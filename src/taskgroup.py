
require task, prettytable

class TaskGroup:
	def __init__(self,tasks=[],name=""):
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

	def task_remove(self,task):
		if isinstance(task,Task) and task in self.__tasks:
			self.__tasks.remove(task)

	def tabulate(self, date, heading=None, index=False):
		data = [ Task.table_heading ]
		data.extend( task.table_fields(date.date) for task in self.task_list() )
		data = [data[0]]+sorted(data[1:], key=lambda x: x[0], reverse=True)
		if index:
			for i,row in enumerate(data):
				data[i] = ["Index" if i==0 else i-1]+data[i]
		result, prefix = prettytable(data), ""
		if heading:
			x = result.find("\n")-len(heading)
			prefix = "="*(x/2-1)+" "+heading+" "+"="*(x-x/2-1)+"\n"
		return prefix+result+"\n"

	def select(self,words):
		return self.__class__( self.__tasks if len(words)==0 else \
			[task for task in self.__tasks if all(word in task for word in words)] )

exports["TaskGroup"] = TaskGroup