import sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT))
from app.core.config import get_settings
s = get_settings()
paths = s.get_model_paths()
print('ASR path:', paths['asr'])
print('ASR exists:', paths['asr'].exists())
print('ASR config exists:', (paths['asr'] / 'config.json').exists())
print('CLASS path:', paths['classifier'])
print('CLASS exists:', paths['classifier'].exists())
print('CLASS config exists:', (paths['classifier'] / 'config.json').exists())
