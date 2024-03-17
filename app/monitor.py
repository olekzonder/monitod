import os, glob, importlib, shutil, importlib.util, subprocess, concurrent.futures
from exceptions import NoExporterError, ModuleNotActivatedError, MissingFilterSettingsError
class Monitor:
    def __init__(self, name):
        self.name = name
        self.data = Group(name)
        self.static = False
    def static_plugin(self):
        self.static = True
    def read(self, type, arg, output_format=None):
        match(type):
            case 'rootfs':
                return RootFSExporter(arg).read()
            case 'logs':
                return LogExporter(arg).read()
            case 'systemd':
                return SystemdExporter(arg).read()
            case 'command':
                return CommandExporter(arg, output_format).read()
            case 'process':
                return ProcessExporter(arg).read()
            case other:
                raise NoExporterError()
    def to_dict(self):
        return self.data.to_dict()

    def include(self,items):
        for item in items:
            if item not in self.data:
                raise ValueError(f"Category {item} was not found in {self.name}")
        self.data = Group(self.name)
        self.data.extend([item for item in self.get_data() if item.name in items])
        return self.data

    def exclude(self,items):
        for item in items:
            if item not in self.data:
                raise ValueError(f"Category {item} was not found in {self.name}")
        self.data = Group(self.name)
        self.data.extend([item for item in self.get_data() if item.name not in items])
        return self.data

class Value:
    def __init__(self,name,value,unit='',prefix=''):
        self.name = name
        self.prefix = f'{prefix}.{self.name}'
        self.value = value
        self.unit = unit

    def set_unit(self,unit):
        self.unit = unit

    def __str__(self):
        return f"{self.name.replace('_', ' ').title()}: {self.value} {self.unit}"

    def to_dict(self):
        if self.unit == '':
            return {
                "value": self.value
            }
        else:
            return {
                "value": self.value,
                "unit": self.unit
            }

    def get_conditions(self):
        return {self.prefix: {'value': self.value, 'unit': self.unit}}

class Group:
    def __init__(self,name,prefix=''):
        self.name = name
        self.prefix = f"{prefix}.{self.name}" if prefix != '' else self.name
        self.items = []
    def append(self, name):
        self.items.append(Group(name,prefix=self.prefix))

    def to_dict(self):
        result = {}
        for item in self.items:
            result[item.name] = item.to_dict()
        return result

    def get_conditions(self):
        result = {}
        for item in self.items:
            result.update(item.get_conditions())
        return result

    def extend(self,items):
        self.items = items

    def _sort(self):
        self.items = sorted(self.items, key=lambda x: (isinstance(x, Value), isinstance(x, Group)),reverse=True)

    def __iter__(self):
        yield from self.items

    def __setitem__(self, key, value):
        for item in range(len(self.items)):
            if self.items[item].name == key:
                if isinstance(self.items[item], Group):
                    self.items[item] = value
                    self.items[item].prefix
                    return self._sort()
                else:
                    self.items[item] = Value(key,value,prefix=self.prefix)
                    return self._sort()
        if isinstance(value, Group):
            self.items.append(value)
            return self._sort()
        self.items.append(Value(key,value,prefix=self.prefix))
        return

    def __getitem__(self, key):
        for item in self.items:
            if item.name == key:
                return item
        raise KeyError(key)

    def __contains__(self, name):
        for item in self.items:
            if item.name == name:
                return True
        return False  

    def __str__(self):
        result = []
        result.append(f"{self.name}:")
        for item in self.items:
                result.append(str(item))
        return '\n'.join(result)


class PidParser:
    def __init__(self):
        pass
    def __get_pids(self):
        pids = []
        for entry in os.listdir('/proc'):
            if entry.isdigit():
                self.pids.append(entry)
        return pids
    def read(self):
        pids = self.__get_pids()
        
class RootFSExporter:
    def __init__(self, filename):
        match filename.split('/')[1]:
            case "proc":
                try:
                    self.parser = ProcParser(filename)
                except FileNotFoundError:
                    raise ValueError("File %s not found in procfs")
            case "sys":
                try:
                    self.parser = SysParser(filename)
                except FileNotFoundError:
                    raise ValueError("File %s not found in sysfs"%filename)
            case other:
                raise ValueError("Only procfs and sysfs are supported by this exporter!")
    def read(self):
        return self.parser.read()

class LogExporter:
    def __init__(self):
        raise NotImplementedError
class SystemdExporter:
    def __init__(self):
        raise NotImplementedError
class CommandExporter:
    def __init__(self, arg, output_type):
        match output_type:
            case 'json':
                self.parser = 'json'
            case 'key_value':
                self.parser = 'key_value'
            case 'table':
                self.parser = 'table'
            case other:
                raise KeyError("Incorrect output type")
        self.data = Data()
        self.args = arg.split()
        if not shutil.which(self.args[0]):
            raise ValueError("Command not found")
        self.result = subprocess.run(self.args, shell=False, text=True, capture_output=True).stdout.strip().split('\n')
    def read(self):
        config = Config()
        match self.parser:
            case 'json':
                pass
            case 'key_value':
                for line in self.result:
                    try:
                        name, value = line.rstrip().split(":")
                    except:
                        continue
                    config.append(name.strip(), value.strip())
                self.data.append(config)
            case 'table':
                pass
        return self.data
        
