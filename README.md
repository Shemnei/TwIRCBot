Highly modular Twitch Bot
=========================

STATUS: WORKING / IN DEVELOPMENT
________________________________

Readme coming soon for now look into /src/plugins for example usage

NYI:

- database for users (for keeping track of permission_level or points etc...)
- tag parsing for default plugins
- cfg -> silent_in_other_channels
- cfg -> lang_t2s
- cfg -> load_plugins
- cfg -> disable_cmd_execution
- cfg -> custom_load_order
- cfg -> disabled_plugins

Errors:
    -> Windows CMD Encoding: if UnicodeEncodeError ->
        - Set cmd font to font supporting utf-8 and type chcp 65001(changing cmd codec to utf-8) into cmd before running bot
        - Working on fix