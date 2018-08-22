import json
import os.path
import platform


if __name__ == '__main__':
    machine = platform.machine()
    processor = platform.processor()
    system = platform.system()

    cpuinfo_f = '/proc/cpuinfo'

    if (processor in {machine, 'unknown', ''} and os.path.exists(cpuinfo_f)):
        with open(cpuinfo_f, 'rt') as f:
            for line in f:
                if line.startswith('model name'):
                    _, _, p = line.partition(':')
                    processor = p.strip()
                    break

    distribution = None
    if 'Linux' in system:

        dist_f = '/etc/issue'
        if os.path.exists(dist_f):
            with open(dist_f, 'rt') as f:
                distribution = f.read().strip()

    data = {
        'cpu': processor,
        'arch': machine,
        'system': '{} {}'.format(system, platform.release()),
        'distribution': distribution
    }

    print(json.dumps(data))
