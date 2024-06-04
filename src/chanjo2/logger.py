import logging

import uvicorn

LOG = logging.getLogger("uvicorn.access")


console_formatter = uvicorn.logging.ColourizedFormatter(
    "{levelprefix} {asctime} : {message}", style="{", use_colors=True
)
if LOG.handlers:
    LOG.handlers[0].setFormatter(console_formatter)
else:
    logging.basicConfig()
