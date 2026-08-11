class MoveonError(Exception):
    pass


class ParseError(MoveonError):
    pass


class BundleError(MoveonError):
    pass


class ManifestError(MoveonError):
    pass
