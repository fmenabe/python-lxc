from __future__ import unicode_literals
import re
import weakref
import unix
import unix.linux as linux


_FIELDS = ('name', 'state', 'ipv4', 'ipv6', 'autostart',
           'pid', 'memory', 'ram', 'swap')

RUNNING = 'RUNNING'
SHUTDOWN = 'STOPPED'

class LXCError(Exception):
    pass


def LXC(host):
    unix.isvalid(host)
    if not unix.ishost(host, 'Linux'):
        raise LXCError('this is not a Linux host')


    class Hypervisor(host.__class__):
        def __init__(self):
            host.__class__.__init__(self)
            self.__dict__.update(host.__dict__)


        def list_containers(self, **kwargs):
            def format_value(key, val):
                return (([v.strip() for v in val.split(',')] if val != '-' else [])
                        if 'ipv' in key
                        else ({'YES': True, 'NO': False}.get(val)
                              if val in ['YES', 'NO']
                              else val))

            kwargs.update({'fancy': True,
                           'fancy_format': ','.join(_FIELDS),
                           '1': True})
            status, stdout, stderr = self.execute('lxc-ls', **kwargs)
            if not status:
                raise LXCError(stderr)
            return {values[0]: {key: format_value(key, val)
                                for key, val in zip(_FIELDS[1:], values[1:])}
                    for container in stdout.splitlines()[2:]
                    for values in [re.split('\s{2,}', container)]}


        @property
        def container(self):
            return Container(weakref.ref(self)())


        @property
        def device(self):
            return Device(weakref.ref(self)())


    class Container(object):
        def __init__(self, host):
            self._host = host


        def exists(self, name):
            return True if name in self._host.list_containers() else False


        def info(self, name, **kwargs):
            kwargs.update(name=name)
            status, stdout, stderr = self._host.execute('lxc-info', **kwargs)
            if not status:
                raise LXCError(stderr)
            return {param.lower().strip().replace(' use', ''): value.strip()
                    for line in stdout.splitlines()
                    for param, value in [line.split(':')]}


        def state(self, name):
            return self.info(name, state=True)['state']


        def console(self, name, **kwargs):
            self._host.execute('lxc-console', name=name,
                                TTY=True, INTERACTIVE=True, **kwargs)


        def create(self, name, tmpl_opts={}, **kwargs):
            def format_opt(opt, value):
                opt = '%s%s' % ('-' if len(opt) == 1 else '--', opt)
                return '%s %s' % (opt, value if isinstance(value, str) else '')

            tmpl_args = ' '.join(format_opt(opt, value) for opt, value in tmpl_opts.items())
            with self._host.set_controls(escape_args=False):
                return self._host.execute('lxc-create', '--', tmpl_args, name=name, **kwargs)


        def destroy(self, name, **kwargs):
            return self._host.execute('lxc-destroy', name=name, **kwargs)


        def start(self, name, **kwargs):
            return self._host.execute('lxc-start', name=name, **kwargs)


    class Device:
        def __init__(self, host):
            self._host = host


        def add(self, name, device):
            return self._host.execute('lxc-device', 'add', device, n=name)

    return Hypervisor()
