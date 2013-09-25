
require date

periodic = { # function arguments: datetime.date instance
	"everyday": lambda date: True,
	"weekdays": lambda date: date.weekday()<5,
	"weekends": lambda date: date.weekday()>4,
}
for index,name in enumerate("monday tuesday wednesday thursday friday saturday sunday".split()):
	periodic[name] = (lambda x: lambda date: date.weekday()==x)(index)

status = "failed impossible done".split()

prefix = "+"
prefixlen = len(prefix)
tagequal = "="

def istagstr(str): return len(str)>0 and len(str.split())==1
def istag(tag): return tag.startswith(prefix) and istagstr(tag[prefixlen:])

# end of tag related declarations

class Task:

	def __init__(self,raw,group,date):
		self.__date = date
		self.group = group
		self.update(raw)

	def update(self,raw):
		self.__raw = []
		self.__tags = {}

		for word in raw.split():
			if not istag(word):
				self.__raw.append(word)
			else:
				tag = word.lower()[prefixlen:]
				index = tag.find(tagequal)
				if index==-1:
					name = tag
					value = None
				else:
					name = tag[:index]
					value = tag[index+1:]
				start = prefix+name+(value or "")
				if name in self.__tags:
					continue
				elif name=="deadline" or name=="birthday":
					if value=="none":
						self.__raw.append(prefix+name+tagequal+value)
						self.__tags[name] = value
						continue
					value = self.__date.translate(value)
					if value:
						self.__raw.append(prefix+name+tagequal+value)
						self.__tags[name] = value
				else:
					self.__raw.append(prefix+name+(tagequal+value if value else ""))
					self.__tags[name] = value

		self.__raw = " ".join(self.__raw)

	def __eq__(self,other): return isinstance(other,self.__class__) and self.__raw==other.__raw
	def __ne__(self,other): return not self.__eq__(other)
	def __hash__(self): return self.__raw.__hash__()
	def __repr__(self): return self.__raw
	def __contains__(self,word):
		suffix = "" if len(filter(lambda tag: tag in status, self.__tags))!=0 \
			else " "+prefix+"pending"
		return isinstance(word,str) and word.lower() in self.__raw.lower()+suffix

	def raw(self): return self.__raw

	table_heading = "Date Task Tags Periodicity Deadline Status".title().split()

	def table_fields(self):
		groupname = self.group.name if self.group else ""
		text = " ".join(word for word in self.__raw.split() if not istag(word))
		tags = ", ".join(tag+":"+self.__tags[tag] if self.__tags[tag] else tag \
			for tag in self.__tags \
			if tag not in status and tag not in periodic and tag!="deadline")
		freq = ", ".join([tag for tag in self.__tags if tag in periodic])
		deadline = "deadline" in self.__tags and self.__tags["deadline"]
		deadline = "No Limit" if deadline=="none" else (deadline or "")
		stat = self.status().title()
		return [groupname, text, tags, freq, deadline, stat]

	sg = "longterm birthdays periodic".split() # special group names

	def tag_add(self,tag):
		if istagstr(tag) and tag not in self.__tags:
			self.update( " ".join(self.__raw.split()+[prefix+tag]) )
			return True
		return False

	def tag_check(self,tag):
		return tag in self.__tags

	def tag_remove(self,tag):
		if istagstr(tag) and tag in self.__tags:
			tag = prefix + tag # eliminates recomputation
			temp = [i for i in self.__raw.split() if i!=tag]
			self.update( " ".join(temp) )
			return True
		return False

	def status(self):
		result = next((tag for tag in self.__tags if tag in status),None)
		if result: return result
		deadline = "deadline" in self.__tags and self.__tags["deadline"]
		if deadline: deadline = deadline!="none" and Date.deconvert(deadline)
		else: deadline = self.group and Date.regexp.match(self.group.name) and Date.deconvert(self.group.name)
		if not deadline or self.__date.date<=deadline: return "pending"
		return "failed"

	def report(self):
		x = self.status()
		return (int(x=="done"),int(x!="impossible"))

	def carryover(self):
		if any(i in status for i in self.__tags): return
		deadline = "deadline" in self.__tags and self.__tags["deadline"]
		if deadline and Date.regexp.match(deadline) \
			and self.__date.date<Date.deconvert(deadline) or deadline=="none":
			return True

	def __nostatus(self,tags={}):
		temp = []
		for word in self.__raw.split():
			if not istag(word): temp.append(word)
			else:
				index = word.find(tagequal)
				if index==-1: tag = word[prefixlen:]
				else: tag = word[prefixlen:index]
				if tag in status: pass
				elif tag in tags and index!=-1:
					temp.append(prefix+tag+tagequal+tags[tag])
				else: temp.append(word)
		for tag in tags:
			if tag not in self.__tags:
				temp.append(prefix+tag+(tagequal+tags[tag] if tags[tag] else ""))
		return " ".join(temp)

	def periodic(self,group):
		if not self.group or self.group.name!="periodic": return
		tags = filter(lambda tag: tag in periodic, self.__tags)
		if not any(periodic[name](self.__date.date) for name in tags): return
		return self.__class__( self.__nostatus(), group, self.__date )

	def birthday(self,group):
		if "birthday" not in self.__tags: return
		d1, d2 = self.__date.date, Date.deconvert(self.__tags["birthday"])
		if (d1.month, d1.day)!=(d2.month, d2.day): return
		return self.__class__( self.__nostatus({"deadline":"none"}), group, self.__date )

exports["Task"] = Task