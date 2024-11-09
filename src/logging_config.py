import sys

def get_logging_config():
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S %z'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'default',
                'level': 'INFO'
            }
        },
        'root': {
            'level': 'INFO',
            'handlers': ['console']
        },
        'loggers': {
            'quart': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'hypercorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            }
        }
    }