import asyncio
import sys
import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class RealMCPClient:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()

    async def connect(self):
        """Inicia o subprocesso do servidor e estabelece conexão MCP."""
        # Define como rodar o servidor (o arquivo que criamos acima)
        server_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        
        server_params = StdioServerParameters(
            command=sys.executable, # Usa o mesmo python do venv
            args=[server_script],
            env=None
        )

        # Estabelece o transporte (stdio) e a sessão
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.session = await self.exit_stack.enter_async_context(ClientSession(stdio_transport[0], stdio_transport[1]))
        
        await self.session.initialize()
        print("   🔌 [MCP CLIENT] Conectado ao servidor de ferramentas via STDIO.")

    async def call_tool(self, tool_name, arguments):
        """Envia uma mensagem JSON-RPC para o servidor executar a tool."""
        if not self.session:
            await self.connect()
        
        # Chama a ferramenta usando o protocolo oficial
        result = await self.session.call_tool(tool_name, arguments=arguments)
        
        # O MCP retorna uma lista de conteúdos (texto, imagem, etc). Pegamos o texto.
        return result.content[0].text

    async def close(self):
        await self.exit_stack.aclose()