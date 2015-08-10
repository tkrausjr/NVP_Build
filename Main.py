__author__ = 'tkraus'
nsx_ip = "192.168.110.201"
nsx_port = 443
username = "admin"
password = "admin"


import httplib
import urllib
import hashlib


class NVPApiHelper:

    def __init__(self):
        engine = create_engine(sql_connection)
        try:
            engine.connect()
        except:
            print "Unable to connect to %s " % sql_connection
        self.db = SqlSoup(engine)

def nvp_login(username, password):
    session_cookie = None
    body = urllib.urlencode({"username": username, "password": password })
    headers = {"Content-Type":"application/x-www-form-urlencoded"}
    conn = httplib.HTTPSConnection(nvp_ip, nvp_port)
    conn.request("POST", "/ws.v1/login", body, headers)
    response = conn.getresponse()
    if response.status in [httplib.OK]:
        cookies = response.getheader("Set-Cookie")
        session_cookie = filter(lambda x: x.find("nvp_sessionid")==0,
                                cookies.split(";"))[0]
    else:
        print "error: login failed, http response status: %s" % response.status
        print response.read()
    conn.close()
    return session_cookie


def nvp_create_lswitch(session_cookie, displayname):
    headers = {'Cookie': session_cookie}
    conn =  httplib.HTTPSConnection(nvp_ip, nvp_port)
    body = {'display_name': displayname,
            'transport_zones':
                [{'zone_uuid': tz_uuid,
                 'transport_type': 'stt'}],
            'replication_mode': 'service',
            'type': 'LogicalSwitchConfig'
            }

    conn.request("POST", "/ws.v1/lswitch", json.dumps(body), headers)
    response = conn.getresponse()
    if response.status != 201:
        print "ERROR create network"
        print response.read()
        exit(1)
    else:
        response = json.loads(response.read())
        return response['uuid']

def nvp_create_lport(session_cookie, displayname, net_uuid, attachment, vp_uuid):
    headers = {'Cookie': session_cookie}
    body = {'display_name': displayname,
            'type': 'LogicalSwitchPortConfig'}
    conn =  httplib.HTTPSConnection(nvp_ip, nvp_port)
    conn.request("POST", "/ws.v1/lswitch/" + str(net_uuid) + "/lport",
                 json.dumps(body), headers)
    response = conn.getresponse()
    if response.status != 201:
        print response.read()
        print "ERROR create_port"
        exit(1)
    elif attachment == 'vif':
        response = json.loads(response.read())
        nvp_id = response['uuid']
        body =  {'vif_uuid': vp_uuid,
                 'type': 'VifAttachment'}
        conn = httplib.HTTPSConnection(nvp_ip, nvp_port)
        conn.request("PUT", "/ws.v1/lswitch/" + str(net_uuid) + "/lport/" +
                     str(nvp_id) + "/attachment",
                     json.dumps(body), headers)
        response = conn.getresponse()
        if response.status != 200:
            print "ERROR attach"
            print response.read()
            exit(1)
        return nvp_id
    elif attachment == 'patch':
        response = json.loads(response.read())
        nvp_id = response['uuid']
        body =  {'peer_port_uuid': vp_uuid,
                 'type': 'PatchAttachment'}
        conn = httplib.HTTPSConnection(nvp_ip, nvp_port)
        conn.request("PUT", "/ws.v1/lswitch/" + str(net_uuid) + "/lport/" +
                     str(nvp_id) + "/attachment",
                     json.dumps(body), headers)
        response = conn.getresponse()
        if response.status != 200:
            print "ERROR attach"
            print response.read()
            exit(1)
        return nvp_id

def nvp_create_lrouter(session_cookie, displayname, gateway_ip):
    headers = {'Cookie': session_cookie}
    conn =  httplib.HTTPSConnection(nvp_ip, nvp_port)
    body = {'display_name': displayname,
            'replication_mode': 'service',
            'routing_config':
                 {'default_route_next_hop': {'gateway_ip_address': gateway_ip,
                                             'type': 'RouterNextHop'
                                            },
                  'type': 'SingleDefaultRouteImplicitRoutingConfig'
                 },
            'type': 'LogicalRouterConfig'
            }

    conn.request("POST", "/ws.v1/lrouter", json.dumps(body), headers)
    response = conn.getresponse()
    if response.status != 201:
        print "ERROR create router"
        print response.read()
        exit(1)
    else:
        response = json.loads(response.read())
        return response['uuid']

def nvp_create_gws(session_cookie, displayname, gw_uuid, device_id, type):
    headers = {'Cookie': session_cookie}
    conn =  httplib.HTTPSConnection(nvp_ip, nvp_port)
    body = {'display_name': displayname,
            'gateways':
                [{'transport_node_uuid': gw_uuid,
                  'device_id': device_id,
                  'group_id': 0,
                  'type': type}],
            'type': type+'ServiceConfig'
            }

    conn.request("POST", "/ws.v1/gateway-service", json.dumps(body), headers)
    response = conn.getresponse()
    if response.status != 201:
        print "ERROR create gateway service"
        print response.read()
        exit(1)
    else:
        response = json.loads(response.read())
        return response['uuid']

