# Интервал обновления скрипта в секундах
SLEEPING_TIME = 300
NB = ('P1', 'P3', 'P4', 'P6',)
ALL = NB + ('ГОД',)
objects = {
    'P3_and_P4': {
        'COM': 2,
        'ports': {
            'port_1': {
                'object': 'P4',
                'line': 1,
                'window': 0
            },
            'port_2': {
                'object': 'P3',
                'line': 1,
                'window': 1
            }
        }
    },
    'stella': {
        'COM': 3,
        'ports': {
            'port_1': {
                'object': 'NB',
                'line': 3,
                'window': 0
            },
            'port_2': {
                'object': 'ZF',
                'line': 3,
                'window': 1
            }
        }
    }
}
