from ipaddress import ip_address

class FilterModule:
	def filters(self):
		return {
			'to_arpa': self.arpa
		}
	def arpa(self, ip):
		return ip_address(ip).reverse_pointer

# Tests
if __name__ == "__main__":
	f = FilterModule()
	print(f.arpa("1.2.3.4"))
	print(f.arpa("1::f"))

