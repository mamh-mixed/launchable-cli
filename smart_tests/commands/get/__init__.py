from ... import args4p
from ...app import Application
from .api_schema import api_schema
from .docs import docs


@args4p.group(help="Retrieve resources")
def get(app: Application):
    return app


get.add_command(api_schema)
get.add_command(docs)
