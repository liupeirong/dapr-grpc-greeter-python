from concurrent import futures
import logging

import grpc
import helloworld_pb2
import helloworld_pb2_grpc

from google.protobuf import json_format

from dapr.proto import appcallback_v1, appcallback_service_v1

class Greeter(helloworld_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        return helloworld_pb2.HelloReply(message='Hello, %s!' % request.name)

class Subscriber(appcallback_service_v1.AppCallbackServicer):
    def ListTopicSubscriptions(self, request, context):
        subscriptions = [appcallback_v1.TopicSubscription(pubsub_name='mqtt-pubsub', topic='greeter')]
        return appcallback_v1.ListTopicSubscriptionsResponse(subscriptions=subscriptions)

    def OnTopicEvent(self, request, context):
        if request.topic == 'greeter':
            logging.info("received message!")
            derequest = helloworld_pb2.HelloRequest()
            json_format.Parse(request.data, derequest)
            g = Greeter()
            message = g.SayHello(derequest, None)
            logging.info(f"processed {message}")
        
        return appcallback_v1.TopicEventResponse()

def main():
    server=grpc.server(futures.ThreadPoolExecutor(max_workers=2))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    appcallback_service_v1.add_AppCallbackServicer_to_server(Subscriber(), server)

    cert = open(r'certs\server.crt', 'rb').read()
    key = open(r'certs\server.key', 'rb').read()
    server_credentials = grpc.ssl_server_credentials(((key, cert,),))
    server.add_secure_port('[::]:50051', server_credentials)
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()