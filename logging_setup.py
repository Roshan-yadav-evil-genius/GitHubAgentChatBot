from rich.logging import RichHandler
from logging import Formatter,FileHandler
import logging

console_formatter = Formatter("%(message)s")
console_handler = RichHandler(rich_tracebacks=True, markup=True)
console_handler.setFormatter(console_formatter)


logging.basicConfig(level=logging.DEBUG,handlers=[
    console_handler
])