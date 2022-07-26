# A sample Dapr grpc server and pubsub subscriber, and a grpc client and pubsub publisher

This sample builds on top of the [helloworld grpc sample](https://github.com/grpc/grpc/tree/master/examples/python/helloworld) to enable the following capabilities:
* The grpc service runs with SSL.
* Both the grpc client and the server can run with or without Dapr.
* The server and the client also act as a Dapr pubsub subscriber and publisher respectively.
* F5 debugging is enabled when running with or without Dapr.

## How is it different from a regular grpc server/client?
* With `proxy.grpc` support in Dapr, existing grpc service code doesn't have to be changed for a Dapr client to call. The only required change is to add `proxy.grpc` in `.dapr/config.yaml` as shown in the following sample:

```yaml
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: daprConfig
spec:
  tracing:
    samplingRate: "1"
    zipkin:
      endpointAddress: http://localhost:9411/api/v2/spans
  features:
    - name: proxy.grpc
      enabled: true
```

__To support pubsub message handling__ though, there are two options:
1. Use [Dapr Python SDK grpc extension](https://github.com/dapr/python-sdk/tree/master/ext/dapr-ext-grpc), or,
2. Add another grpc servicer that inherits from `appcallback_service_v1.AppCallbackServicer` and overrides its virtual methods `ListTopicSubscriptions` and `OnTopicEvent` as shown in the  [server](./server.py).

In this example, we chose #2 because grpc extension adds an existing grpc service to a Dapr grpc service using `add_insecure_port`. At the time of this writing, [it doesn't appear to support secure port yet](https://github.com/dapr/python-sdk/blob/master/ext/dapr-ext-grpc/dapr/ext/grpc/app.py#L61). This means if your existing Dapr server and client are communicating over SSL, with this change, your existing client can no longer talk to the server. You'll have to use a Dapr client to talk to its sidecar without SSL. 

For pubsub, you also need to deserialize the message yourself. To reuse the existing grpc method as the message handler as much as possible, you might want to deserialize the message to the same protobuf request the grpc method takes. To avoid SeDer incomptibility between grpc and dapr, we use protobuf `json_formatter` to serialize and deserialize the message.

## How to run and debug the service?
### Enable SSL
For debugging, you could change the code to use `grpc.local_channel_credentials` in the client and `grpc.local_sever_credentials` in the server to run with SSL. If you want to use certificate, run the following command to generate self-signed certificates.

```bash
# create a folder certs in the project folder
mkdir certs
cd certs
openssl req -newkey rsa:2048 -nodes -x509 -days 3650 -keyout server.key -out server.crt -subj "/CN=contoso.local"
```

If you already have a certificate, use the following command to generate the server cert and key. The root CA of the cert must be trusted.

```bash
# create a folder certs in the project folder
mkdir certs
cd certs
openssl pkcs12 -in ${EXISTING_CERT}.pfx -nocerts -nodes -passin pass:${PASSCODE} | openssl pkcs8 -nocrypt -out server.key
openssl pkcs12 -in ${EXISTING_CERT}.pfx -nokeys -passin pass:${PASSCODE} | openssl x509 -out server.crt
```

### Configure Dapr
* Install Dapr in your environment. Update `.dapr/config.yaml` to enable `proxy.grpc` as mentioned above.
* The [client](./client.py) publishes messages to a Dapr pubsub component called `mqtt-pubsub`. You can change it to any pubsub component. Make sure you have it installed, for example, it can be a [Redis Streams](https://docs.dapr.io/reference/components-reference/supported-pubsub/setup-redis-pubsub/). 
* Add a Dapr Subscription to declaratively route messages. For example, 

```yaml
apiVersion: dapr.io/v1alpha1
kind: Subscription
metadata:
  name: subscription-greeter
spec:
  topic: greeter
  pubsubname: mqtt-pubsub
scopes:
- greeter
```

### Run the server
* If you use certificates, make sure to put `server.key` and `server.crt` generated above in a folder called `certs`.
* To run the server without Dapr, it's simply `python server.py`.
* To run the server with Dapr, assuming port 50051 that the server is hardcoded to run on isn't changed:

```bash
dapr run --app-id greeter --app-port 50051 --app-protocol grpc --app-ssl -- python server.py
```

* To debug in vscode, make sure the task `daprd-debug-server` in [tasks.json](.vscode/tasks.json) has the correct `appPort`. Choose `Server Dapr Python` profile and hit F5 to debug. When you are done, the `daprd` and `daprd-down` tasks started by vscode are not closed. You should be able to hit return in those terminals to close them.


### Run the client
* Whether the server is running with or without Dapr, you can run the client to invoke grpc service without Dapr, although you can't publish messages without Dapr since pubsub is a Dapr feature:

```bash
python client.py 1
```


* To call grpc service with Dapr, the server must already be running with Dapr, run the following command to start the client:

```bash
dapr run --app-id greeter-client -- python client.py 1 
```

To debug, choose `Client Dapr Python` profile and F5. When the app finishes running, the `daprd` and `daprd-down` tasks started by vscode are not closed. You should be able to hit return in those terminals to close them. 

* To publish message to pubsub broker:

```bash
dapr run --app-id greeter-client -- python client.py 
```
