from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
import urllib
import re

import requests
import pandas as pd

from pgsheets.exceptions import _check_status, PGSheetsValueError


def _ns_w3(name):
    return '{http://www.w3.org/2005/Atom}' + name


def _ns_sheet(name):
    return '{http://schemas.google.com/spreadsheets/2006}' + name


def _get_first(elements, prop, equal):
    for e in elements:
        if e.get(prop) == equal:
            return e
    raise ValueError('missing element')


class Worksheet():
    """Represents a single Spreadsheet's worksheet.

    Do not initialize manually, instead retrieve from a Spreadsheet object.
    """

    def __init__(self, token, element, **kwargs):
        self._element = element
        self._token = token
        super().__init__(**kwargs)

    def _getFeed(self):
        self_uri = _get_first(
            self._element.findall(_ns_w3('link')), 'rel', 'self').get('href')
        r = requests.get(self_uri,
                         headers=self._token.getAuthorizationHeader())
        _check_status(r)
        self._element = ElementTree.fromstring(r.content.decode())
        return self._element

    def _resize(self, feed, rows=None, cols=None):
        if cols is None and rows is None:
            return
        edit_uri = _get_first(
            feed.findall(_ns_w3('link')), 'rel', 'edit').get('href')

        if cols is not None:
            feed.find(_ns_sheet('colCount')).text = str(cols)
        if rows is not None:
            feed.find(_ns_sheet('rowCount')).text = str(rows)

        if (int(feed.find(_ns_sheet('colCount')).text)
                * int(feed.find(_ns_sheet('rowCount')).text)
                > 2000000):
            raise PGSheetsValueError(
                "No sheet may be more than 2000000 cells large"
                )

        r = requests.put(
            edit_uri,
            data=ElementTree.tostring(feed),
            headers=self._token.getAuthorizationHeader(
                {'content-type': 'application/atom+xml'}))
        _check_status(r)

    def _getTitle(self, feed):
        """Calling with feed=self._element will get the title at the
        time of retrieval
        """
        return feed.find(_ns_w3('title')).text

    def getTitle(self):
        """Get the title of this individual worksheet (not the title of the
        spreadsheet).

        This involves calling the Google API.
        """
        # title may have changed so use the latest information
        return self._getTitle(self._getFeed())

    def _getId(self):
        return self._element.find(_ns_w3('id')).text.split('/')[-4]

    def resizeToAtLeast(self, rows=None, cols=None):
        """Ensures a minimum size of the sheet.

        Setting row=None or cols=None ignores that axis.
        """
        if rows is None and cols is None:
            return
        # get the current size
        feed = self._getFeed()

        f_cols, f_rows = (
            int(feed.find(_ns_sheet('colCount')).text),
            int(feed.find(_ns_sheet('rowCount')).text),
            )
        if rows is None or rows <= f_rows:
            rows = None
        if cols is None or cols <= f_cols:
            cols = None
        self._resize(feed, rows, cols)

    def resize(self, rows=None, cols=None):
        """Resizes one or both of the sheet's axes.

        Setting row=None or cols=None ignores that axis.
        Data outside of the new dimensions will be deleted.
        """
        if rows is None and cols is None:
            return
        feed = self._getFeed()
        self._resize(feed, rows, cols)

    def asDataFrame(self, set_index=True, set_columns=True, values=False):
        """Returns a DataFrame representation of the sheet

        The index/column names are the row/column numbers, unless set_index or
        set_columns is set respectively

        Setting values=True returns the values of the cell, reather than a
        formula.

        Currently all values are returned as a string.
        """
        cell_feed_uri = (
            _get_first(self._element.findall(_ns_w3('link')), 'rel',
                       'http://schemas.google.com/spreadsheets/2006#cellsfeed')
            .get('href')
            )
        r = requests.get(
            cell_feed_uri, headers=self._token.getAuthorizationHeader())
        _check_status(r)
        cell_feed = ElementTree.fromstring(r.content.decode())

        df = pd.DataFrame()
        for cell in cell_feed.findall(_ns_w3('entry')):
            gs = cell.find(_ns_sheet('cell'))
            if values:
                content = list(gs.itertext())[0]
            else:
                content = gs.get('inputValue')
            column = int(gs.get('col'))
            row = int(gs.get('row'))

            df.loc[row, column] = content

        # fill in blanks and order
        if len(df):
            df = df.reindex(columns=list(range(1, max(df.columns)+1)))
            df = df.reindex(list(range(1, max(df.index)+1)))

            if set_columns:
                df.columns = df.iloc[0]
                df = df.drop(1)
            if set_index and len(df):
                df.index = df[df.columns[0]]
                del df[df.columns[0]]
                if not set_columns:
                    df.index.name = ""

            # we use the index name, not the columns name
            df.columns.name = ""

        return df

    def setDataFrame(self,
                     df,
                     x_pos=1,
                     y_pos=1,
                     copy_index=True,
                     copy_columns=True,
                     resize=False,
                     escape_formulae=False,
                     ):
        """Sets the values of a given DataFrame at x_pos, y_pos

       Currently does not support multiindexed DataFrame objects

        * resize
            Forces the bottom right of the spreadhseet to be the bottom
            right of this DataFrame.
            If the DataFrame is bigger than the spreadsheet it will be resized
            irrespective of this variable.
        * escape_formulae
            If any text starts with an equals sign =, it will be prefixed with
            a apostrophe ', to avoid being interpreted as a formula.

        Note:
            A Google Spreadsheet may not (as of July 2015) have more than
            2,000,000 cells.

            The name of the columns is never copied.
            The name of the index is copied if both copy_index=True and
            copy_columns=True
        """
        # x_pos, y_post is the position of the data, excluding any columns
        y, x = df.shape
        if copy_index is True:
            x_pos += 1
        if copy_columns is True:
            y_pos += 1
        if resize:
            self.resize(y + y_pos - 1, x + x_pos - 1)
        else:
            self.resizeToAtLeast(y + y_pos - 1, x + x_pos - 1)

        updates = []

        def update(up):
            updates.append(up)

        def str_repr(data):
            """Get a representation of 'data' for a cell"""
            if pd.isnull(data):
                return ""
            data = str(data)
            if escape_formulae and data and data[0] == "=":
                data = "'{}".format(data)
            return str(data)

        if copy_columns:
            for i, col in enumerate(df.columns):
                update((y_pos - 1, x_pos+i, str_repr(col)))
        if copy_index:
            for i, col in enumerate(df.index):
                update((i+y_pos, x_pos-1, str_repr(col)))
        if copy_columns and copy_index:
            update((y_pos-1, x_pos-1, str_repr(df.index.name)))

        for i, row in enumerate(df.values):
            for j, v in enumerate(row):
                update((i+y_pos, j+x_pos, str_repr(v)))

        self._addCells(updates)

    def _addCells(self, cells):
        """Updates the referenced cells. *cells* is a list of tuples:
            (row, col, content)
        """
        if len(cells) == 0:
            return
        feed = Element('feed', {
            'xmlns': 'http://www.w3.org/2005/Atom',
            'xmlns:batch': 'http://schemas.google.com/gdata/batch',
            'xmlns:gs': 'http://schemas.google.com/spreadsheets/2006',
            })

        id_elem = SubElement(feed, 'id')
        id_elem.text = (
            _get_first(self._element.findall(_ns_w3('link')), 'rel',
                       'http://schemas.google.com/spreadsheets/2006#cellsfeed')
            .get('href')
            )

        def add_entry(feed, row, col, content):
            code = 'R{}C{}'.format(row, col)
            entry = SubElement(feed, 'entry')
            SubElement(entry, 'batch:id').text = code
            SubElement(entry, 'batch:operation', {'type': 'update'})
            SubElement(entry, 'id').text = id_elem.text + '/' + code
            SubElement(entry, 'link', {
                'rel': 'edit',
                'type': "application/atom+xml",
                'href': id_elem.text + '/' + code})

            SubElement(entry, 'gs:cell', {
                'row': str(row),
                'col': str(col),
                'inputValue': content})

        for row, col, content in cells:
            add_entry(feed, row, col, content)

        data = ElementTree.tostring(feed)

        r = requests.post(
            id_elem.text + '/batch',
            data=data,
            headers=self._token.getAuthorizationHeader({
                'Content-Type': 'application/atom+xml', 'If-Match': '*'}))

        _check_status(r)

    def __repr__(self):
        return "<{cls} title={title!r} id={id_!r}>".format(
            cls=self.__class__.__name__,
            title=self._getTitle(self._element),
            id_=self._getId())


