from typing import List


def load(
    hub,
    sources: List[str],
    cli: str = None,
    dyne_names: List[str] = None,
    loader: str = "yaml",
    parse_cli: bool = True,
    logs: bool = True,
):
    """
    Load up the configs from the integrate system
    """
    if not isinstance(sources, list):
        sources = [sources]

    # Load config from any project that has extended this place on the hub
    for source in hub.config.LOAD:
        if source not in sources:
            # Insert at the front of the list so that these are not authoritative
            sources.insert(0, source)

    if dyne_names is None:
        dyne_names = []
    raw = hub.config.dirs.load(sources, dyne_names, cli)
    os_vars = hub.config.os_vars.gather(raw)
    cli_args, raw_cli = hub.args.cli.gather(raw, cli, parse_cli)
    if cli_args.get("version"):
        hub.config.version.run(cli)
    configs = hub.config.file.parse(raw, cli, os_vars, cli_args, loader)

    opt = hub.config.order.apply(raw, raw_cli, cli, cli_args, os_vars, configs)
    # Sync pop-config with the log-level
    opt["pop_config"] = {
        k: opt[sources[0]][k] for k in opt["pop_config"] if k in opt[sources[0]]
    }

    # Perform checks against the compiled options
    hub.config.verify.sanitize(raw_cli, opt)

    # Output a config based on the current os and cli parameters
    if cli_args.get("config_template"):
        hub.config.template.run(opt)
    if cli_args.get("versions_report"):
        hub.config.versions_report.run(opt, cli, raw)

    hub.OPT = hub.pop.data.imap(opt)

    if logs:
        hub.log[hub.OPT.pop_config.log_plugin].setup(hub.OPT.pop_config)
