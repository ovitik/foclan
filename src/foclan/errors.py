import builtins


class FocusLangError(Exception):
    """Base class for focus language errors."""


class ParseError(FocusLangError):
    pass


class UnknownOp(FocusLangError):
    pass


class UnknownBranch(FocusLangError):
    pass


class UnknownLabel(FocusLangError):
    pass


class DuplicateBranch(FocusLangError):
    pass


class DuplicateLabel(FocusLangError):
    pass


class InvalidBackTarget(FocusLangError):
    pass


class InvalidMerge(FocusLangError):
    pass


class TypeError(FocusLangError, builtins.TypeError):
    pass


class RuntimeError(FocusLangError, builtins.RuntimeError):
    pass
