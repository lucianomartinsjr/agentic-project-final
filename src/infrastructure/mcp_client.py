import sys
import os
import contextlib
import asyncio
import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPToolTimeoutError(TimeoutError):
    pass

class RealMCPClient:
    def __init__(self, *, init_timeout_s: float = 10.0, tool_timeout_s: float = 10.0):
        self.session = None
        self.init_timeout_s = float(os.environ.get("MCP_INIT_TIMEOUT_S", init_timeout_s))
        self.tool_timeout_s = float(os.environ.get("MCP_TOOL_TIMEOUT_S", tool_timeout_s))

    @contextlib.asynccontextmanager
    async def run_session(self):
        server_script = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        
        env = os.environ.copy()
        current_dir = os.getcwd()
        env["PYTHONPATH"] = current_dir + os.pathsep + env.get("PYTHONPATH", "")
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
            env=env 
        )

        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    try:
                        await asyncio.wait_for(session.initialize(), timeout=self.init_timeout_s)
                    except asyncio.TimeoutError as e:
                        raise TimeoutError(
                            f"Timeout ao inicializar sessão MCP após {self.init_timeout_s:.1f}s"
                        ) from e
                    self.session = session
                    yield 
        except Exception as e:
            print(f"\n❌ ERRO NO SUBPROCESSO MCP: {e}")
            print(f"Dica: Verifique se o arquivo {server_script} existe e se as importações nele estão corretas.\n")
            raise e
        finally:
            self.session = None

    async def call_tool(self, tool_name, arguments):
        if not self.session:
            raise RuntimeError("Sessão MCP fechada ou não iniciada.")

        timeout = datetime.timedelta(seconds=float(self.tool_timeout_s))
        try:
            result = await self.session.call_tool(
                tool_name,
                arguments=arguments,
                read_timeout_seconds=timeout,
            )
        except TimeoutError as e:
            raise MCPToolTimeoutError(
                f"Timeout chamando tool '{tool_name}' após {self.tool_timeout_s:.1f}s"
            ) from e
        
        if not result.content:
            return "Erro: Retorno vazio da ferramenta."
            
        return result.content[0].text