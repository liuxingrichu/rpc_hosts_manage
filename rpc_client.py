#!/usr/bin/env python
# -*- coding:utf-8 -*-

import random
import pika


class RpcClient(object):
    def __init__(self):
		#部署rabbitMQ服务的IP、端口和用户账号及密码
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters( host='192.168.31.101', port=5672,virtual_host='/',
            credentials=pika.PlainCredentials('test','123456')))

        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='direct_logs',
                                      type='direct')
        result = self.channel.queue_declare(exclusive=True)
        self.callback_queue = result.method.queue
        self.channel.basic_consume(self.on_response,
                                   no_ack=True,
                                   queue=self.callback_queue)
        self.response = False

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            response_list.append(body)
            response_dict[self.corr_id] = response_list
            self.response = True

    @staticmethod
    def identifying_code(lenth=5):
        _code = list()
        for i in range(lenth):
            _code.append(str(random.randrange(0, 9)))
        return "".join(_code)

    def call(self, cmd):
        self.corr_id = self.identifying_code()
        for severity in severities:
            self.channel.basic_publish(exchange='direct_logs',
                                       routing_key=severity,
                                       properties=pika.BasicProperties(
                                           reply_to=self.callback_queue,
                                           correlation_id=self.corr_id,
                                       ),
                                       body=cmd)
        print('\ttask ID: ', self.corr_id)


rpc_client = RpcClient()
response_list = []
response_dict = dict()

while True:
    cmd_str = input('>>').strip() 
    if not cmd_str:
        continue
    # print(cmd_str)

    if '"' in cmd_str:
        cmd_list = cmd_str.split('"')
    else:
        cmd_list = cmd_str.split()

    action = cmd_list[0].strip()

    if action == 'run':
        if len(cmd_list) != 3:
            print('\tparameters error')
            continue

        cmd = cmd_list[1]
        severities = cmd_list[-1].split()[1:]
        rpc_client.call(cmd)

        for severity in severities:
            rpc_client.channel.queue_bind(exchange='direct_logs',
                                          queue=rpc_client.callback_queue,
                                          routing_key=severity)


    elif action == 'check_task':
        if len(cmd_list) != 2:
            print('\tparameters error')
            continue

        cmd = cmd_list[1]
        while not rpc_client.response:
            rpc_client.connection.process_data_events()

        if response_dict.get(cmd):
            for value in response_dict[cmd]:
                print(value.decode())
            del response_dict[cmd]
            response_list = []
            rpc_client.response = False
    else:
        continue
