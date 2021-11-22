import asyncio
import websockets

class MultiEARWebsocket():

  """
  Class MultiEARWebsocket
  Wrapper for broadcasting data over the HTML5 Websocket protocol
  
  Author: Mathijs Koymans, 2021
  """

  def __init__(self):

    """
    Def MultiEARWebsocket.__init__
    Instantiates the MultiEARWebsocket by creating an empty set of clients
    """

    self.clients = set()


  def listen(self, host, port):

    """
    Def MultiEARWebsocket.listen
    Wrapper around asyncio run_until_complete
    """

    self.host = host
    self.port = port

    # Start the websocket server
    self.__complete(websockets.serve(self.handler, self.host, self.port))


  def broadcast(self, serialized):

    """
    Def MultiEARWebsocket.broadcast
    Update function called once in a while to draw new data from the database
    """

    self.__complete(self.__broadcast(serialized))


  def __complete(self, callback):

    """
    Def MultiEARWebsocket.__complete
    Wrapper around asyncio run_until_complete
    """

    asyncio.get_event_loop().run_until_complete(callback)


  async def __broadcast(self, serialized):
  
    """
    Def MultiEARWebsocket.__broadcast
    Private function to broadcast the serialized buffer to all clients
    """
  
    # Await writing to all clients (this is asynchronous)
    try:
      await asyncio.gather(
         *[ws.send(serialized) for ws in self.clients]
      ) 
    except websockets.ConnectionClosedOK:
      pass
  
  
  async def handler(self, websocket, path):

    """
    Def MultiEARWebsocket.handler
    Callback fired when a client is connected: ignore incoming messages and only keep track of connected clients
    """
    
    # Save a list of the clients
    self.clients.add(websocket)
    
    try:
      async for msg in websocket:
        pass
    except websockets.ConnectionClosedError:
      pass
    finally:
      self.clients.remove(websocket)


if __name__ == '__main__':

  """
  Def __name__
  Only fired when direct execution of script
  """

  # Create and listen
  M = MultiEARWebsocket()
  M.listen("localhost", 8765)

  while True:
    M.broadcast("1");
 