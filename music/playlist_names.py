"""
Display names for special playlist tags.

Any tag not listed here will automatically be formatted using:
    tag.replace("_", " ").title()

Examples:
    jersey_club -> Jersey Club
    future_funk -> Future Funk
"""

DISPLAY_NAME_OVERRIDES = {
    # Artists
    "newjeans": "NewJeans",
    "le_sserafim": "LE SSERAFIM",
    "loona": "LOONA",

    # Genres / Collections
    "kpop": "K-Pop",
    "uk_garage": "UK Garage",
    "jersey_club": "Jersey Club",
    "future_funk": "Future Funk",

    # Add future special cases here.
    # Examples:
    # "rnb": "R&B",
    # "dnb": "DnB",
    # "edm": "EDM",
}


def playlist_display_name(tag: str) -> str:
    """
    Convert an internal playlist tag into a display name.

    Examples
    --------
    newjeans     -> NewJeans
    uk_garage    -> UK Garage
    future_funk  -> Future Funk
    remix        -> Remix
    night_drive  -> Night Drive
    """

    if tag in DISPLAY_NAME_OVERRIDES:
        return DISPLAY_NAME_OVERRIDES[tag]

    return tag.replace("_", " ").title()
