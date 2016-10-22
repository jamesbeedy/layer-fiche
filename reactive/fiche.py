import os
import subprocess

from charms.reactive import (
    when,
    when_not,
    only_once,
    set_state,
    remove_state
)
from charmhelpers.core.templating import render

from charmhelpers.core.hookenv import (
    config,
    status_set,
    close_port,
    open_port,
    unit_public_ip
)

from charmhelpers.core.host import chdir

from nginxlib import configure_site

from charms.layer import options


@when('codebase.available')
@when_not('fiche.installed')
@only_once
def install_fiche():

    """ Install Fiche
    """

    status_set('maintenance', 'Installing and configuring Fiche.')

    # Build fiche
    with chdir(options('git-deploy').get('target')):
        subprocess.call('make', shell=False)
        subprocess.call('make install'.split(), shell=False)
        subprocess.call('rm -rf /srv/fiche/*'.split(), shell=False)

    set_state('fiche.installed')


@when('nginx.available')
@when_not('fiche.web.configured')
def render_nginx_conf():

    # Configure nginx vhost
    configure_site('fiche', 'fiche.nginx.tmpl', port=config('port'),
                   app_path=options('git-deploy').get('target'))
    # Open fiche front-end port
    open_port(config('port'))
    # Set state
    set_state('fiche.web.configured')


@when('fiche.installed')
@when_not('fiche.systemd.configured')
def render_systemd_conf():
    """Render fiche systemd conf
    """

    if config('fqdn'):
        server_name = config('fqdn')
    else:
        server_name = unit_public_ip()

    # Systemd vars
    SYSTEMD_CTXT = {
        'fiche_server_address': server_name,
        'fiche_server_port': config('fiche-server-port'),
        'slug_size': config('slug-size'),
        'buffer_size': config('buffer-size')
    }

    if os.path.exists('/etc/systemd/system/fiche.service'):
        os.remove('/etc/systemd/system/fiche.service')

    # Render systemd template
    render(source="fiche.service.tmpl",
           target="/etc/systemd/system/fiche.service",
           perms=0o644,
           owner="root",
           context=SYSTEMD_CTXT)

    # Open fiche server port
    open_port(config('fiche-server-port'))

    # Set 'fiche.systemd.configured'
    set_state('fiche.systemd.configured')


@when('fiche.web.configured', 'fiche.systemd.configured',
      'fiche.installed')
@when_not('fiche.available')
def fiche_available():
    # Set status
    status_set('active', 'Fiche is active at: %s' %
               ("%s/%s" % (unit_public_ip(), config('fiche-server-port'))))
    set_state('fiche.available')


@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=config('port'))


@when('config.changed.fiche-server-port')
def fiche_server_port_changed():

    """ React to fiche-server-port changed
    """
    status_set('maintenance', 'Reconfiguring fiche-server-port')

    conf = config()
    # Check and change open port, close prev port
    if conf.previous('fiche-server-port') and \
       conf.previous('fiche-server-port') != config('fiche-server-port'):
        close_port(config.previous('fiche-server-port'))
    # Remove state to re-render systemd conf
    remove_state('fiche.systemd.configured')
    remove_state('fiche.available')


@when('config.changed.port')
def fiche_port_changed():

    """ React to fiche front end port changed
    """
    status_set('maintenance', 'Reconfiguring fiche front end port')

    conf = config()
    # Close prev port
    close_port(conf.previous('fiche-server-port'))
    # Remove state to re-render nginx conf
    remove_state('fiche.web.configured')
    remove_state('fiche.available')


@when('config.changed.slug-size')
def fiche_slug_size_changed():

    """ React to slug-size changed
    """
    status_set('maintenance', 'Reconfiguring slug-size')
    # Remove state to re-render systemd conf
    remove_state('fiche.systemd.configured')
    remove_state('fiche.available')


@when('config.changed.buffer-size')
def fiche_buffer_size_changed():

    """ React to buffer-size changed
    """
    status_set('maintenance', 'Reconfiguring buffer-size')
    # Remove state to re-render systemd conf
    remove_state('fiche.systemd.configured')
    remove_state('fiche.available')
