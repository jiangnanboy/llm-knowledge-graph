# -*- coding: utf-8 -*-
import tomli

def load_config(config_file="config.toml"):
    try:
        with open(config_file, "rb") as f:
            return tomli.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        return None 