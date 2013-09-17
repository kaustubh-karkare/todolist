
import prettytable
require task

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

	def tabulate(self,heading=None,index=False):
		fields = (["Index"] if index else [])+Task.table_heading
		table = prettytable.PrettyTable(fields, padding_width=1)
		for i in fields: table.align[i] = "l"
		for i, task in enumerate(self.task_list()):
			table.add_row( ([i] if index else [])+task.table_fields() )
		table, prefix = table.get_string(), ""
		if heading:
			x = table.find("\n")-len(heading)
			prefix = "="*(x/2-1)+" "+heading+" "+"="*(x-x/2-1)+"\n"
		return prefix+table+"\n"

	def select(self,words):
		return self.__class__( self.__tasks if len(words)==0 else \
			[task for task in self.__tasks if all(word in task for word in words)] )

exports["TaskGroup"] = TaskGroup