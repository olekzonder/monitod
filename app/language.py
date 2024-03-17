import re
import socket
from monitor import PluginImporter
from notifier import NotifierImporter
from exceptions import LanguageParseError, ConfigurationError

class ServerSettings:
    def __init__(self):
        self.timeout = 5000
        self.secret = None
        self.message = f"[{socket.gethostname()}]"
    def set_var(self,name,option):
        match name:
            case 'timeout':
                self.timeout = int(option)
            case 'secret':
                self.secret = option
            case 'message':
                self.message = f"{self.message} {option}"
            case other:
                raise ConfigurationError("Unknown server parameter")
                
class Parameter:
    def __init__(self,name,value):
        self.name = name.strip()
        self.value = value.strip()
    def __str__(self):
        value = ' '.join(self.value.split()).replace('\'','').replace('"','')
        return f"\t{self.name}={value}" if self.name != 'none' else '\t no filter'
class Section:
    def __init__(self,name):
        self.name = name.strip()
        self.items = []
    def __iter__(self):
        yield from self.items
    def append(self,item):
        self.items.append(item)
    def __contains__(self,key):
        for item in self.items:
            if item.name == key:
                return True
        return False

    def  __getitem__(self,key):
        for item in self.items:
            if item.name == key:
                return item
        raise KeyError(f"{key}")

    def __setitem__(self,key,new_item):
        for item in self.items:
            if item.name == key:
                item = new_item
                return
        new_section = Section(key)
        new_section.append(new_item)
        self.items.append(new_section)
    def __str__(self):
        result = [self.name]
        for item in self.items:
            result.append(f"\t{str(item)}")
        return '\n'.join(result)

class ParseTree:
    def __init__(self):
        self.items = []
    def __iter__(self):
        yield from self.items
    def append(self,item):
        if isinstance(item, Section):
            self.items.append(item)
    def __getitem__(self,key):
        for item in self.items:
            if item.name == key:
                return item
        raise KeyError(f"{key}")
    def __containes__(self,key):
        for item in self.items:
            if item.name == key:
                return True
        raise False
    def __str__(self):
        result = ["Parse tree:"]
        for item in self.items:
            result.append(f"{str(item).strip()}")
        return '\n'.join(result)

