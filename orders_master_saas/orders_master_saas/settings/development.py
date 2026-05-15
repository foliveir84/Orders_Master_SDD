"""
Development settings for orders_master_saas project.

Import all base settings and override for local development.
"""

from .base import *  # noqa: F401,F403

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]