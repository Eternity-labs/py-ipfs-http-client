# -*- encoding: utf-8 -*-
"""Defines encoding related classes.

Classes:
TestEncoding - A class that tests constructs located in the encoding.py module.
"""

import unittest
import json

import pytest
import six

import ipfshttpclient.encoding
import ipfshttpclient.exceptions


class TestEncoding(unittest.TestCase):
    """Unit tests the Encoding class

    Public methods:
    setUp - create a Json encoder 
    test_json_parse - Asserts parsed key/value json matches expected output
    test_json_parse_chained - Tests if concatenated string of JSON object is being parsed correctly
    test_json_parse_chained_newlines - Tests parsing of concatenated string of JSON object containing a new line
    test_json_encode - Tests serilization of json formatted string to an object
    test_get_encoder_by_name - Tests the process of obtaining an Encoder object given the named encoding
    test_get_invalid_encoder - Tests the exception handling given an invalid named encoding

    """
    def setUp(self):
        """create a Json encoder"""
        self.encoder_json = ipfshttpclient.encoding.Json()

    def test_json_parse(self):
        """Asserts parsed key/value json matches expected output."""
        data = {'key': 'value'}
        raw = six.b(json.dumps(data))
        res = self.encoder_json.parse(raw)
        assert res['key'] == 'value'

    def test_json_parse_partial(self):
        """Tests if feeding parts of JSON strings in the right order to the JSON parser produces the right results."""
        data1 = {'key1': 'value1'}
        data2 = {'key2': 'value2'}
        
        # Try single fragmented data set
        data1_binary = six.b(json.dumps(data1))
        assert list(self.encoder_json.parse_partial(data1_binary[:8])) == []
        assert list(self.encoder_json.parse_partial(data1_binary[8:])) == [data1]
        assert list(self.encoder_json.parse_finalize()) == []
        
        # Try multiple data sets contained in whitespace
        data2_binary = six.b(json.dumps(data2))
        data2_final  = b"  " + data1_binary + b"  \r\n  " + data2_binary + b"  "
        assert list(self.encoder_json.parse_partial(data2_final)) == [data1, data2]
        assert list(self.encoder_json.parse_finalize()) == []
        
        # String containing broken UTF-8
        with pytest.raises(ipfshttpclient.exceptions.DecodingError):
            list(self.encoder_json.parse_partial(b'{"hello": "\xc3ber world!"}'))
        assert list(self.encoder_json.parse_finalize()) == []
    
    def test_json_with_newlines(self):
        """Tests if feeding partial JSON strings with line breaks behaves as expected."""
        data1 = '{"key1":\n"value1",\n'
        data2 = '"key2":\n\n\n"value2"\n}'
        
        data_expected = json.loads(data1 + data2)
        
        assert list(self.encoder_json.parse_partial(six.b(data1))) == []
        assert list(self.encoder_json.parse_partial(six.b(data2))) == [data_expected]
        assert list(self.encoder_json.parse_finalize()) == []
    
    def test_json_parse_incomplete(self):
        """Tests if feeding the JSON parse incomplete data correctly produces an error."""
        list(self.encoder_json.parse_partial(b'{"bla":'))
        with pytest.raises(ipfshttpclient.exceptions.DecodingError):
            self.encoder_json.parse_finalize()

        list(self.encoder_json.parse_partial(b'{"\xc3')) # Incomplete UTF-8 sequence
        with pytest.raises(ipfshttpclient.exceptions.DecodingError):
            self.encoder_json.parse_finalize()

    def test_json_parse_chained(self):
        """Tests if concatenated string of JSON object is being parsed correctly."""
        data1 = {'key1': 'value1'}
        data2 = {'key2': 'value2'}
        res = self.encoder_json.parse(
            six.b(json.dumps(data1)) + six.b(json.dumps(data2)))
        assert len(res) == 2
        assert res[0]['key1'] == 'value1'
        assert res[1]['key2'] == 'value2'

    def test_json_parse_chained_newlines(self):
        """Tests parsing of concatenated string of JSON object containing a new line."""
        data1 = {'key1': 'value1'}
        data2 = {'key2': 'value2'}
        res = self.encoder_json.parse(
            six.b(json.dumps(data1)) + b'\n' + six.b(json.dumps(data2)))
        assert len(res) == 2
        assert res[0]['key1'] == 'value1'
        assert res[1]['key2'] == 'value2'

    def test_json_encode(self):
        """Tests serilization of an object into a json formatted UTF-8 string."""
        data = {'key': 'value with Ünicøde characters ☺'}
        assert self.encoder_json.encode(data) == \
               b'{"key":"value with \xc3\x9cnic\xc3\xb8de characters \xe2\x98\xba"}'

    def test_get_encoder_by_name(self):
        """Tests the process of obtaining an Encoder object given the named encoding."""
        encoder = ipfshttpclient.encoding.get_encoding('json')
        assert encoder.name == 'json'

    def test_get_invalid_encoder(self):
        """Tests the exception handling given an invalid named encoding."""
        with pytest.raises(ipfshttpclient.exceptions.EncoderMissingError):
            ipfshttpclient.encoding.get_encoding('fake')
