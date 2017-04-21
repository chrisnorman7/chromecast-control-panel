"""Control Chromecast devices from the command line."""

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pychromecast import get_chromecasts
from attr import attrs, attrib, Factory
parser = ArgumentParser(
    description=__doc__,
    formatter_class=ArgumentDefaultsHelpFormatter
)

parser.add_argument(
    '--verbose',
    action='store_true',
    help='Print more information'
)

parser.add_argument(
    '-d',
    '--devices',
    action='append',
    help='Device(s) to control'
)

parser.add_argument(
    '-i',
    '--include-type',
    action='append',
    default=[],
    metavar='TYPE',
    help='Include a cast type (group for example)'
)
parser.add_argument(
    '-I',
    '--ignore-type',
    action='append',
    default=[],
    metavar='TYPE',
    help='Ignore a cast type (group for example)'
)

action_group = parser.add_mutually_exclusive_group()
action_group.add_argument(
    '-s',
    '--show',
    action='store_true',
    help='Show info about the target device(s)'
)
action_group.add_argument(
    '-v',
    '--set-volume',
    type=float,
    metavar='VOLUME',
    help='Set the volume of the target device(s) between 0.0 and 1.0'
)
action_group.add_argument(
    '-m',
    '--mute',
    action='store_true',
    help='Mute the target device(s)'
)
action_group.add_argument(
    '-u',
    '--unmute',
    action='store_true',
    help='Unmute the target device(s)'
)
action_group.add_argument(
    '--volume-up',
    action='store_true',
    help='Turn the volume of the target device(s) up a bit'
)
action_group.add_argument(
    '--volume-down',
    action='store_true',
    help='Turn the volume of the target device(s) down a bit'
)

action_group.add_argument(
    '-r',
    '--reboot',
    action='store_true',
    help='Reboot the target device(s)'
)


class ShowAction:
    """Show info about the currently-selected device."""
    def run(self, device):
        """Run this action."""
        if device.status:
            print(
                'Volume={} ({})\n'.format(
                    round(device.status.volume_level, 2),
                    'muted' if device.status.volume_muted else 'unmuted'
                )
            )
        else:
            print('No device status available.')


@attrs
class Action:
    """An action to perform."""
    name = attrib()
    args = attrib(default=Factory(list))
    kwargs = attrib(default=Factory(dict))

    def run(self, device):
        """Run this action on a device."""
        func = getattr(device, self.name)
        func(*self.args, **self.kwargs)


def error(msg):
    """Show an error and exit."""
    print('Error: ' + msg)
    raise SystemExit


if __name__ == '__main__':
    args = parser.parse_args()
    print('Scanning for Chromecast devices...')
    devices = get_chromecasts()
    if not devices:
        error('No Chromecast devices detected.')
    if args.devices:
        devices = [d for d in devices if d.name in args.devices]
        if not devices:
            error('No devices found matching %r.' % args.devices)
    devices = [
        x for x in devices if
        x.cast_type not in args.ignore_type and
        (not args.include_type or x.cast_type in args.include_type)
    ]
    if not devices:
        error('No devices found matching the specified criteria.')
    if args.set_volume is not None:
        if args.set_volume < 0.0 or args.set_volume > 1.0:
            error('Volume must be between 0.0 and 1.0.')
        else:
            actions = [Action('set_volume', args=[args.set_volume])]
    else:
        actions = []
    if args.show:
        actions.append(ShowAction())
    if args.mute:
        actions.append(Action('set_volume_muted', args=[True]))
    if args.unmute:
        actions.append(Action('set_volume_muted', args=[False]))
    if args.reboot:
        actions.append(Action('reboot'))
    if args.volume_up:
        actions.append(Action('volume_up'))
    if args.volume_down:
        actions.append(Action('volume_down'))
    for d in devices:
        if actions:
            print('Device: %s.' % d.name)
            for a in actions:
                if args.verbose:
                    print('Running %r.' % a)
                a.run(d)
        else:
            print(d)
