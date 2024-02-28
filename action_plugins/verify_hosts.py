

__metaclass__ = type

from ansible.plugins.action import ActionBase

from itertools import product
import json
import re

def retrieve_values(tree : dict, path : str) -> list:
	path = path.split(".")
	tree = [tree]
	for p in path:
		n = []
		addn = lambda a: n.extend(a) if isinstance(a, list) else n.append(a)
		for t in tree:
			# wildcard: all fields
			if p == '*':
				for tt in t.values():
					addn(tt)
			# found field
			elif p in t:
				addn(t[p])
		tree = n
	return tree

def fail(ret : dict, msg : str):
	ret["failed"] = True
	ret["msg"] = msg
	return ret

class ActionModule(ActionBase):
	def run(self, tmp=None, task_vars=None):
		# task_vars: all variables for a task, including playbook variables
		# module_args: arguments for the module itself
		super(ActionModule, self).run(tmp, task_vars)
		module_args = self._task.args.copy()
		check_mode = self._play_context.check_mode

		hostvars = task_vars["hostvars"]

		ret = dict(changed=False)

		unique_names = module_args.get("unique_value", [])
		if isinstance(unique_names, str):
			unique_names = [unique_names]
		if not isinstance(unique_names, list):
			return fail(ret, "unique_value needs to be a list of strings or a string")
		unique_values = {name: dict() for name in unique_names}

		# Verify unique values
		for (lh, v), (name, un) in product(hostvars.items(), unique_values.items()):
			for lv in retrieve_values(v, name):
				lv = json.dumps(lv)
				if lv in un:
					rh = un[lv]
					return fail(ret, f"{rh} and {lh} shares same value from {name}")
				else:
					un[lv] = lh

		value_regex = module_args.get("value_format", dict())
		if not isinstance(value_regex, dict):
			return fail(ret, "value_format needs to be a dictionary")
		value_regexes = {name: re.compile(reg) for name, reg in value_regex.items()}

		# Verify regular expression compliance
		for (lh, v), (name, reg) in product(hostvars.items(), value_regexes.items()):
			for lv in retrieve_values(v, name):
				if reg.match(str(lv)) is None:
					return fail(ret, f"{lh}.{name} has invalid format")

		return ret

if __name__ == "__main__":
	import json
	tree = dict(
		a=3,
		b=dict(c=1),
		d=[
			dict(e=4, f=8),
			dict(e=5, g=7)
		],
		h=dict(
			i=dict(j=9, l=0),
			k=dict(j=2, l=0),
			m=dict(l=0)
		))
	assert retrieve_values(tree, "a") == [3]
	assert retrieve_values(tree, "b.c") == [1]
	assert retrieve_values(tree, "d.e") == [4, 5]
	assert retrieve_values(tree, "d.*") == [4, 8, 5, 7]
	assert retrieve_values(tree, "h.*.j") == [9, 2]
