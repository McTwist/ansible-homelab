
from copy import deepcopy

class FilterModule:
	def filters(self):
		return {
			'expand_dict': self.expand_dict,
		}
	def expand_dict(self, config : list, field : str):
		return [{field: conf} for conf in config]

# Tests
if __name__ == "__main__":
	pass
