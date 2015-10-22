# Copyright 2015 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


__all__ = [
    'cast_data', 'cast_custom_data'
]


from datetime import datetime
import json
import re


DEFAULTS = {
    'interpolationWeight': 100,
    'interpolationWidth': 100,
    'widthValue': 100,
    'weightValue': 100}


def cast_data(data, types=None):
    """Cast the attributes of parsed glyphs file content."""

    if types is None:
        types = get_type_structure()

    for key, cur_type in types.items():
        if key not in data:
            try:
                data[key] = DEFAULTS[key]
            except KeyError:
                pass
            continue
        if type(cur_type) == dict:
            for cur_data in data[key]:
                cast_data(cur_data, dict(cur_type))
        else:
            data[key] = cur_type(data[key])


def cast_custom_data(data):
    """Cast some known data in custom parameters."""

    for param in data['customParameters']:
        if param['name'] == 'openTypeOS2Type':
            param['value'] = map(int, param['value'])


def get_type_structure():
    """Generate and return the highest-level type hierarchy for glyphs data.
    https://github.com/schriftgestalt/GlyphsSDK/blob/master/GlyphsFileFormat.md
    """

    return {
        'DisplayStrings': list,
        'classes': {
            'automatic': truthy,
            'code': feature_syntax,
            'name': str
        },
        'copyright': str,
        'customParameters': {
            'name': str,
            'value': default
        },
        'date': glyphs_datetime,
        'designer': str,
        'designerURL': str,
        'disablesAutomaticAlignment': truthy,  # undocumented
        'disablesNiceNames': truthy,  # undocumented
        'familyName': str,
        'featurePrefixes': {
            'code': feature_syntax,
            'name': str
        },
        'features': {
            'automatic': truthy,
            'code': feature_syntax,
            'disabled': truthy,  # undocumented
            'name': str,
            'notes': feature_syntax  # undocumented
        },
        'fontMaster': {
            'alignmentZones': pointlist,
            'ascender': int,
            'capHeight': int,
            'customParameters': {
                'name': str,
                'value': default
            },
            'descender': descender_val,
            'horizontalStems': intlist,
            'id': str,
            'userData': dict,
            'verticalStems': intlist,
            'weight': str,  # undocumented
            'weightValue': int,
            'width': str,  # undocumented
            'widthValue': int,
            'xHeight': int
        },
        'glyphs': {
            'glyphname': str,
            'lastChange': glyphs_datetime,
            'layers': {
                'anchors': {
                    'name': str,
                    'position': point
                },
                'annotations': default,  # undocumented
                'associatedMasterId': str,
                'background': default,
                'components': {
                    'anchor': str,
                    'disableAlignment': truthy,  # undocumented
                    'locked': truthy,  # undocumented
                    'name': str,
                    'transform': transform
                },
                'guideLines': default,  # undocumented
                'hints': default,  # undocumented
                'layerId': str,
                'leftMetricsKey': str,
                'rightMetricsKey': str,
                'name': str,
                'paths': {
                    'closed': truthy,
                    'nodes': nodelist
                },
                'width': num
            },
            'leftKerningGroup': str,
            'leftMetricsKey': str,
            'rightKerningGroup': str,
            'rightMetricsKey': str,
            'unicode': hex_int,
            'widthMetricsKey': str  # undocumented
        },
        'instances': {
            'customParameters': {
                'name': str,
                'value': default
            },
            'interpolationWeight': int,  # undocumented
            'interpolationWidth': int,  # undocumented
            'name': str,  # undocumented
            'weightClass': str,  # undocumented
            'widthClass': str  # undocumented
        },
        'kerning': kerning,
        'manufacturer': str,
        'manufacturerURL': str,
        'unitsPerEm': int,
        'userData': dict,
        'versionMajor': int,
        'versionMinor': version_minor
    }


def default(value):
    """Just return the value (i.e. don't cast it to anything)."""
    return value


def truthy(string):
    """Determine if an int stored in a string is truthy."""
    return bool(int(string))


def num(string):
    """Prefer casting to int, but use float if necessary."""

    val = float(string)
    int_val = int(val)
    return int_val if int_val == val else val


def hex_int(string):
    """Return the hexidecimal value represented by a string."""
    return int(string, 16)


def vector(string, dimension):
    """Parse a vector from a string with format {X, Y, Z, ...}."""

    rx = '{%s}' % ', '.join(['([-.e\d]+)'] * dimension)
    return [num(i) for i in re.match(rx, string).groups()]


def point(string):
    return vector(string, 2)


def transform(string):
    return vector(string, 6)


def node(string):
    """Cast a node from a string with format X Y TYPE [SMOOTH]."""

    rx = '([-.e\d]+) ([-.e\d]+) (LINE|CURVE|OFFCURVE)(?: (SMOOTH))?'
    m = re.match(rx, string).groups()
    return [num(m[0]), num(m[1]), m[2], m[3]]


def intlist(strlist):
    return map(int, strlist)


def pointlist(strlist):
    return map(point, strlist)


def nodelist(strlist):
    return map(node, strlist)


def glyphs_datetime(string):
    """Parse a datetime object from a string, ignoring the timezone."""
    return datetime.strptime(string[:string.rfind(' ')], '%Y-%m-%d %H:%M:%S')


def kerning(kerning_data):
    """Cast the values in kerning data to ints."""

    new_data = {}
    for master_id, master_map in kerning_data.items():
        new_data[master_id] = {}
        for left_glyph, glyph_map in master_map.items():
            new_data[master_id][left_glyph] = {}
            for right_glyph, value in glyph_map.items():
                new_data[master_id][left_glyph][right_glyph] = int(value)
    return new_data


def descender_val(string):
    """Ensure that descender values are always negative."""

    num = int(string)
    assert num < 0
    return num


def version_minor(string):
    """Ensure that the minor version number is between 0 and 999."""

    num = int(string)
    assert num >= 0 and num <= 999
    return num


def feature_syntax(string):
    """Replace escaped characters with their intended characters.
    Unescapes curved quotes to straight quotes, so that we can definitely
    include this casted data in feature syntax.
    """

    replacements = (
        ('\\012', '\n'), ('\\011', '\t'), ('\\U2018', "'"), ('\\U2019', "'"),
        ('\\U201C', '"'), ('\\U201D', '"'))
    for escaped, unescaped in replacements:
        string = string.replace(escaped, unescaped)
    return string
