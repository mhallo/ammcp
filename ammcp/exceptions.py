class MusicControlError(RuntimeError):
    """Raised when Music.app can't be controlled via JXA (app not running, permission denied, target not found)."""
