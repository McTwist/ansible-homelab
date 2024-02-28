
from copy import deepcopy
from itertools import product

def retrieve_value(tree : dict, path : str):
	"""
	Retrieve value in dictionary from path
	"""
	path = path.split('.')
	for p in path:
		if p in tree:
			tree = tree[p]
		else:
			return None
	return tree

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

class FilterModule:
	def filters(self):
		return {
			'flatten_dict': self.flatten_dict,
		}
	def flatten_dict(self, config : list[dict], to : str, fields : list[str]):
		"""
		Flatten a dict by traversing into a child and apply all parent fields
		"""
		config = deepcopy(config)

		ret = []
		for conf in config:
			node = retrieve_value(conf, to)
			if node is None:
				node = dict()
			elif not isinstance(node, dict):
				continue
			for field in fields:
				value = retrieve_value(conf, field)
				if value is not None:
					node[field.rsplit('.', 1)[-1]] = value
			ret.append(node)
		return ret
	def flatten_dicts(self, config : list[dict], to : str, fields : list[str]):
		"""
		Flatten dicts by traversing into a child and apply all parent fields
		Note: Not tested
		"""
		config = deepcopy(config)

		ret = []
		for conf in config:
			node = retrieve_values(conf, to)
			if node is None:
				node = dict()
			elif not isinstance(node, dict):
				continue
			for field in fields:
				value = retrieve_value(conf, field)
				if value is not None:
					node[field.rsplit('.', 1)[-1]] = value
			ret.append(node)
		return ret

# Tests
if __name__ == "__main__":
	pass
