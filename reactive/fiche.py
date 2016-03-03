#!/usr/bin/python3
# Copyright (c) 2016, James Beedy <jamesbeedy@gmail.com>

import os
import sys
import pwd
import shutil
import subprocess

from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import only_once
from charms.reactive import set_state
from charmhelpers.core.templating import render
from charmhelpers.core import hookenv
from charmhelpers.core import host
from charmhelpers.core.host import chdir

from nginxlib import configure_site


FICHE_GIT_REPO = 'https://github.com/solusipse/fiche.git'
FICHE_CODE_DIR = '/srv/fiche/'
FICHE_SUPERVISOR_CONF = '/etc/supervisor/conf.d/fiche.conf'

config = hookenv.config()

FICHE_SUPERVISOR_CTXT = {
    'fiche_server_address': hookenv.unit_public_ip(),
    'fiche_server_port': config['fiche-server-port'],
    'slug_size': config['slug-size'],
    'buffer_size': config['buffer-size']
}


def _render_fiche_supervisor_conf(ctxt):

    """ Render /etc/supervisor/conf.d/fiche.conf
        and restart supervisor process.
    """
    if os.path.exists(FICHE_SUPERVISOR_CONF):
        subprocess.call('supervisorctl stop fiche'.split(), shell=False)
        os.remove(FICHE_SUPERVISOR_CONF)

    render(source='fiche.conf',
           target=FICHE_SUPERVISOR_CONF,
           owner='root',
           perms=0o644,
           context=ctxt)

    # Reread supervisor .conf and start/restart process
    subprocess.call('supervisorctl reread'.split(), shell=False)
    subprocess.call('supervisorctl update'.split(), shell=False)
    subprocess.call('supervisorctl start fiche'.split(), shell=False)

    # Restart NGINX
    host.service_restart('nginx')


def _ensure_basedir():

    """ Ensure fiche basedir exists
    """
    if not os.path.isdir(FICHE_CODE_DIR):
        os.makedirs(FICHE_CODE_DIR)

    uid = pwd.getpwnam('www-data').pw_uid
    os.chown(FICHE_CODE_DIR, uid, -1)


@when('nginx.available')
@when_not('fiche.available')
@only_once
def install_fiche():

    """ Install Fiche
    """

    hookenv.status_set('maintenance', 'Installing and configuring Fiche.')

    # Clone fiche repo
    hookenv.status_set('maintenance', 
                       'Installing and building fiche from github.')

    git_clone_cmd = 'git clone %s /tmp/fiche' % FICHE_GIT_REPO
    subprocess.call(git_clone_cmd.split(), shell=False)  
  
    # Build fiche
    with chdir("/tmp/fiche"):
        subprocess.call('make', shell=False)
        subprocess.call('make install'.split(), shell=False)

    # Ensure base dir exists
    _ensure_basedir()

    # Configure nginx vhost
    configure_site('fiche', 'fiche.vhost', app_path=FICHE_CODE_DIR)

    # Render fiche supervisor conf
    _render_fiche_supervisor_conf(FICHE_SUPERVISOR_CTXT)
    
    # Open fiche server port
    hookenv.open_port(config['fiche-server-port'])

    # Open fiche front-end port
    hookenv.open_port(config['port'])

    # Set status
    hookenv.status_set('active', 'Fiche is active on port %s' % \
                       config['fiche-server-port'])
    # Set state
    set_state('fiche.available')
    

@when('nginx.available', 'website.available')
def configure_website(website):
    website.configure(port=config['port'])


@when('config.changed.fiche-server-port')
def fiche_port_changed():

    """ React to fiche-server-port changed
    """
    hookenv.status_set('maintenance', 'Reconfiguring fiche-server-port')

    # Check and change open port, close prev port
    if config.previous('fiche-server-port') and \
       config.previous('fiche-server-port') != config['fiche-server-port']:
        hookenv.close_port(config.previous('fiche-server-port'))
        hookenv.open_port(config['fiche-server-port'])

    _render_fiche_supervisor_conf(FICHE_SUPERVISOR_CTXT)
    hookenv.status_set('active', 'Fiche is active on port %s' % \
                       config['fiche-server-port'])


@when('config.changed.slug-size')
def fiche_slug_size_changed():

    """ React to slug-size changed
    """
    hookenv.status_set('maintenance', 'Reconfiguring slug-size')

    # Rerender supervisord conf
    _render_fiche_supervisor_conf(FICHE_SUPERVISOR_CTXT)

    hookenv.status_set('active', 'Fiche is active on port %s' % \
                       config['fiche-server-port'])

@when('config.changed.buffer-size')
def fiche_buffer_size_changed():

    """ React to buffer-size changed
    """
    hookenv.status_set('maintenance', 'Reconfiguring buffer-size')

    # Rerender supervisord conf
    _render_fiche_supervisor_conf(FICHE_SUPERVISOR_CTXT)

    hookenv.status_set('active', 'Fiche is active on port %s' % \
                       config['fiche-server-port'])
