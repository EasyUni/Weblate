# Copyright © Yunhan <elitetai2006@gmail.com>
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Config file for gunicorn, supposed to be run by systemd.

import logging
import os
from logging import LogRecord
from typing import cast


def is_bot(user_agent: str):
    bot_ids = (
        "SemrushBot",
        "DataForSeoBot",
        "bingbot",
        "YandexBot",
        "AhrefsBot",
        "DotBot",
        "PetalBot",
        "EzLynx",
        "Googlebot",
        "Amazonbot",
        "MJ12bot",
        "Sogou web spider",
    )
    return any(s in user_agent for s in bot_ids)


class BotIgnoreFilter(logging.Filter):
    def filter(self, record: LogRecord) -> bool:
        passed = super().filter(record)
        # Ref: https://docs.gunicorn.org/en/stable/settings.html#access-log-format
        user_agent = (
            cast(str, record.args["a"]) if isinstance(record.args, dict) else ""
        )
        from_bot = is_bot(user_agent)
        return bool(passed) and not from_bot


proc_name = "weblate-web"
worker_tmp_dir = "/dev/shm/"
# Production server should configure worker number in systemd service file,
# because this file is shared.


# Use systemd's RuntimeDirectory when available, otherwise a hidden file in CWD.
runtime_dir = os.getenv("RUNTIME_DIRECTORY")
if runtime_dir:
    control_socket = runtime_dir + "/gunicorn.ctl"
else:
    control_socket = os.getcwd() + "/.gunicorn.ctl"

# Make short log line. Some info is discarded, because it is shown by journalctl already.
logconfig_dict = {
    "formatters": {
        "generic": {
            "format": "[%(levelname)s] %(message)s",
        }
    },
    "loggers": {
        "gunicorn.error": {
            "level": "INFO",
            "handlers": ["error_console"],
            "propagate": False,
            "qualname": "gunicorn.error",
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
            "qualname": "gunicorn.access",
        },
    },
}


# Ref: https://stackoverflow.com/a/68824216/502780
def on_starting(server):
    server.log.access_log.addFilter(BotIgnoreFilter())
