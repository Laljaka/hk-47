import json

__all__ = ['json_read', 'json_write']


def json_read(filename):
    with open(f'storage/{filename}.json', 'r') as f:
        data = json.load(f)
    return data


def json_write(filename, data):
    with open(f'storage/{filename}.json', 'w') as f:
        json.dump(data, f, indent=4)

