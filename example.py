#!/usr/bin/env python3

# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Ian Pilcher <arequipeno@gmail.com>


"""Example tsarp usage: a fictional server management utility."""


import tsarp


def _parse_port(s: str) -> int:
    n = int(s)
    if not (1 <= n <= 65535):
        raise ValueError(f"invalid port number: {n}")
    return n

PORT = tsarp.Type("port", _parse_port)


class StartCmd(
    tsarp.Schema,
    custom_types=(PORT,),
    description="Start the server process"
):

    conn = tsarp.group(title="Connection options")
    logging = tsarp.group(title="Logging options")

    host: str = tsarp.param(help="Hostname or address to bind")
    port: int = tsarp.opt(
        type=PORT, default=8080, short="-p", group="conn",
        help="TCP port to listen on"
    )
    daemon: bool = tsarp.flag(short="-d", help="Daemonize after startup")
    log_level: str = tsarp.opt(
        default="info", choices=["debug", "info", "warning", "error"],
        group="logging", help="Log verbosity level"
    )


class StopCmd(tsarp.Schema, description="Stop the server process"):

    shutdown_mode = tsarp.mxgroup()

    host: str = tsarp.param(help="Hostname or address of the running server")
    timeout: int = tsarp.opt(
        default=30, help="Seconds to wait before giving up"
    )
    force: bool = tsarp.flag(
        group="shutdown_mode", short="-f",
        help="Kill immediately without waiting"
    )
    graceful: bool = tsarp.flag(
        group="shutdown_mode", help="Wait for active connections to close"
    )


class StatusCmd(tsarp.Schema, description="Report server status"):

    host: str = tsarp.param(help="Hostname or address of the server to query")
    format: str = tsarp.opt(
        default="text", choices=["text", "json"], short="-f",
        help="Output format"
    )


class Srvctl(
    tsarp.Schema,
    description="Server control utility",
    epilog="Run 'srvctl COMMAND --help' for command-specific help."
):
    verbose: bool = tsarp.flag(short="-v", help="Enable verbose output")
    command: str | None = tsarp.subcommands(title="commands", required=True)
    start: StartCmd | None = tsarp.subcmd(StartCmd)
    stop: StopCmd | None = tsarp.subcmd(StopCmd)
    status: StatusCmd | None = tsarp.subcmd(StatusCmd)


if __name__ == "__main__":

    args = tsarp.parse(Srvctl)

    if args.verbose:
        print("[verbose mode]")

    match args.command:
        case "start":
            assert args.start is not None
            print(f"Starting server on {args.start.host}:{args.start.port}")
            if args.start.daemon:
                print("  (daemonizing)")
            print(f"  log level: {args.start.log_level}")

        case "stop":
            assert args.stop is not None
            print(f"Stopping server at {args.stop.host}")
            if args.stop.force:
                print("  (forced kill)")
            elif args.stop.graceful:
                print("  (waiting for connections to close)")
            else:
                print(f"  (timeout: {args.stop.timeout}s)")

        case "status":
            assert args.status is not None
            print(f"Querying {args.status.host} [{args.status.format}]")


# kate: tab-width 8; indent-width 4; replace-tabs on;
