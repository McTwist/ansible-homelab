
from copy import deepcopy

class FilterModule:
	def filters(self):
		return {
			'chunks': self.chunks,
		}
	def chunks(self, config : list, count : int = 1):
		for i in range(0, len(config), count):
			yield config[i:i+count]

# Tests
if __name__ == "__main__":
	pass
