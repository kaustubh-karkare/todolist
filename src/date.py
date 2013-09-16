
import datetime, re

class Date:

	relative = {
		"yesterday": -1,
		"today": 0,
		"tomorrow": 1,
	}

	regexp = re.compile("\d{4}-\d{2}-\d{2}")
	oneday = datetime.timedelta(1)

	def __init__(self,today=None):

		self.date = datetime.date.today()
		self.__relative = {}

		if today is None:
			pass
		elif today in self.relative:
			self.date += self.relative[today]*self.oneday
		elif self.regexp.match(today):
			self.date = self.deconvert(today)

		self.today = self.convert(self.date)

		for word in self.relative:
			temp = self.date + self.relative[word] * self.oneday
			self.__relative[word] = self.convert(temp)

	def translate(self,word):
		# Convert from string to string.
		if word in self.__relative: return self.__relative[word]
		elif self.regexp.match(word): return word

	@staticmethod
	def convert(obj):
		# Convert from date to string.
		return obj.strftime("%Y-%m-%d")

	@staticmethod
	def deconvert(word):
		# Convert from string to date.
		return datetime.date(*map(int,word.split("-")))

	@staticmethod
	def weekdiff(d1,d2):
		m1 = d1 - datetime.timedelta(days=d1.weekday())
		m2 = d2 - datetime.timedelta(days=d2.weekday())
		return (m2-m1).days/7

	@staticmethod
	def monthdiff(d1,d2):
		return (d2.year*12+d2.month)-(d1.year*12+d1.month)

exports["Date"] = Date