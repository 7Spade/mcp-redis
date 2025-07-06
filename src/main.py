import sys
import os
import click

from src.common.connection import RedisConnectionManager
from src.common.server import mcp
import src.tools.server_management
import src.tools.misc
import src.tools.redis_query_engine
import src.tools.hash
import src.tools.list
import src.tools.string
import src.tools.json
import src.tools.sorted_set
import src.tools.set
import src.tools.stream
import src.tools.pub_sub
from src.common.config import MCP_TRANSPORT, parse_redis_uri, set_redis_env_from_config


class RedisMCPServer:
    def __init__(self):
        print("Starting the Redis MCP Server", file=sys.stderr)

    def run(self):
        mcp.run(transport=MCP_TRANSPORT)


@click.command()
@click.option('--url', help='Redis connection URI (redis://user:pass@host:port/db or rediss:// for SSL)')
@click.option('--host', default='127.0.0.1', help='Redis host')
@click.option('--port', default=6379, type=int, help='Redis port')
@click.option('--db', default=0, type=int, help='Redis database number')
@click.option('--username', help='Redis username')
@click.option('--password', help='Redis password')
@click.option('--ssl', is_flag=True, help='Use SSL connection')
@click.option('--ssl-ca-path', help='Path to CA certificate file')
@click.option('--ssl-keyfile', help='Path to SSL key file')
@click.option('--ssl-certfile', help='Path to SSL certificate file')
@click.option('--ssl-cert-reqs', default='required', help='SSL certificate requirements')
@click.option('--ssl-ca-certs', help='Path to CA certificates file')
@click.option('--cluster-mode', is_flag=True, help='Enable Redis cluster mode')
@click.option('--mcp-transport', default='stdio', type=click.Choice(['stdio', 'streamable-http', 'sse']), help='MCP transport method')
@click.option('--mcp-host', default='127.0.0.1', help='MCP server host (for http/sse transport)')
@click.option('--mcp-port', default=8000, type=int, help='MCP server port (for http/sse transport)')
def cli(url, host, port, db, username, password,
        ssl, ssl_ca_path, ssl_keyfile, ssl_certfile,
        ssl_cert_reqs, ssl_ca_certs, cluster_mode,
        mcp_transport, mcp_host, mcp_port):
    """Redis MCP Server - Model Context Protocol server for Redis."""

    # Handle Redis URI if provided
    if url:
        try:
            uri_config = parse_redis_uri(url)
            set_redis_env_from_config(uri_config)
        except ValueError as e:
            click.echo(f"Error parsing Redis URI: {e}", err=True)
            sys.exit(1)
    else:
        # Set individual Redis parameters
        config = {
            'host': host,
            'port': port,
            'db': db,
            'ssl': ssl,
            'cluster_mode': cluster_mode
        }

        if username:
            config['username'] = username
        if password:
            config['password'] = password
        if ssl_ca_path:
            config['ssl_ca_path'] = ssl_ca_path
        if ssl_keyfile:
            config['ssl_keyfile'] = ssl_keyfile
        if ssl_certfile:
            config['ssl_certfile'] = ssl_certfile
        if ssl_cert_reqs:
            config['ssl_cert_reqs'] = ssl_cert_reqs
        if ssl_ca_certs:
            config['ssl_ca_certs'] = ssl_ca_certs

        set_redis_env_from_config(config)

    # Set MCP transport settings
    os.environ['MCP_TRANSPORT'] = mcp_transport
    os.environ['MCP_HOST'] = mcp_host
    os.environ['MCP_PORT'] = str(mcp_port)

    # Start the server
    server = RedisMCPServer()
    server.run()


def main():
    """Legacy main function for backward compatibility."""
    server = RedisMCPServer()
    server.run()


if __name__ == "__main__":
    main()
