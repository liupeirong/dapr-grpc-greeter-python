import logging
import sys

import grpc
import helloworld_pb2
import helloworld_pb2_grpc

from dapr.clients import DaprClient
from google.protobuf import json_format

def main():
    request = helloworld_pb2.HelloRequest(name='you')
    if len(sys.argv) > 1:
        print('Invoke grpc service')
        native_grpc_host = "contoso.local" 
        native_grpc_port = "50051"
        # daprd launch task set the env var DAPR_GRPC_PORT, however,
        # Python launcher doesn't seem to pass env vars to the main process.
        # So pass it in as a command line argument. 
        # port = os.getenv('DAPR_GRPC_PORT', native_grpc_port)
        port = sys.argv[2] if len(sys.argv) > 2 else native_grpc_port
        if (port != native_grpc_port): # running in dapr
            grpc_channel = grpc.insecure_channel(f"localhost:{port}")
            print(f'Connecting to localhost:{port}')
        else:
            with open('certs\server.crt', 'rb') as f:
               channel_credentials = grpc.ssl_channel_credentials(f.read())
            grpc_channel = grpc.secure_channel(f"{native_grpc_host}:{port}", channel_credentials) #grpc.local_channel_credentials() also works in dev.
            print(f'Connecting to secure {native_grpc_host}:{port}')
        with grpc_channel as channel:
            stub = helloworld_pb2_grpc.GreeterStub(channel)
            # metadata for dapr grpc proxy to route to the original service
            metadata = [('dapr-app-id', 'greeter')]
            response = stub.SayHello(request, metadata=metadata)
        print("Greeter client received: " + response.message)
    else:
        print('Publish event')
        request_json = json_format.MessageToJson(request)
        client = DaprClient()
        client.publish_event(pubsub_name='mqtt-pubsub', topic_name='greeter', data=request_json, data_content_type='application/json')
        print('Published event')

if __name__ == '__main__':
    logging.basicConfig()
    main()