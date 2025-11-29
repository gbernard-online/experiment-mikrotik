#!/usr/bin/env python3
#--------------------------------------------- ghislain.bernard@gmail.com ---------------------------------------------#

import datetime
import os
import socket
import ssl
import time

import routeros_api

#----------------------------------------------------------------------------------------------------------------------#

DELAY = 60
EXPIRATION = '5m'
TIMEOUT = 1.0

#----------------------------------------------------------------------------------------------------------------------#

def main():

  print(datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)

  router = routeros_api.RouterOsApiPool(os.environ['MIKROTIK_HOSTNAME'],
                                        password=os.environ['MIKROTIK_PASSWORD'],
                                        username=os.environ['MIKROTIK_USERNAME'],
                                        plaintext_login=True,
                                        ssl_context=ssl.create_default_context(cafile='ca.crt')).get_api()

  #######################

  static = router.get_resource('/ip/dns/static')

  for entry in sorted([entry for entry in static.call('print') if entry['type'] in ['A', 'AAAA']],
                      key=lambda entry: entry['name'] + entry['type'] + entry['address']):

    if 'comment' not in entry or '=' not in entry['comment']:
      continue

    service = entry['comment'].split('=', 1)

    #######################

    if entry['ttl'] != EXPIRATION:
      static.call('set', {'id': entry['id'], 'ttl': EXPIRATION})
      entry['ttl'] = EXPIRATION
      print(entry, flush=True)

    #######################

    stream = socket.socket(socket.AF_INET6 if entry['type'] == 'AAAA' else socket.AF_INET, socket.SOCK_STREAM)

    if stream.connect_ex((entry['address'], int(service[0]))) == 0 and (service[1] == '' or stream.recvmsg(
        len(service[1]))[0].decode('ASCII').rstrip() == service[1]):

      if entry['disabled'] == 'true':
        static.call('set', {'id': entry['id'], 'disabled': 'false'})
        entry['disabled'] = 'false'
        print(entry, flush=True)

    else:

      if entry['disabled'] == 'false':
        static.call('set', {'id': entry['id'], 'disabled': 'true'})
        entry['disabled'] = 'true'
        print(entry, flush=True)

    stream.close()

  #######################

  print('-', flush=True)

#----------------------------------------------------------------------------------------------------------------------#

if __name__ == '__main__':

  socket.setdefaulttimeout(TIMEOUT)

  while True:
    main()
    time.sleep(DELAY)

#--------------------------------------------- ghislain.bernard@gmail.com ---------------------------------------------#
