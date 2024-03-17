from monitor import Monitor
class Plugin(Monitor):
    def get_data(self):
        loadavg = self.read('rootfs','/proc/loadavg')
        cpuinfo = self.read('rootfs','/proc/cpuinfo')
        for core in cpuinfo:
            cpu_count = int(core['siblings'])
            break
        for config in loadavg:
            current = config["line_0"][0]
            self.data['current_load'] = round(float(current)/cpu_count*100)
            self.data['current_load'].set_unit("%")
            self.data['1_minute_load'] = current
            self.data['5_minutes_load'] = config["line_0"][1]
            self.data['15_minutes_load'] = config["line_0"][2]
            self.data['running_processes'],self.data['total_processes']  = config["line_0"][3].split("/")
        return self.data