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
        "client_id": cfg_c.CLIENT,
        "channel": "lirik",
        "msg_decoding": "utf-8",
        "msg_encoding": "utf-8",
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
        "only_silent_in_other_channels": False,
    },
    "plugins": {
        "load_plugins": True,
        "custom_load_order": ["gui_user_input"],    # <- loads those plugins in order first then the others found
        "disabled_plugins": ["display_raw", ""],
    },
    "plugin_settings": {
        "lang_t2s": 'en',
        "enable_gui_messages": False,
    },
    "currency": {
        "enabled": False,
        "interval": 60,                        # <- in sec
        "amount": 1,
        "message": "I'm laughing straight to the bank with this (Ha, ha ha ha ha ha, ha, ha ha ha ha ha)"
    },
    "cron": {
        "cron_job_one": {
            "enabled": False,
            "channel": "own_channel",
            "interval": 10,                     # <- in sec
            "message": "Hello i am cron job one"
        },
        "cron_job_two": {
            "enabled": False,
            "ignore_silent_mode": False,
            "channel": "own_channel",
            "interval": 30,                     # <- in sec
            "message": "Hello i am cron job two"
        },
    }
}
