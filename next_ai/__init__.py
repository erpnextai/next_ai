import warnings
import os

VERSION = {
    'default': '0.0.1',
    'main': '-Nightly',
    'dev': '-Dev',
    'version-14': '14.2.1',
    'version-15': '15.2.1'
}


try:
    from git import Repo

    file_path = os.path.abspath(__file__)
    repo = Repo(file_path, search_parent_directories=True)
    branch = repo.active_branch.name
    version = VERSION.get(branch.lower(), VERSION['default'])
except Exception as e:
    version = VERSION['default']
    warnings.warn(f"Error getting git branch: {str(e)}", category=RuntimeWarning)


__version__ = version