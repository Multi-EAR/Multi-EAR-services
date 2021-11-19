import asyncio
import numpy as np
import websockets
import json
from influxdb_client import InfluxDBClient

class MultiEARWebsocket():

  """
  Class MultiEARWebsocket
  Wrapper for Python websocket that broadcasts data to connect clients
  """

  HOST = ("localhost", 8765)
  TICK_RATE_SECONDS = 2


  def __init__(self):

    """
    Def MultiEARWebsocket.__init__
    Initializes the websocket server and keeps track of periodically updated clients & data
    """

    # Open client
    self.db_client = InfluxDBClient(url="http://127.0.0.1:8086", token="ear:listener", org="-")

    # Keep track of the connected clients
    self.clients = set()
    self.data = None

    self.broadcast()


  @property
  def _q(self):
    return None


  def broadcast(self):

    """
    Def MultiEARWebsocket.broadcast
    Begins broadcasting incoming data over the websocket
    """

    stream = self.db_client.request(self._q, stream=True):

    for line in stream.iter_lines():

      serialized = json.dumps(line)

      for websocket in self.clients:
        websocket.send(serialized)


  def run(self):

    """
    Def MultiEARWebsocket.run
    Starts the main loop of the websocket server (this will run indefinitely)
    """

    asyncio.run(self.main())


  def update(self):

    """
    Def MultiEARWebsocket.update
    Update function called once in a while to draw new data from the database
    """

    self.data = None
  
  async def handler(self, websocket, path):
  
    """
    Def MultiEARWebsocket.handler
    Callback fired when a client is connected: ignore incoming messages and only keep track of connected clients
    """

    self.clients.add(websocket)
  
    try:
      async for msg in websocket:
        pass
    except websockets.ConnectionClosedError:
      pass
    finally:
      self.clients.remove(websocket)
  
  
  async def main(self):
  
    """
    Def MultiEARWebsocket.main
    Main function to schedule events and create websocket listener
    """

    async with websockets.serve(self.handler, *self.HOST):
      await asyncio.Future()  # run forever


if __name__ == "__main__":

  """
  Def __main__
  Only executed when script is called directly
  """

  WebsocketServer = MultiEARWebsocket()
  WebsocketServer.run()