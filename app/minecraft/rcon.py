from mcrcon import MCRcon

from app.settings import RCON_HOST, RCON_PASSWORD, RCON_PORT


class RconClient:
    def __init__(self, host: str = None, password: str = None, port: int = None):
        self.rcon = MCRcon(host or RCON_HOST, password or RCON_PASSWORD, port or RCON_PORT)        

    def send(self, command: str):
        """Send a command to the RCON server."""
        response = None
        
        try:
            self.rcon.connect()
            response = self.rcon.command(command)
        except Exception as e:
            return f"Error: {e}"
        finally:
            self.rcon.disconnect()

        return response
