from monitor import Monitor
class Plugin(Monitor):
    def get_data(self):
        cpuinfo = self.read('rootfs','/proc/cpuinfo')
        for core in cpuinfo:
            self.data['vendor'] = core['vendor_id']
            self.data['model'] = core['model name']
            self.data['cores'] = core['cpu cores']
            self.data['threads'] = core['siblings']
            self.data['address_sizes'] = core['address sizes']
            # self.data['features'] = core['flags'].upper()
            if 'frequency' not in self.data:
                    self.data.append('frequency')
            self.data['frequency'][f"processor_{core['processor']}"] =  core['cpu MHz']
            self.data['frequency'][f"processor_{core['processor']}"].set_unit("MHz")
        cache_dirs = self.read('rootfs', '/sys/devices/system/cpu/cpu*/cache/index*')
        if 'cache' not in self.data:
            self.data.append('cache')
        instances = {}
        for cache in cache_dirs:
            if cache['level'] == '1':
                if cache['type'] == 'Data':
                    cache_name = 'l1d'
                elif cache['type'] == 'Instruction':
                    cache_name = 'l1i'
                else:
                    cache_name = 'l1'
            else:
                    cache_name = f"l{cache['level']}"
            if not cache_name in instances.keys():
                instances[cache_name] = {}
                instances[cache_name]['shared'] = []
            instances[cache_name]['shared'].append(cache['shared_cpu_list'])
            instances[cache_name]['size'] = int(cache['size'][:-1])
        for key in instances.keys():
            instances[key]['shared'] = len(list(set(instances[key]['shared'])))
            self.data['cache'][key] = instances[key]['size'] * instances[key]['shared']
            self.data['cache'][key].set_unit("kB")
        bug_dirs = self.read('rootfs','/sys/devices/system/cpu/vulnerabilities')
        if 'bugs' not in self.data:
            self.data.append('bugs')
        for config in bug_dirs:
            for bug in config:
                bug_name = bug.name
                self.data['bugs'][bug_name] = bug.value
        return self.data