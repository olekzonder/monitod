from monitor import Monitor
class Plugin(Monitor):
    def get_data(self):
        self.static_plugin()
        gpuinfo = self.read('command','glxinfo -B', output_format='key_value')
        for gpu in gpuinfo:
            self.data['vendor'] = gpu['OpenGL vendor string']
            self.data['device'] = gpu['OpenGL renderer string']
            self.data['video_memory'] = gpu['Video memory']
            self.data['opengl_version'] = gpu['OpenGL version string']
            self.data['opengl_gles_version'] = gpu['OpenGL ES profile version string']
            self.data['mesa_version'] = gpu['Version']
            self.data['accelerated'] = gpu['Accelerated']
        return self.data