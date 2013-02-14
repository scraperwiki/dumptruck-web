#!/usr/bin/env python
# run with nosetests
# Test the metadata API

from nose.tools import *

def testMeta1():
    endpoint = "/sql/meta/"
    result = get_json_from_query()
    # Returns something like:
    """
    {
      "table": {
        "first_table_name": {
          "type": "table",
          "column_names": ["column1", "column2"]
        },
        "a_view": {
          "type": "view",
          "column_names": ["blah blah", "blah"]
        },
      },
      "database_type": "sqlite"
    }
    # With future expansion for columns that are typed:
        "columns": [{"name":"column1","type":"Number"}]
    # and tables with unique keys.
        "unique_keys": ["col1", "col2"}
    """
    assert result
    assert result['database_type']
    assert result['table']
    assert result['table']['test1']
    assert_equal(result['table']['test1']['type'], 'table')
    column_names = result['table']['test1']['column_names']
    assert column_names
    assert "column1" in column_names
    assert "column2" in column_names

def get_json_from_query():
    return {
      "table": {
        "test1": {
          "type": "table",
          "column_names": ["column1", "column2"]
        },
        "another_table": {
          "column_names": ["blah blah", "blah"]
        },
      },
      "database_type": "sqlite"
    }
