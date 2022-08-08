import logging
import sys
import os

import grpc
import helloworld_pb2
import helloworld_pb2_grpc

from dapr.clients import DaprClient
from google.protobuf import json_format

def publish_message(request):
    client = DaprClient()
    request_json = json_format.MessageToJson(request)
    client.publish_event(pubsub_name='mqtt-pubsub', topic_name='greeter', data=request_json, data_content_type='application/json')


def build_grpc_channel(native_grpc_port, dapr_grpc_port, command_line_port = None):
    native_grpc_host = "contoso.local" #to match the ssl certificate CN
    if dapr_grpc_port == 0:
        port = command_line_port if command_line_port != None else native_grpc_port
    else:
        port = dapr_grpc_port
    if (port != native_grpc_port): # running in dapr
        grpc_channel = grpc.insecure_channel(f"localhost:{port}")
        logging.info(f'Connecting to localhost:{port}')
    else:
        with open('certs\server.crt', 'rb') as f:
            channel_credentials = grpc.ssl_channel_credentials(f.read())
        grpc_channel = grpc.secure_channel(f"{native_grpc_host}:{port}", channel_credentials) #grpc.local_channel_credentials() also works in dev.
        logging.info(f'Connecting to secure {native_grpc_host}:{port}')
    return grpc_channel


def main():
    request = helloworld_pb2.HelloRequest(name='world')
    if len(sys.argv) > 1:
        logging.info('Invoke grpc service')
        native_grpc_port = "50051"
        # daprd launch task sets the env var DAPR_GRPC_PORT, however,
        # Python launcher doesn't seem to pass env vars to the main process.
        # So pass it in as a command line argument for debugging. 
        command_line_port = sys.argv[2] if len(sys.argv) > 2 else None
        dapr_grpc_port = os.getenv('DAPR_GRPC_PORT', 0)
        with build_grpc_channel(native_grpc_port, dapr_grpc_port, command_line_port) as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            # metadata for dapr grpc proxy to route to the original service
            metadata = [('dapr-app-id', 'greeter')]
            response = stub.SayHello(request, metadata=metadata)
        logging.info("Greeter client received: " + response.message)
    else:
        logging.info('Publish event')
        publish_message(request)
        logging.info('Published event')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()