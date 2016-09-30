import cfg_c

config = {
    "paths": {
        "database_dir": "database",
        "plugin_dir": "plugins"
    },
    "connection": {
        "server": "irc.chat.twitch.tv",
        "port": 443,                           # <- 6667 normal, 443 ssl
        "ssl": True,
        "nick_name": cfg_c.USER,
        "oauth_token": cfg_c.OAUTH,
        "channel": "lirik",
        "msg_decoding": "utf-8",
        "msg_encoding": "utf-8",
        "send_queue_empty_timeout": 1,
        "timeout_between_msg": (20 / 30),
        "receive_size_bytes": 4096,
        "auto_reconnect": True,
        "membership_messages": True,
        "tags": True,
        "commands": True
    },
    "general": {
        "join_msg": ".me up and running!",
        "depart_msg": ".me battery empty, leaving!",
        "silent_mode": True,
        "silent_in_other_channels": True,
        "lang_t2s": 'en'
    },
    "plugins": {
        # TODO Implement stuff below
        "load_plugins": True,
        "disable_cmd_execution": False,         # <- if on only cmd are being disabled
        "custom_load_order": [],
        "disabled_plugins": None,
    },
    "cron": {
        "cron_job_one": {
            "enabled": True,
            "channel": "own_channel",
            "interval": 10,                     # <- in sec
            "message": "Hello i am cron job one"
        },
        "cron_job_two": {
            "enabled": True,
            "ignore_silent_mode": False,
            "channel": "own_channel",
            "interval": 30,                     # <- in sec
            "message": "Hello i am cron job two"
        },
    }
}
