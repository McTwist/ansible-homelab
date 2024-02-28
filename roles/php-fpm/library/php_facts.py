#!/usr/bin/env python3

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

from glob import glob
import re
import subprocess

if __name__ == "__main__":
	module = AnsibleModule(
		argument_spec=dict(config=dict()),
		supports_check_mode=True)
	module_args = module.params

	ret = dict(ansible_facts={})

	reg = re.compile(r'^/etc/php/([0-9\.]+)/fpm/pool\.d/([^/]+)\.conf$')
	paths = glob('/etc/php/*/fpm/pool.d/*.conf')

	domains = dict()
	for path in paths:
		m = reg.match(path)
		if m is None:
			continue
		php, domain = m.group(1, 2)
		domains[f'{domain}-{php}'] = {
			"name": domain,
			"version": float(php)
		}

	ret['ansible_facts']['php_config'] = list(domains.values())

	module.exit_json(**ret)
	
