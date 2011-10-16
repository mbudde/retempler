
import os.path
import json
import xdg.BaseDirectory as basedir


class Config(dict):

    defaults = {
        'width': 800,
        'height': 600,
        'regexes': [
            '(?P<show>.*?)S(?P<season>\d{2})E(?P<episode>\d{2})(?P<title>(\.[A-Z][a-z]+)*)',
        ],
        'templates': [
            '{{ show|replace(".", " ")|trim }}{% if year %} ({{ year }}){% endif %}/Season {{ season|int }}/{{ "S%02dE%02d"|format(season|int, episode|int) }}{% if title %} - {{ title|replace(".", " ")|trim }} {% endif %}',
            ('{{ show }}{% if year %} ({{ year }}){% endif %}'
             '/Season {{ season }}/{{ "S%02dE%02d"|format(season|int, episode|int) }}'
             '{% if title %} - {{ title }} {% endif %}'),
        ],
        'destination': None,
        'show_full_path': False,
    }

    def __getattribute__(self, name):
        try:
            return super(Config, self).__getattribute__(name)
        except AttributeError:
            try:
                return self[name]
            except KeyError:
                raise AttributeError

    def __setattr__(self, name, value):
        self[name] = value

    def __getitem__(self, key):
        try:
            return super(Config, self).__getitem__(key)
        except KeyError:
            return self.defaults[key]

    def load(self):
        dir = basedir.load_first_config('retempler')
        if dir:
            try:
                with open(os.path.join(dir, 'settings.json'), 'r') as fp:
                    self.update(json.load(fp))
            except (ValueError, IOError):
                pass

    def save(self):
        dir = basedir.save_config_path('retempler')
        with open(os.path.join(dir, 'settings.json'), 'w') as fp:
            json.dump(self, fp, indent=4)
