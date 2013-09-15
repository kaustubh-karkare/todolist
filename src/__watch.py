
import collections, pyinotify, threading

def debounce(wait,collect=False):
	def decorator(fn):
		def debounced(*_args, **_kwargs):
			# javascript/arguments.caller
			self = debounced
			# cancel waiting thread
			if self.lock: self.thread.join()
			else: self.thread.cancel()
			# collect function arguments
			if not collect: self.args, self.kwargs = _args, _kwargs
			else: self.args.extend(_args), self.kwargs.update(_kwargs)
			# define and launch thread
			def wrapper():
				self.lock = True
				fn(*self.args, **self.kwargs)
				self.args, self.kwargs = [], {}
				self.lock = False
			self.thread = threading.Timer(wait, wrapper)
			self.thread.start()
		# initialize thread, lock & argument collections
		debounced.thread = threading.Timer(0, debounced)
		debounced.lock = False
		if collect: debounced.args, debounced.kwargs = [], {}
		return debounced
	return decorator

eventmap = {
	"create": "IN_CREATE",
	"modify": "IN_MODIFY",
	"delete": "IN_DELETE",
}

def start(path,events,handler):

	mask = reduce( (lambda x,y: x|y), (getattr(pyinotify,eventmap[i]) for i in events) )

	event = collections.namedtuple("event",["type","path"])
	def wrapper(e):
		etype = next((i for i,j in eventmap.items() if j==e.maskname),"unknown")
		return handler(event(etype,e.pathname))

	wm = pyinotify.WatchManager()
	notifier = pyinotify.Notifier(wm, wrapper)
	wm.add_watch(path, mask, rec=True)
	notifier.loop()
