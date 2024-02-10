import os

from betamax import Betamax

with Betamax.configure() as config:
    config.cassette_library_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "cassettes"
    )
    config.default_cassette_options["record_mode"] = "once"