class Parser:
    def __init__(self,language_path):
        self.sections = ParseTree()
        self.plugins = None
        self.notifiers = None
        self.rules = None
        self.settings = None
        with open(language_path) as f:
            self.text = [line.strip() for line in f.read().splitlines()]

    def _parse(self):
        current_section = None
        current_subsection = None
        current_subsection_empty = True
        current_mode = None
        for i, line in enumerate(self.text):
            if line == '':
                continue
            line = line.strip()
            if current_subsection != None and re.match(r'^-\s*(\w+)\s*:$',line) and current_subsection_empty:
                raise LanguageParseError(i,line,f"Subsection {current_subsection} expects a value!")
            if re.match(r'^\[(\w+)\]$',line):
                current_subsection = None
                current_section = re.match(r'^\[(\w+)\]$',line).group(1).strip()
                if current_section not in ['monitor','notify','rules','settings']:
                    raise LanguageParseError(i,line,f"Section {current_section} is not a valid section")
                self.sections.append(Section(current_section))
            elif re.match(r'\[.*',line):
                raise LanguageParseError(i,line, "Incorrect section syntax. Sections can't have whitespaces and should end with newline")
            # фильтрация подсекций с ключами и значениями
            elif re.match(r'^-\s*(\w+)\s*:$',line):
                current_subsection_empty = True
                current_subsection = re.match(r'^-\s*(\w+)\s*:$',line).group(1).strip()
                self.sections[current_section].append(Section(current_subsection))
            elif re.match('^-\s*"(.+)":$',line):
                if current_section != 'rules':
                    raise LanguageParseError(i,line,"Quoted parameters are only available for section notify")
                current_subsection_empty = True
                current_subsection = re.match('^-\s*"(.+)":$',line).group(1).strip()
                self.sections[current_section].append(Section(current_subsection))
            # фильтрация параметров   
            elif re.match(r'^\s*(\w+)\s*:(.+)$',line):
                key = re.match(r'^\s*(\w+)\s*:(.+)$',line).group(1).strip()
                value = re.match(r'^\s*(\w+)\s*:(.+)$',line).group(2).strip()
                if current_subsection == None:
                    raise LanguageParseError(i,line,f"Unexpected parameter: {key}")
                current_subsection_empty = False
                self.sections[current_section][current_subsection].append(Parameter(key,value))
            # фильтрация простых подсекций
            elif re.match(r'^\s*-\s*(\w+)$',line):
                if current_section != 'monitor':
                    raise LanguageParseError(i,line,"Simple subsections are only available for the 'monitor' section")
                simple_subsection = re.match(r'^-\s*(\w+)$',line).group(1).strip()
                self.sections[current_section][simple_subsection] = Parameter('none','none')
                pass
            else:
                raise LanguageParseError(i,line,"Syntax Error")
        if self.sections != None:
            return True
        else:
            return False

    def _analyze(self):
        try:
            parsed = self._parse()
        except LanguageParseError as e:
            print(str(e))
            return False
        if not parsed:
            raise ValueError("Other error")
        for section in self.sections:
            match section.name:
                case 'monitor':
                    if self.plugins != None:
                        continue
                    self.plugins = PluginImporter()
                    for subsection in section:
                        if not subsection.name in self.plugins:
                            raise ConfigurationError(f"Monitor {subsection.name} does not exist")
                        self.plugins[subsection.name].activate()
                        if 'include' in subsection and 'exclude' in subsection:
                            raise ConfigurationError(f"Can't have both filters applied in {subsection.name} subsection of {section.name}")
                        for parameter in subsection:
                            match parameter.name:
                                case 'include':
                                    self.plugins[subsection.name].set_filter(parameter.name,[i.strip() for i in parameter.value.strip().split(',')] if parameter.value.strip().split(',') else [parameter.value.strip()])
                                case 'exclude':
                                    self.plugins[subsection.name].set_filter(parameter.name,[i.strip() for i in parameter.value.strip().split(',')] if parameter.value.strip().split(',') else [parameter.value.strip()])
                                case 'none':
                                    pass
                                case other:
                                    raise ConfigurationError(f"No such filter: {parameter.name}")
                    self.plugins.read_all()
                    conditions = [i for i in self.plugins.read_conditions()]
                case 'notify':
                    if self.notifiers != None:
                        continue
                    self.notifiers = NotifierImporter()
                    for subsection in section:
                        options = {}
                        if subsection.name not in self.notifiers:
                            raise ConfigurationError(f"Notifier {subsection.name} does not exist")
                        self.notifiers[subsection.name].activate()
                        for parameter in subsection:
                            options[parameter.name] = parameter.value.replace('"','').replace('\'','').strip()
                        self.notifiers[subsection.name].set_options(options)
                case 'rules':
                    if self.rules != None:
                        continue
                    self.rules = True
                    if not self.notifiers:
                        raise ConfigurationError(f"Section {section.name} can't come before the notify section")
                    for subsection in section:
                        for parameter in subsection:
                            match parameter.name.strip():
                                case 'condition':
                                    groups = re.match(r"([\w\d_]+(?:\.[\w\d_]+)*\.[\w\d_]+)\s*([><=]+)\s*(\d+)",parameter.value.strip())
                                    if groups == None:
                                        raise ConfigurationError(f"Incorrect condition in {subsection.name} subsection  of {section.name}:\n{parameter.name}:{parameter.value}")
                                    condition,comparison,value = groups.groups()
                                    if condition not in conditions:
                                        raise ConfigurationError(f"Condition {condition} was not set up or does not exist")
                                    if comparison not in ['>','<','=','>=','<=']:
                                        raise ConfigurationError(f"Incorrect syntax:\n{subsection.name}: error in {parameter.name}:{parameter.value} \nComparison sign {comparison} is not valid")
                                case 'notify':
                                    for parameter in [i.strip() for i in parameter.value.split(',')] if parameter.value.split(',') else [parameter.value.strip()]:
                                        if parameter not in self.notifiers:
                                            raise ConfigurationError(f"Notifier {parameter} is not set up or does not exist!")
                                        self.notifiers[parameter].add_rule(subsection.name,condition,comparison,value)
                case 'settings':
                    self.settings = ServerSettings()
                    for subsection in section:
                        match subsection.name:
                            case 'server':
                                for parameter in subsection:
                                    if parameter.name not in vars(self.settings).keys():
                                        raise ConfigurationError(f"No such option for {subsection.name}: {parameter.name}")
                                    self.settings.set_var(parameter.name,parameter.value.replace('"','').replace('\'','').strip())
        return True

    def check(self):
        try:
            language = self._analyze()
        except LanguageParseError as e:
            print("Encountered a syntax error:")
            print(str(e))
            return False
        except ConfigurationError as e:
            print("Encountered a syntax error:")
            print(str(e))
            return False
        except ValueError as e:
            print("Encountered a runtime error:")
            print(str(e))
            return False
        return str(self.sections)

    def get_values(self):
        return self.plugins, self.notifiers, self.rules, self.settings