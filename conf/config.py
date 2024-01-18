import yaml


class Config:
    def __init__(self):
        with open('../conf/config.yml', 'rt') as f:
            config = yaml.safe_load(f.read())

        self.openApi_key = config["api"]["open-api-key"]
        self.graph_ip = config["graph"]["ip"]
        self.graph_port = config["graph"]["port"]
        self.graph_username = config["graph"]["username"]
        self.graph_password = config["graph"]["password"]



