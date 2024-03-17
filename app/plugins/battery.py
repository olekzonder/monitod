from monitor import Monitor
class Plugin(Monitor):
    def get_data(self):
        try:
            info = self.read('rootfs', '/sys/class/power_supply/BAT*')
        except:
            self.data['error'] = "No battery detected"
            return self.data
        n = 0
        for battery in info:
            if f"bat{n}" not in self.data:
                self.data.append(f"bat{n}")
            self.data[f"bat{n}"]['manufacturer'] = battery['manufacturer']
            self.data[f"bat{n}"]['model_name'] = battery['model_name']
            self.data[f"bat{n}"]['charge'] = battery['capacity']
            self.data[f"bat{n}"]['charge'].set_unit("%")
            self.data[f"bat{n}"]['capacity'] = int(battery['energy_now'])//1000
            self.data[f"bat{n}"]['capacity'].set_unit("mWh")
            self.data[f"bat{n}"]['cycle_count'] = battery['cycle_count']
            self.data[f"bat{n}"]['designed_full_capacity'] = int(battery['energy_full_design'])//1000
            self.data[f"bat{n}"]['designed_full_capacity'].set_unit("mWh")
            self.data[f"bat{n}"]['current_full_capacity'] = int(battery['energy_full'])//1000
            self.data[f"bat{n}"]['current_full_capacity'].set_unit("mWh")
            self.data[f"bat{n}"]['wear'] = round((1 - (int(battery['energy_full'])//1000)/(int(battery['energy_full_design'])//1000))*100,1)
            self.data[f"bat{n}"]['wear'].set_unit("%")
            n+=1
        return self.data
