from monitor import Monitor
class Plugin(Monitor):
    def get_data(self):
        meminfo = self.read('rootfs','/proc/meminfo')
        for mem in meminfo:
            total = round(int(mem['MemTotal'].split()[0])/1024)
            free = round(int(mem['MemFree'].split()[0])/1024)
            available = round(int(mem['MemAvailable'].split()[0])/1024)
            cached = round(int(mem['Cached'].split()[0])/1024)
            buffers = round(int(mem['Buffers'].split()[0])/1024)
            used = total - free - buffers - cached
            self.data["total"] = total
            self.data["free"] = free
            self.data["available"] = available
            self.data["used"] = used
            self.data["cached"] = cached
            self.data["buffers"] = buffers
        for unit in self.data:
            unit.set_unit("MiB")
        return self.data