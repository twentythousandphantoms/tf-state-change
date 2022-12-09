from typing import Dict, Any


class SchemaError(Exception):
    """Exception raised for field/key errors."""

    def __init__(self, *args) -> None:
        self.args = args

    def __str__(self) -> str:
        return str(self.args)


class DataNotFoundError(Exception):
    """Exception raised if data not found.
    Attributes:
        data
    """

    def __init__(self, data: Dict[str, Any]) -> None:
        self.data = data

    def __str__(self) -> str:
        return f"The resource {self.data!r} does not exists in the Terraform State!"


class TFStateChangeError(Exception):
    """Exception raised for other errors."""

    def __init__(self, *args) -> None:
        self.args = args

    def __str__(self) -> str:
        return str(self.args)
