import logging
import coloredlogs

level_styles = coloredlogs.DEFAULT_LEVEL_STYLES
level_styles['debug'] = {'color': 'blue'}
level_styles['warning'] = {'color': 'black', 'background': 'yellow'}
level_styles['error'] = {'color': 'yellow', 'background': 'red'}


def init_logging(level: str = 'DEBUG'):
    log_format = '[%(asctime)s.%(msecs)03d][%(name)s][%(threadName)s] %(levelname)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    coloredlogs.install(level=level, fmt=log_format, datefmt=date_format)
