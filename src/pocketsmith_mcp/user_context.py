"""User context holder for auto-resolved user ID."""


class UserContext:
    """Holds the authenticated user ID, set by the server lifespan before tools run."""

    def __init__(self, user_id: int = 0) -> None:
        self._user_id = user_id

    @property
    def is_resolved(self) -> bool:
        return self._user_id != 0

    @property
    def user_id(self) -> int:
        if self._user_id == 0:
            raise RuntimeError(
                "user_id has not been resolved yet. "
                "The server lifespan must run before tools are called."
            )
        return self._user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        if not isinstance(value, int) or value <= 0:
            raise ValueError(
                f"user_id must be a positive integer, got {value}"
            )
        if self._user_id != 0:
            if self._user_id == value:
                return
            raise RuntimeError(
                "user_id has already been set and cannot be changed."
            )
        self._user_id = value
