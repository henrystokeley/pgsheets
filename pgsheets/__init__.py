"""Package for representing and modifying Google Sheets using Panda DataFrames.

The Spreadsheet class represents a Google Spreadhsheet and can be used to
access worksheets.

The Client and Token objects are used for authentication with Google's API
"""

from pgsheets.token import Client, Token
from pgsheets.models import Spreadsheet

__version__ = '0.0.1'
