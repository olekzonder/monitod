# Monitord

Monitord is a simple monitoring agent written in Python. 

Command reference:

```
  -h, --help            show this help message and exit
  -c, --cli             run CLI mode
  -s SERVER, --server SERVER
                        configure and run a server
  -p PORT, --port PORT  specify port for server mode (default is 1050)
  -pl PLUGIN, --plugin PLUGIN
                        test a plugin's output and get available conditions
  -t TEST, --test TEST  test a config file

```


# Config example

```

[monitor]
-cpu
- battery
- thermal:
  exclude: thinkpad, iwlwifi_1
- load
- memory:
  include: total, free, used

[notify]
- telegram:
  api_token: 'TOKEN'
  chat_id: "CHAT ID"

[rules]
- "Not nice charge":
  condition: battery.bat0.charge <= 69
  notify: telegram
- "CPU is heated":
  condition: thermal.coretemp.package_id_0.current > 75
  notify: telegram
- "RAM leak":
  condition: memory.free: 1000
  notify: telegram
  
[settings]
- server:
  timeout: "2500"
  message: "Please notice the following values:"
  secret: "test"
```
