from language import Parser, ServerSettings
from exceptions import NotifierError
import websockets, threading, uuid, logging, asyncio, json
class Server:
    def __init__(self,file,port):
        logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',level=logging.INFO)
        self.port = port
        self.notifications = False
        self.connected_clients = set()
        language = Parser(file)
        if language.check() != False:
            logging.info("Configuration file OK!")
            self.plugins, self.notifiers, self.rules, self.settings = language.get_values()
        else:
                logging.error("Config has not passed!")
                exit()
        if self.notifiers != None and self.rules == None:
            logging.warning("Notifier is set up, but no rules are applied, messages won't be sent")
        elif self.notifiers != None and self.rules != None:
            self.notifications = True
        if self.settings == None:
            logging.info("Using standart logs")
            self.settings = ServerSettings()
    def update(self):
        self.data = self.plugins.read_all()
        self.conditions = self.plugins.read_conditions()
    def send_messages(self):
        if not self.notifications:
            return
        for notifier in self.notifiers:
            for rule in notifier:
                thresholds = []
                condition = float(self.conditions[rule.condition]['value'])
                unit = self.conditions[rule.condition]['unit']
                if rule.active:
                    was_active = True
                else:
                    was_active = False
                match rule.sign:
                    case '>':
                        if condition > float(rule.value):
                            rule.active = True
                        else:
                            rule.active = False
                    case '<':
                        if condition < float(rule.value):
                            rule.active = True
                        else:
                            rule.active = False
                    case '<=':
                        if condition <= float(rule.value):
                            rule.active = True
                        else:
                            rule.active = False
                    case '>=':
                        if condition >= float(rule.value):
                            rule.active = True
                        else:
                            rule.active = False
                    case '=':
                        if condition == float(rule.value):
                            rule.active = True
                        else:
                            rule.active = False
                if was_active and not rule.active:
                    continue
                elif was_active and rule.active:
                    continue
                elif not was_active and rule.active:
                    thresholds.append(f"{rule.name}: {condition} {unit}")
                if thresholds:
                    message = [self.settings.message, '\n'.join(thresholds)]
                    try:
                        notifier.send(message)
                        logging.info(f"Successfully sent a message to {notifier.name}")
                    except NotifierError as e:
                        logging.error(f"{notifier.name} returned error: {str(e)}")

    async def handle_client(self, websocket, path):
        connected = False
        header = websocket.request_headers
        if self.settings.secret is not None:
            if header.get('Secret') == self.settings.secret:
                logging.info("successful connection")
                self.connected_clients.add(websocket)
                connected = True
            else:
                logging.info("connection refused: incorrect secret")
                websocket.send('No secret provided or incorrect secret')
                await websocket.close()
        else:
            self.connected_clients.add(websocket)
            connected = True
        if connected:
            try:
                while True:
                    await self.send_message(websocket)
                    await asyncio.sleep(self.settings.timeout/1000)  # Ждем некоторое время, чтобы не блокировать цикл
            except websockets.exceptions.ConnectionClosed:
                self.connected_clients.remove(websocket)

    async def send_message(self, websocket):
        data_json = json.dumps(self.data.to_dict())
        await websocket.send(data_json)

    def start_server(self):
        logging.info("Starting server...")
        async def update_loop():
            while True:
                self.update()
                self.send_messages()
                await asyncio.sleep(self.settings.timeout/1000)
        async def start_websockets():
            server = await websockets.serve(self.handle_client, 'localhost', self.port)
            await server.wait_closed()
        loop = asyncio.get_event_loop()
        loop.create_task(update_loop())
        loop.run_until_complete(start_websockets())
        
    def run(self):
        self.start_server()