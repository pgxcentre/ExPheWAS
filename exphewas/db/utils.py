"""
Utilities for the SQLAlchemy ORM or for other database related matters.
"""

def mod_to_dict(o):
    """Introspects a model to convert it to a regular Python dict."""
    keys = o.__table__.columns.keys()
    return {k: getattr(o, k) for k in keys}
