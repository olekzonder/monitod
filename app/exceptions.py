class ModuleNotActivatedError(Exception):
    def __init__(self,module):
        self.module = module
    def __str__(self):
        return f"Module {self.module} was not activated!"

class MissingFilterSettingsError(Exception):
    def __str__(self):
        return "Filter settings were not specified!"

class NoExporterError(Exception):
    def __str__(self):
        return "No such exporter!"
    
class LanguageParseError(Exception):
    def __init__(self, num:int, line:str, text:str):
        self.num = num+1
        self.line = line
        self.text = text
    def __str__(self):
        return f"{self.text}.\nCheck line:\n {self.num}\t{self.line}"

class ConfigurationError(Exception):
    def __init__(self,text:str):
        self.text = text
    def __str__(self):
        return f"{self.text}"

class NotifierError(Exception):
    def __init__(self,text):
        self.text = text
    def __str__(self):
        return f"{self.text}"
