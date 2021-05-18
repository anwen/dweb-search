
log = {
    'log_max_bytes': 50 * 1024 * 1024,  # 50M
    'backup_count': 100,
    'log_path': {
        # logger of running server; DONOT change the name 'logger'
        'logger': 'log/files/server.log',
        # logger of user behavior
        'user_logger': 'log/files/user.log'
    }
}
port = 8888

from options.server_config import *  # noqa
