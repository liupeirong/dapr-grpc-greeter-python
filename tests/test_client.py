import helloworld_pb2
from google.protobuf import json_format

from client import publish_message;

def test_publish_message_serializes_request_to_json(mocker):
    # arrange
    request = helloworld_pb2.HelloRequest(name='foo')
    mock_publish_event = mocker.patch("client.DaprClient.publish_event", return_value=None)
    request_json = json_format.MessageToJson(request)

    # act
    publish_message(request)

    # assert
    mock_publish_event.assert_called_with(pubsub_name=mocker.ANY, topic_name=mocker.ANY, data=request_json, data_content_type='application/json')