class _BaseSpreadsheet():
    def __init__(self, token, element, **kwargs):
        self._token = token
        self._element = element
        super().__init__(**kwargs)

    def getKey(self):
        return self._element.find(_ns_w3('id')).text.split('/')[-1]

    def getTitle(self):
        return self._element.find(_ns_w3('title')).text

    def getURL(self):
        return (_get_first(self._element.findall(_ns_w3('link')),
                           'rel',
                           'alternate')
                .get('href'))

    def getWorksheets(self):
        """Returns a list of Worksheet objects representing the worksheets of
        this Spreadsheet

        This involves calling the Google API.
        """
        link = self._element.find(_ns_w3('link'))
        assert link.get('rel') == (
            'http://schemas.google.com/spreadsheets/2006#worksheetsfeed')
        r = requests.get(
            link.get('href'), headers=self._token.getAuthorizationHeader())
        _check_status(r)

        e = ElementTree.fromstring(r.content.decode())
        return [Worksheet(self._token, a) for a in e.findall(_ns_w3('entry'))]

    def getWorksheet(self, title):
        """Get a worksheet with the given title.

        This involves calling the Google API.
        """
        worksheets = self.getWorksheets()
        for w in worksheets:
            if w._getTitle(w._element) == title:
                return w
        raise ValueError('unavailable sheet {}'.format(title))

    def __repr__(self):
        return "<{cls} title={title!r} key={key!r}>".format(
            cls=self.__class__.__name__,
            title=self.getTitle(),
            key=self.getKey())


class Spreadsheet(_BaseSpreadsheet):
    def __init__(self, token, key, **kwargs):
        """Initialize a Spreadsheet

        The key is either the URL of your spreadsheet or the *key*
        part as shown below:
        https://docs.google.com/spreadsheets/d/{{key}}/edit

        Initialization involves calling the Google API.
        """
        # did we get a URL?
        m = re.match(r'^(?:https?://)?(?:www\.)?'
                     'docs\.google\.com/spreadsheets/d/([^/]*)',
                     key
                     )
        if m:
            key = m.group(1)

        key = urllib.parse.quote(key)
        url = ('https://spreadsheets.google.com/feeds/spreadsheets'
               '/private/full/{}'.format(key))
        r = requests.get(url, headers=token.getAuthorizationHeader())
        _check_status(r)
        element = ElementTree.fromstring(r.content.decode())

        super().__init__(token=token, element=element, **kwargs)
