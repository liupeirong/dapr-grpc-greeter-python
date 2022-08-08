from google.protobuf import json_format
import helloworld_pb2
from server import Greeter, Subscriber
from dapr.proto import appcallback_v1

def test_SayHello_returns_name():
    # arrange
    req = helloworld_pb2.HelloRequest(name='foo')
    greeter = Greeter()

    # act
    resp = greeter.SayHello(req, None)

    # assert
    assert isinstance(resp, helloworld_pb2.HelloReply)
    assert 'foo' in resp.message


def test_OnTopicEvent_calls_SayHello_with_Deserialized_request(mocker):
    # arrange
    hello_req = helloworld_pb2.HelloRequest(name='foo')
    hello_req_json = json_format.MessageToJson(hello_req)
    topic_event_req = appcallback_v1.TopicEventRequest(topic='greeter', data=hello_req_json.encode('utf8'))
    mock_SayHello = mocker.patch("server.Greeter.SayHello", return_value=None)
    subscriber = Subscriber()

    # act
    subscriber.OnTopicEvent(topic_event_req, None)

    # assert
    mock_SayHello.assert_called_with(hello_req, None)