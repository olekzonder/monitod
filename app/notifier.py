from exceptions import ModuleNotActivatedError
import os, importlib,importlib.util

# classes 
class Rule:
    def __init__(self,name,condition,sign,value):
        self.name = name
        self.condition = condition
        self.sign = sign
        self.active = False
        self.value = float(value)

class Notifier:
    def __init__(self,name):
        self.name = name
        self.options = {}
    def set_options(self,options):
        self.options = options
    def send(self):
        pass

class Plugin:
    def __init__(self,name,module):
        self.name = name
        self.module = module
        self.activated = False
        self.rules = []

    def activate(self):
        self.module = self.module(self.name)
        self.activated = True

    def send(self,message):
        self.module.send(message)
    def set_options(self,options):
        self.module.set_options(options)
    
    def add_rule(self,name,condition,sign,value):
        self.rules.append(Rule(name,condition,sign,value))

    def __iter__(self):
        yield from self.rules

class NotifierImporter:
    def __init__(self,directory = f"{os.path.dirname(os.path.abspath(__file__))}/notifiers"):
            self.plugins = []
            self.directory = directory
            files = [i for i in os.listdir(self.directory) if i[-3:] == '.py']
            for file in files:
                path = os.path.join(self.directory,file)
                name = file[:-3]
                spec = importlib.util.spec_from_file_location(name, path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                self.plugins.append(Plugin(name,module.Plugin))

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