def nvp_create_lrport(session_cookie, displayname, ip_address, lr_uuid, gws_uuid, attachment):
    headers = {'Cookie': session_cookie}
    body = {'display_name': displayname,
            'ip_addresses': [ip_address],
            'type': 'LogicalRouterPortConfig'}
    conn =  httplib.HTTPSConnection(nvp_ip, nvp_port)
    conn.request("POST", "/ws.v1/lrouter/" + lr_uuid + "/lport",
                 json.dumps(body), headers)
    response = conn.getresponse()
    if response.status != 201:
        print response.read()
        print "ERROR create_port"
        exit(1)
    elif attachment == 'l3':
        response = json.loads(response.read())
        nvp_id = response['uuid']
        body = {'l3_gateway_service_uuid': gws_uuid,
                'type': 'L3GatewayAttachment'}
        conn = httplib.HTTPSConnection(nvp_ip, nvp_port)
        conn.request("PUT", "/ws.v1/lrouter/" + lr_uuid + "/lport/" +
                     str(nvp_id) + "/attachment",
                     json.dumps(body), headers)
        response = conn.getresponse()
        if response.status != 200:
            print "ERROR attach"
            print response.read()
            exit(1)
        return nvp_id
    else:
        response = json.loads(response.read())
        nvp_id = response['uuid']
        return nvp_id


tz_uuid = '384f5f37-627c-45c4-9b34-1ae77db1e991'

def main():
    session_cookie = nvp_login(username, password)
    web_uuid = nvp_create_lswitch(session_cookie, 'Web-Tier')
    app_uuid = nvp_create_lswitch(session_cookie, 'App-Tier')
    db_uuid = nvp_create_lswitch(session_cookie, 'DB-Tier')
    print "created logical switch with uuid = '%s'" % web_uuid
    print "created logical switch with uuid = '%s'" % app_uuid
    print "created logical switch with uuid = '%s'" % db_uuid

    web1_port = nvp_create_lport(session_cookie, 'web-sv-01a', web_uuid, 'vif', '52c6c6f7-715d-e6b8-93b5-d1ded1e7ce98-0')
    web2_port = nvp_create_lport(session_cookie, 'web-sv-02a', web_uuid, 'vif', '03b2fac8-f673-c5e8-c265-41b27bc7e608')
    web3_port = nvp_create_lport(session_cookie, 'web-sv-03a', web_uuid, 'vif', '72ad106e-90e8-d09a-c57f-3a7472d8ae83')
    app_port = nvp_create_lport(session_cookie, 'app-sv-01a', app_uuid, 'vif', '524e42a5-3a9a-8d7e-b86f-21a7432d40be-0')
    db_port = nvp_create_lport(session_cookie, 'db-sv-01a', db_uuid, 'vif', '521ccb03-e0c6-4437-3a42-0c296fcba36d-0')
    lb_port = nvp_create_lport(session_cookie, 'lb-sv-01a', web_uuid, 'vif', '52febf18-afcf-c131-c784-49e89564dca1-0')
    print "created logical port with uuid = '%s'" % web1_port
    print "created logical port with uuid = '%s'" % web2_port
    print "created logical port with uuid = '%s'" % web3_port
    print "created logical port with uuid = '%s'" % app_port
    print "created logical port with uuid = '%s'" % db_port
    print "created logical port with uuid = '%s'" % lb_port
    l3gws_uuid = nvp_create_gws(session_cookie, 'L3GWService', 'dc51a1bc-4c43-4d55-8011-6b558d2f4740', 'breth0', 'L3Gateway')
    print "created L3 GWS with uuid = '%s'" % l3gws_uuid
    router_uuid = nvp_create_lrouter(session_cookie, 'Distributed-Router', '192.168.130.2')
    print "created logical router with uuid = '%s'" % router_uuid
    uplink_uuid = nvp_create_lrport(session_cookie, 'L3Uplink', '192.168.130.10/24', router_uuid, l3gws_uuid, 'l3')
    webgw_uuid = nvp_create_lrport(session_cookie, 'Web-GW', '172.16.10.1/24', router_uuid, '', '')
    appgw_uuid = nvp_create_lrport(session_cookie, 'App-GW', '172.16.20.1/24', router_uuid, '', '')
    dbgw_uuid = nvp_create_lrport(session_cookie, 'DB-GW', '172.16.30.1/24', router_uuid, '', '')
    print "created logical router port with uuid = '%s'" % uplink_uuid
    print "created logical router port with uuid = '%s'" % webgw_uuid
    print "created logical router port with uuid = '%s'" % appgw_uuid
    print "created logical router port with uuid = '%s'" % dbgw_uuid
    webpatch_uuid = nvp_create_lport(session_cookie, 'Web-Patch', web_uuid, 'patch', webgw_uuid)
    apppatch_uuid = nvp_create_lport(session_cookie, 'App-Patch', app_uuid, 'patch', appgw_uuid)
    dbpatch_uuid = nvp_create_lport(session_cookie, 'DB-Patch', db_uuid, 'patch', dbgw_uuid)
    print "created patch port with uuid = '%s'" % webpatch_uuid
    print "created patch port with uuid = '%s'" % apppatch_uuid
    print "created patch port with uuid = '%s'" % dbpatch_uuid

if __name__ == "__main__":
    main()
