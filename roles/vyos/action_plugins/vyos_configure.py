
__metaclass__ = type

from ansible.plugins.action import ActionBase
from ansible.module_utils.common.dict_transformations import recursive_diff
from ansible.utils.display import Display
import json

display = Display()

def _fail(ret, msg):
	ret['failed'] = True
	ret['msg'] = msg
	return ret

def convert_str(config):
	if isinstance(config, list):
		return [convert_str(v) for v in config]
	elif isinstance(config, dict):
		return {str(k): convert_str(v) for k, v in config.items()}
	else:
		return str(config)

# TODO: Make use of recursive_diff instead
def adiff(a, b, path=[]):
	if b is None:
		return a
	if a is None:
		return None
	if not isinstance(a, type(b)):
		raise TypeError(type(a).__name__, type(b).__name__, path)
	if isinstance(a, list):
		r = []
		for aa in a:
			for bb in b:
				rr = adiff(aa, bb, path)
				if rr is None:
					break
			else:
				# TODO: Fix difference on unknown
				r.append(aa)
		return r
	elif isinstance(a, dict):
		r = {}
		for k, v in a.items():
			if k in b:
				rr = adiff(v, b[k], path + [k])
				if rr:
					r[k] = rr
			else:
				r[k] = v
		return r
	elif a != b:
		return a
	return None

def listify(config):
	if isinstance(config, dict):
		return [[k] + c for k, v in config.items() for c in listify(v)]
	elif isinstance(config, list):
		return [c for v in config for c in listify(v)]
	else:
		return [[config]]

# Create api-like structure
def create_api(op: str, pre: list[str], config: dict) -> list[dict]:
	return [{"op": op, "path": pre + cmd} for cmd in listify(config)]

def create_api_delete(pre: list, prev: dict, delete: dict) -> list[dict]:
	kept = adiff(prev, delete)
	def remove_path(kept1, delete1, path: list):
		cmd = []
		if isinstance(delete1, list):
			for v in delete1:
				for vv in kept1:
					rr = remove_path(v, vv)
					if rr:
						cmd.extend(rr)
						break
				else:
					cmd.append(path)
		elif isinstance(delete1, dict):
			for k, v in delete1.items():
				if k in kept1:
					cmd.extend(remove_path(kept1[k], v, path + [k]))
				else:
					cmd.append(path + [k])
		elif kept1 != delete1:
			cmd.append(path + [delete1])
		return cmd
	return [{"op": "delete", "path": pre + path} for path in remove_path(kept, delete, [])]

# Create cli-like structure
# TODO: Make use of create_api to generate lists
def create_cli(op: str, pre: list[str], config: dict) -> str:
	def safe_str(s):
		s = str(s)
		return "'{}'".format(s) if " " in s else s
	return "\n".join([" ".join(safe_str(c) for c in [op] + pre + cmd) for cmd in listify(config)])

class ActionModule(ActionBase):
	def run(self, tmp=None, task_vars=None):
		# task_vars: all variables for a task, including playbook variables
		# module_args: arguments for the module itself
		super(ActionModule, self).run(tmp, task_vars)
		module_args = self._task.args.copy()
		check_mode = self._play_context.check_mode
		diff_mode = self._task.diff

		hostvars = task_vars['hostvars']

		ret = dict(changed=False)

		path = module_args.get('path', "").split()
		state = module_args.get('state', "replaced")
		if state not in ["replaced", "merged", "subtracted"]:
			return _fail(ret, f"'{state}' is not valid")

		vyos_api = self._shared_loader_obj.action_loader.get("vyos_api", self._task, self._connection,
			self._play_context, self._loader, self._templar, self._shared_loader_obj)

		self._task.args['method'] = 'retrieve'
		self._task.args['data'] = json.dumps(dict(
			op='showConfig',
			path=path))

		# Disable temporary as it will not modify anything anyway
		self._play_context.check_mode = False
		retrieve_ret = vyos_api.run(tmp, task_vars)
		self._play_context.check_mode = check_mode

		if 'failed' in retrieve_ret and retrieve_ret['failed']:
			# Handle empty config
			if "empty" in retrieve_ret['msg']:
				retrieve_ret['response'] = None
			else:
				return _fail(ret, retrieve_ret['msg'])

		current = retrieve_ret['response']

		# Get rid of Ansible unicodes
		data = convert_str(json.loads(json.dumps(module_args['data'])))

		delete_conf = None
		set_conf = None

		match state:
			case "replaced":
				delete_conf = adiff(current, data)
				set_conf = adiff(data, current)
				# TODO: Verify the differences
				"""dif = recursive_diff(current, data)
				if dif:
					dif2 = (adiff(dif[0], delete_conf), adiff(delete_conf, dif[0]),
						adiff(dif[1], set_conf), adiff(set_conf, dif[1]))
					if any(dif2):
						ret['data'] = data
						ret['current'] = current
						ret['delete'] = delete_conf
						ret['set'] = set_conf
						ret['dif0'] = dif[0]
						ret['dif1'] = dif[1]
						ret['d0'] = dif2[0]
						ret['0d'] = dif2[1]
						ret['s1'] = dif2[2]
						ret['1s'] = dif2[3]
						return _fail(ret, "Invalid difference, revise implementation")"""
			# NOTE: These two will not work with --diff, disable it for now
			case "merged":
				self._task.diff = False
				set_conf = adiff(data, current)
			case "subtracted":
				self._task.diff = False
				delete_conf = data

		ops = []
		if delete_conf:
			ops.extend(create_api_delete(path, current, delete_conf))
		if set_conf:
			ops.extend(create_api("set", path, set_conf))
		if ops:
			ret['cmds'] = ops
			if not check_mode:
				self._task.args['method'] = 'configure'
				self._task.args['data'] = json.dumps(ops)
				update_ret = vyos_api.run(tmp, task_vars)
				if 'failed' in update_ret and update_ret['failed']:
					return _fail(ret, update_ret['msg'])

		ret['changed'] = delete_conf or set_conf
		if diff_mode and ret['changed']:
			ret['diff'] = [
				dict(
					before=current,
					after=data
				)
			]

		return ret
