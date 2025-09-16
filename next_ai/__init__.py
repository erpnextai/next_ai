import warnings
import os

VERSION = {
    'default': '0.0.1',
    'main': '0.0.1-nightly',
    'dev': '0.0.1-dev',
    'version-14': '14.2.1',
    'version-15': '15.2.1'
}

try:
    from git import Repo
    repo = Repo(os.path.abspath(__file__), search_parent_directories=True)
    branch = repo.active_branch.name.lower()
    __version__ = VERSION.get(branch, VERSION['default'])
except Exception as e:
    __version__ = VERSION['default']
    warnings.warn(f"Error getting git branch: {str(e)}", category=RuntimeWarning)
