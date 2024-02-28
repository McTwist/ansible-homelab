
from copy import deepcopy

class FilterModule:
	def filters(self):
		return {
			'nat_combine': self.nat_combine,
		}
	def nat_combine(self, config : list[dict]):
		"""
		Combine dhcp_ipv4 into each nat item.
		VERY SPECIFIC, NONPORTABLE
		"""
		config = deepcopy(config)
		ret = []
		for conf in config:
			for rule in conf['nat']:
				rule['dhcp_ipv4'] = conf['dhcp_ipv4']
				ret.append(rule)
		return ret
