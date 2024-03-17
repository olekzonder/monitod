from monitor import PluginImporter
from cli import CLI
from language import Parser
from server import Server
import argparse

def cli():
    importer = PluginImporter()
    cli = CLI(importer)
    cli.run()
    exit()

def check_plugin(name):
    importer = PluginImporter()
    importer[name].activate()
    print(importer[name].read())
    print(f"\nAvailable conditions:\n{importer[name].get_conditions()}")
    exit()

def check_grammar(file):
    check = Parser(file).check()
    if check:
        print(check)
        print("Config file OK!")
def serve(file,port):
    server = Server(file,port)
    server.run()
    exit()
    return

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cli", action="store_true", help="run CLI mode")
    parser.add_argument("-s", "--server", type=str,  help="configure and run a server")
    parser.add_argument("-p", "--port", type=int, help="specify port for server mode (default is 1050)")
    parser.add_argument('-pl',"--plugin", type=str, help='test a plugin\'s output and get available conditions')
    parser.add_argument('-t',"--test",type=str,help="test a config file")
    args = parser.parse_args()

    if args.cli:
        cli()
    if args.server:
        serve(args.server, args.port if args.port else 1050)
    elif args.server and args.port:
        serve(args.server, args.port)
    elif args.test:
        check_grammar(args.test)
    elif args.plugin:
        check_plugin(args.plugin)
    else:
        cli()

if __name__ == "__main__":
    main()