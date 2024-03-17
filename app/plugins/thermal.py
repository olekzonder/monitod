from monitor import Monitor
class Plugin(Monitor):
    def get_data(self):
        hwmons = self.read('rootfs','/sys/class/hwmon/hwmon*')
        for hwmon in hwmons:
            n = 1
            if not hwmon.find('temp'):
                continue
            name = hwmon['name']
            if name not in self.data:
                self.data.append(name)
            while True:
                labeled = False
                zone = f'temp{n}'
                if f'{zone}_label' in hwmon:
                    label = hwmon[f'{zone}_label'].lower().replace(' ','_')
                    if label not in self.data[name]:
                        self.data[name].append(label)
                    labeled = True
                if f'{zone}_input' in hwmon:
                    current = hwmon[f'{zone}_input']
                    if labeled:
                        if current == 'N/A':
                            self.data[name][label]['current'] = 'N/A'
                        else:
                            self.data[name][label]['current'] = float(current)/1000
                            self.data[name][label]['current'].set_unit('°C')
                    else:
                        if current == 'N/A':
                            self.data[name][f'{zone}'] = 'N/A'  
                        else:
                            self.data[name][f'{zone}'] = float(current)/1000
                            self.data[name][f'{zone}'].set_unit('°C')
                else:
                    break
                thresholds = ['min','max','crit','crit_alarm']
                for threshold in thresholds:
                    th = f'{zone}_{threshold}'
                    if th in hwmon:
                        if hwmon[th] == 'N/A' or hwmon[th] == '0':
                            continue
                        if labeled:
                            self.data[name][label][threshold] = float(hwmon[th])/1000
                            self.data[name][label][threshold].set_unit('°C')
                        else:
                            self.data[name][threshold] = float(hwmon[th])/1000
                            self.data[name][threshold].set_unit('°C')
                n += 1
        return self.data