class ProcessExporter:
    def __init__(self):
        raise NotImplementedError

class Item:
    def __init__(self,name,value):
        self.name = name
        self.value = value
    def __str__(self):
         return f"{self.name}: {self.value}"

class Config:
    def __init__(self):
        self.values = []
    def __getitem__(self,name):
        for value in self.values:
            if value.name == name:
                return value.value
        raise KeyError(f"{name}")
    def append(self, name, value):
        self.values.append(Item(name, value))
    def __str__(self):
        return ' '.join([str(value) for value in self.values])
    def __iter__(self):
        yield from self.values
    def __contains__(self, name):
        for item in self.values:
            if item.name == name:
                return True
        return False
    def is_empty(self):
        return not len(self.values)
    def find(self,name):
        result = []
        for value in self.values:
            if value.name[:len(name)] == name:
                result.append(value.name)
        return result

class Data:
    def __init__(self):
        self.configs = []    
    def __iter__(self):
        return iter(self.configs)
    def append(self, config):
        self.configs.append(config)

class SysParser:
    def __init__(self, filename):
        self.paths = sorted(glob.glob(filename))
        self.data = Data()
        if not self.paths:
            raise FileNotFoundError
    def read(self):
        for path in self.paths:
            config = Config()
            dirlist = os.listdir(path)
            for file in dirlist:
                filename = os.path.join(path,file)
                if os.path.isdir(filename):
                    continue
                with open(os.path.join(path,file),"r") as f:
                    try:
                        for line in f:
                            config.append(file,line.rstrip())
                    except OSError:
                        config.append(file,"N/A")
            self.data.append(config)
        return self.data

class ProcParser:
    def __init__(self, filename):
        if not os.path.exists(filename):
            raise FileNotFoundError
        self.data = Data()
        self.path = filename
    def read(self):
        config = Config()
        k = 0
        with open(self.path, "r") as file:
            for line in file:
                if line != '\n':
                    if ':' in line:
                        kv = line.strip().split(":")
                        name, value = kv[0].strip(), kv[1].strip()
                        config.append(name, value)
                    elif '\t' in line:
                        values = line.strip().split("\t")
                        config.append(f"line_{k}",values)
                        k += 1
                    else: 
                        values = line.strip().split()
                        config.append(f'line_{k}', values)
                        k += 1
                else:
                    self.data.append(config)
                    config = Config()
            if not config.is_empty():
                self.data.append(config)
        return self.data

class Plugin:
    def __init__(self,name,module):
        self.name = name
        self.module = module
        self.activated = False
        self.data = None
        self.filter = None
    def activate(self):
        self.module = self.module(self.name)
        self.activated = True
    def _apply_filter(self):
        match self.filter:
            case 'include':
                self.data = self.module.include(self.options)
            case 'exclude':
                self.data = self.module.exclude(self.options)
            case None:
                return
    def set_filter(self, filter, options):
        match filter:
                case 'include':
                    if not options:
                        raise MissingFilterSettingsError()
                    self.filter = 'include'
                    self.options = options
                case 'exclude':
                    if not options:
                        raise MissingFilterSettingsError()
                    self.filter = 'exclude'
                    self.options = options
                case other:
                    raise RuntimeError(f"No such filter: {filter}")
    def read(self):   
        if not self.activated:
            raise ModuleNotActivatedError()
        if self.data != None and self.module.static:
            return self.data
        try:    
            self.data = self.module.get_data()
            self._apply_filter()
        except RuntimeError as e:
            self.data = Group()
            self.data['error'] = str(e)
        return self.data

    def read_conditions(self):
        conditions = self.data.get_conditions()
        return conditions
        
    def get_conditions(self):
        return ' '.join(self.read_conditions().keys())

    def to_dict(self):
        if self.data == None:
            raise RuntimeError("Read data first!")
        return self.data.to_dict()

class PluginImporter:
    def __init__(self,directory = f"{os.path.dirname(os.path.abspath(__file__))}/plugins"):
        self.plugins = []
        self.directory = directory
        self.data = Group('Importer')
        self.conditions = []
        files = [i for i in os.listdir(self.directory) if i[-3:] == '.py']
        for file in files:
            path = os.path.join(self.directory,file)
            name = file[:-3]
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.plugins.append(Plugin(name,module.Plugin))

    def activate_all(self):
        for plugin in self.plugins:
            plugin.activate()
            
    def _read_plugin(self,plugin):
        return plugin.name, plugin.read()

    def read_all(self):
        plugins = [plugin for plugin in self.plugins if plugin.activated]
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(self._read_plugin, plugins)
        for name, data in results:
            self.data[name] = data
        return self.data

    def read_conditions(self):
        self.conditions = {}
        plugins = [plugin for plugin in self.plugins if plugin.activated]
        for plugin in plugins:
            self.conditions.update(plugin.read_conditions())
        return self.conditions
    
    def __contains__(self,name):
        for plugin in self.plugins:
            if plugin.name == name:
                return True
        return False
    def __getitem__(self,name):
        for plugin in self.plugins:
            if plugin.name == name:
                return plugin
        raise KeyError(plugin)
    def __contains__(self,name):
        for plugin in self.plugins:
            if plugin.name == name:
                return True
        return False
    def __iter__(self):
        yield from self.plugins