pgsheets : Manipulate Google Sheets Using Python
================================================

pgsheets is a Python3 library for interacting with Google Sheets.
It makes use of `Pandas <http://pandas.pydata.org/>`__ DataFrames,
2-dimensional structures perfectly
suited for data analysis and representing a spreadsheet.

This library can be integrated easily with your existing data to present dashboards, update documents, or provide quick data analysis.

Features
~~~~~~~~~~~~~~~~~~~~~~~~~~

- Get / Set all or part of a Google Sheet
- Manage authorization with Google API
- Retrieve/set formulas or values
- Resize spreadsheets
- Open up a wealth of Pandas data tools to use on Google Sheets

Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Simply install with pip:

.. code-block:: bash

    $ pip install pgsheets

Usage
~~~~~~~~~~~~~~~~~~~~~~~~~~

Setting up a Google Project
----------------------------

If you haven't already you will need to create a project in Google's Developer Console and get your Client ID and Client Secret.

#. Navigate to the `Google Developer Console <https://console.developers.google.com/project>`__
#. Create a project (you will be redirected to the project page)
#. Click on *APIs & Auth*
#. Click on *Consent screen* and set a Product Name
#. Now click on *credentials*.
#. Click *Create new Client ID* and select *Installed Application* > *Other*

Getting a Token
----------------------------

Using your Google *client id* and *client secret* we can get a
authorization URL to present to a user:

.. code-block:: python

    >>> from pgsheets import Token, Client
    >>> c = Client(my_client_id, my_client_secret)
    >>> c.getOauthUrl()
    'https://accounts.google.com/o/oauth2/auth?...'

By visiting this URL a Google user can consent to your application
viewing and modifying their Google sheets. After consenting to this
an access code is returned, which we use to get a token:

.. code-block:: python

    >>> my_token = c.getRefreshToken(access_code)
    >>> type(my_token)
    str
    >>> t = Token(c, my_token)

You need to save *my_token* for future use.

Editing a spreadsheet
-------------------------------------------

Create a spreadsheet (and make sure you save it) and copy the url.
Now we can access the Spreadsheet:

.. code-block:: python

    >>> import pandas as pd
    >>> from pgsheets import Spreadsheet
    >>> s = Spreadsheet(t, my_url)
    >>> s
    <Spreadsheet title='test' key='.....'>
    >>> s.getTitle()
    'test'
    >>> s.getWorksheets()
    [<Worksheet title='Sheet1' sheet_key='.....'>]
    >>> w = s.getWorksheet('Sheet1')
    >>> w.getTitle()
    'Sheet1'
    >>> w.setDataFrame(
            pd.DataFrame([['money', 'interest', 'years', 'result'],
                          ['1000', '0.015', '3', '=A2 * (1+B2) ^ C2']]),
            copy_columns=False,
            copy_index=False,
            resize=True)
    >>> w.asDataFrame()
              interest years                                  result
        money                                                       
        1000     0.015     3  =R[0]C[-3] * (1+R[0]C[-2]) ^ R[0]C[-1]
    >>> w.asDataFrame(values=True)
              interest years       result
        money                                                       
        1000     0.015     3  1045.678375
    >>> df = w.asDataFrame()
    >>> df['checked'] = "TRUE"
    >>> w.setDataFrame(df)
    >>> w.asDataFrame()
              interest years                                  result checked
        money                                                               
        1000     0.015     3  =R[0]C[-3] * (1+R[0]C[-2]) ^ R[0]C[-1]    TRUE

Limitations
~~~~~~~~~~~~~~~~~~~~~~~~~~

The library has only been tested in Python3.4.
It will almost certainly not work in Python2.

Currently the following cannot be done with pgsheets:

- Create a spreadsheet
- Add a workbook to a spreadsheet
- Rename a spreadsheet or a workbook
- Prevent certain values from changing slightly e.g. 'True' becomes 'TRUE'

Finally the Google API has some limitations.
Ideally this code should not cause any changes to a worksheet:

.. code-block:: python

    >>> w.setDataFrame(w.asDataFrame())

Unfortunately, there are certain edge cases. 
For example, with a Formula such as the following

=======    =======
={1, 2}
=======    =======

which displays across two cells:

=======    =======
  1         2
=======    =======

There is no clear way to know
that the cell on the right wasn't input as a '2' by the user.
Thus the above code would cause the following output:

=======    =======
={1, 2}      2
=======    =======

which displays as:

=======    =======
 #REF!       2
=======    =======
