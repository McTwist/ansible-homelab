
from copy import deepcopy

class FilterModule:
	def filters(self):
		return {
			'vyos_firewall': self.firewall,
			'vyos_nat': self.nat,
			'vyos_dhcp': self.dhcp,
			'vyos_nat_combine': self.nat_combine,
		}
	def firewall(self, config: dict) -> dict:
		ret = {}
		if 'groups' in config:
			groups = config['groups']['group']
			group = dict()
			ret['group'] = group
			if 'address_group' in groups:
				for address_group in groups['address_group']:
					if 'afi' in address_group and address_group['afi'] == 'ipv6':
						if 'ipv6-address-group' not in group:
							group['ipv6-address-group'] = dict()
						gro = group['ipv6-address-group']
					else:
						if 'address-group' not in group:
							group['address-group'] = dict()
						gro = group['address-group']
					gro[address_group['name']] = dict(
						description=address_group['description'])
					if 'members' in address_group:
						if len(address_group['members']) == 1:
							members = address_group['members'][0]['address']
						else:
							members = []
							for member in address_group['members']:
								members.append(member['address'])
						gro[address_group['name']]['address'] = members
			if 'network_group' in groups:
				for network_group in groups['network_group']:
					if 'afi' in network_group and network_group['afi'] == 'ipv6':
						if 'ipv6-network-group' not in group:
							group['ipv6-network-group'] = dict()
						gro = group['ipv6-network-group']
					else:
						if 'network-group' not in group:
							group['network-group'] = dict()
						gro = group['network-group']
					gro[network_group['name']] = dict(
						description=network_group['description'])
					if 'members' in network_group:
						if len(network_group['members']) == 1:
							members = network_group['members'][0]['address']
						else:
							members = []
							for member in network_group['members']:
								members.append(member['address'])
						gro[network_group['name']]['address'] = members
		if 'rules' in config:
			for rule_set in config['rules']:
				if rule_set['afi'] == 'ipv4':
					if 'name' not in ret:
						ret['name'] = dict()
					names = ret['name']
				elif rule_set['afi'] == 'ipv6':
					if 'ipv6-name' not in ret:
						ret['ipv6-name'] = dict()
					names = ret['ipv6-name']
				for rule in rule_set['rule_sets']:
					name = names[rule['name']] = dict()
					name['description'] = rule['description']
					name['default-action'] = rule['default_action']
					rul = dict()
					for old_rule in rule['rules'] or []:
						new_rule = dict()
						rul[old_rule['number']] = new_rule
						new_rule['action'] = old_rule['action']
						for gr, v in old_rule.items():
							if gr in ['source', 'destination']:
								gro = dict()
								new_rule[gr] = dict(group=gro)
								if 'address_group' in v['group']:
									gro['address-group'] = v['group']['address_group']
								if 'network_group' in v['group']:
									gro['network-group'] = v['group']['network_group']
							elif gr == 'state':
								if v['new']:
									new_rule['state'] = dict(new='enable')
					if rul:
						name['rule'] = rul
		if 'interfaces' in config:
			ret['interface'] = dict()
			for inter in config['interfaces']:
				ret['interface'] = ret['interface'] | inter
		return ret
	def nat(self, config: dict, inbound_interface : str) -> dict:
		"""
		Prepare nat config
		Do not care about validation for certain fields
		"""
		ret = {}
		if 'destination' in config:
			rules = dict()
			ret['destination'] = dict(rule=rules)
			index = 1
			for destination in config['destination']:
				# destination -> inbound
				rule = {
					'protocol': destination['protocol'],
					'inbound-interface': inbound_interface,
					'destination': dict(port=destination['destination']),
					'translation': dict(address=destination['address'])
				}
				if 'description' in destination:
					rule['description'] = destination['description']
				if 'translation' in destination:
					rule['translation']['port'] = destination['translation']
				rules[index] = rule
				index += 1
		if 'source' in config:
			rules = dict()
			ret['source'] = dict(rule=rules)
			index = 1
			for source in config['source']:
				# source -> outbound
				rules[index] = deepcopy(source)
				index += 1
		if 'static' in config:
			rules = dict()
			ret['static'] = dict(rule=rules)
			index = 1
			for static in config['static']:
				# less fields
				rules[index] = deepcopy(static)
				index += 1
		return ret
	def dhcp(self, config: list, hostvars: dict) -> dict:
		"""
		Prepare dhcp config
		"""
		shared = dict()
		ret = {'shared-network-name': shared}
		for conf in config:
			subnets = dict()
			server = dict(
				authoritative={},
				subnet=subnets)
			shared[conf['name']] = server
			if 'domain-name' in conf:
				server['domain-name'] = conf['domain-name']
			if 'domain-search' in conf:
				if not isinstance(conf['domain-search'], list):
					conf['domain-search'] = [conf['domain-search']]
				server['domain-search'] = [search for search in conf['domain-search']]
			if 'name-servers' in conf:
				server['name-server'] = [ns for ns in conf['name-servers']]
			for subnet in conf['subnets']:
				ran = dict()
				static = dict()
				sub = dict()
				subnets[subnet['prefix']] = {
					'default-router': subnet['default-router'],
					'range': ran,
					'static-mapping': static
				}
				index = 1
				for rang in subnet['range']:
					ran[index] = dict(
						start=rang['start'],
						stop=rang['stop'])
					index += 1
				for hostname, host in hostvars.items():
					if 'dhcp_mac' in host and 'dhcp_ipv4' in host:
						static[hostname] = {
							'mac-address': host['dhcp_mac'],
							'ip-address': host['dhcp_ipv4']
						}
		return ret
	def nat_combine(self, config : list[dict]):
		"""
		Combine dhcp_ipv4 into each nat item.
		VERY SPECIFIC, NONPORTABLE
		"""
		config = deepcopy(config)
		ret = []
		for conf in config:
			for rule in conf['nat']:
				rule['address'] = conf['dhcp_ipv4']
				ret.append(rule)
		return ret

# Tests
if __name__ == "__main__":
	pass
