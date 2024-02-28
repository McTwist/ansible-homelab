
from copy import deepcopy

class FilterModule:
	def filters(self):
		return {
			'get_php_modules': self.get_php_modules,
			'diff_config': self.diff_config,
		}
	def get_php_modules(self, config : list[dict], default=None):
		# - php: version
		#   modules:
		#   - module
		default = [] if default is None else default
		modules = list(set(f"php{site['version']}-{module}" for site in config for module in site["modules"] + default))
		return modules

	def diff_config(self, config : list[dict], remove : list[dict], fields : list[str]):
		config = deepcopy(config)
		removed = []
		for i, a in enumerate(config):
			for b in remove:
				if all(field in a and field in b and a[field] == b[field] for field in fields):
					removed.append(i)
		for i in reversed(removed):
			del config[i]
		return config

# Tests
if __name__ == "__main__":
	import json
	a = FilterModule().diff_config(
		[
			dict(a="a", b="b", c="c"),
			dict(a="b", b="a"),
			dict(a="c", b="c", c="c"),
			dict(a="a", b="c")
		],
		[
			dict(a="a", b="b"),
			dict(a="a", b="c")
		],
		["a", "b"])
	print(json.dumps(a, indent=" "*4))
