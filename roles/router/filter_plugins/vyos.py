

def listify(config):
	if isinstance(config, dict):
		return [[k] + c for k, v in config.items() for c in listify(v)]
	elif isinstance(config, list):
		return [c for v in config for c in listify(v)]
	else:
		return [[config]]

class FilterModule:
	def filters(self):
		return {
			'vyos_stringify': self.stringify,
			'vyos_api': self.api,
			'vyos_api_list': self.api_list,
		}
	def stringify(self, config):
		def safe_str(s):
			s = str(s)
			return "'{}'".format(s) if " " in s else s
		return [" ".join(safe_str(c) for c in cmd) for cmd in listify(config)]
	def api(self, config, op : str, arg : str="path"):
		return [{"op": op, arg: l} for l in listify(config)]
	def api_list(self, ll : list, pre: list[str]):
		return [{"op": "set", "path": [*pre, l]} for l in ll]

# Tests
if __name__ == "__main__":
	import yaml
	t = FilterModule()
	with open("test.yml", "r") as f:
		y = yaml.safe_load(f)
		print(t.stringify(y))
		print(t.api(y, "set"))
		print(t.api_set([1, 2, 3, 4, 5], ["a", "b"]))

