#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# vim: autoindent expandtab tabstop=4 sw=4 sts=4 filetype=python

"""
Display cursors, dicts and objects as html-tables.
"""

# Copyright (c) 2012, Adfinis SyGroup AG
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Adfinis SyGroup AG nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS";
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Adfinis SyGroup AG BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import IPython.core.display as ipdisp
import sys
from textwrap import wrap
from pprint import pformat


def extended_styles(css=False):
    """Injects styles and scripts for print_html and toggle input into a
    ipython notebook.

    css: Inject table css-styles for pre-wrapped tables content and nbconvert
            display fixes.
    """
    pre = """
        <script type="text/javascript">
        var toggleInput;
        (function() {
            var inputInterval;
            var intervalCount = 0;
            var init = false;
            var inputUp = false;
            toggleInput = function() {
                if(inputUp) {
                    $('div.input').slideDown();
                    $('div.code_cell').attr('style', '');
                }
                else {
                    $('div.input').slideUp();
                    $('div.code_cell').attr('style', 'padding: 0px; margin: 0px');
                }
                inputUp = !inputUp;
                init = true;
            }
            function initExtendedStyles() {
                if(intervalCount > 15) {
                    clearInterval(inputInterval);
                }
                intervalCount += 1;
                try {"""
    middle = """
                    var style = [
'                           <style type="text/css" id="extendedStyle">',
'                               table.nowrap td {',
'                                   white-space: nowrap;',
'                               }',
'                               table.bound {',
'                                   margin-right: 80px;',
'                               }',
'                               table.dataframe {',
'                                   margin-right: 80px;',
'                               }',
'                           </style>'].join("\\n");
                    if($('#extendedStyle').length == 0) {
                        $('head').append(style);
                    }
                    else {
                        $('#extendedStyle').replaceWith(style);
                    }"""
    post = """
                    // Only slideUp if we're not on notebook server
                    // meaning Print View and nbconverted
                    if($('#save_status').length == 0 && init == false) {
                        toggleInput();
                    }
                    clearInterval(inputInterval);
                } catch(e) {}
            }
            if (typeof jQuery == 'undefined') {
                // if jQuery Library is not loaded
                var script = document.createElement( 'script' );
                script.type = 'text/javascript';
                script.src = 'https://ajax.googleapis.com/ajax/libs/jquery/1.8.3/jquery.min.js';
                document.body.appendChild(script);
            }

            setTimeout(initExtendedStyles, 200);
            // jQuery is doing this interval trick
            // I guess its the way to do it then.
            inputInterval = setInterval(initExtendedStyles, 1000);
        }());
        </script>
       <a href="javascript:toggleInput()">Toggle Input</a>
        """
    if css:
        return ipdisp.HTML("".join([pre, middle, post]))
    else:
        return ipdisp.HTML("".join([pre, post]))


def remove_extended_styles():
    """Removes solarized theme."""
    html = """
        <script type="text/javascript">
        jQuery(function($){
            $('#extendedStyle').replaceWith('');
        });
        </script>"""
    return ipdisp.HTML(html)


def display_html(data, tight=False, projection=None):
    """Displays database-API cursor, dicts or objects as html, fallback to pprint.

    Short cut: dh()

    data       : The data to display.
    tight      : If used with dictonaries, do not textwrap and do not use <pre>.
    projection : A list of fields to display (used for dicts only)


    Display sql cursors and dictionaries as html-tables, sub dictionaries are
    pprinted and line-wrapped to a width of 80 chars. Please note that wrapped
    lines will have the prefix $.
    Call extended_styles() once in your notebook or qtconsole.

    """

    if hasattr(data, 'to_html'):
        return ipdisp.HTML(data.to_html())
    elif hasattr(data, 'description') and hasattr(data, 'fetchall'):
        return html_cursor(data)
    elif hasattr(data, "__dict__"):
        return html_dict(data.__dict__, tight, projection)
    elif str(data.__class__) == "<type 'dict'>":
        return html_dict(data, tight, projection)
    elif str(data.__class__) == "<class 'dict'>":
        return html_dict(data, tight, projection)
    elif (
        str(data.__class__) == "<class 'list'>"
        or
        str(data.__class__) == "<type 'list'>"
    ):
        if len(data) > 0:
            if (
                str(data[0].__class__) == "<class 'dict'>"
                or
                str(data[0].__class__) == "<type 'dict'>"
            ):
                return html_multi_dict(data, tight, projection)
    return html_pprint(data)

dh = display_html


def pprint_wrap(data):
    """Pretty print and wrap the data."""
    return enc('\n'.join(['\n$'.join(wrap(x, width=80))
               for x in pformat(data).split('\n')]))


def html_pprint(data):
    return ipdisp.HTML('\n'.join([
        "<pre>",
        pprint_wrap(data),
        "</pre>"]))


def _enc_v2(value):
    return unicode(value).replace(
        '&',
        '&amp;'
    ).replace(
        '<',
        '&lt;'
    ).replace(
        '>',
        '&gt;'
    )


def _enc_v3(value):
    return str(value).replace(
        '&',
        '&amp;'
    ).replace(
        '<',
        '&lt;'
    ).replace(
        '>',
        '&gt;'
    )

if sys.version_info[0] == 2:
    enc = _enc_v2
else:
    enc = _enc_v3


def html_cursor(cursor):
    """Pretty prints a generic database API cursor."""
    if cursor.description is None:
        ipdisp.display_html(ipdisp.HTML("<i>No data returned</i>"))
        return
    headers = [x[0] for x in cursor.description]
    header_line = "<tr><th>" + ("</th><th>".join(headers)) + "</th></tr>"

    def getrow(row):
        rendered = ["<tr>"] + ["<td>%s</td>" % enc(row[col])
                   for col in range(0, len(headers))] + ["</tr>"]
        return "".join(rendered)

    rows = [header_line] + [getrow(row) for row in cursor]
    body = '\n'.join(rows)
    table = '<table class="nowrap">\n%s\n</table>' % body
    return ipdisp.HTML(table)


def _table_config(tight):
    if tight:
        output = ['<table class="bound"><tr>']
        td_start = "<td>"
        td_end   = "</td>"
        print_function = enc
    else:
        output = ['<table class="nowrap"><tr>']
        td_start = "<td><pre>"
        td_end   = "</pre></td>"
        print_function = pprint_wrap
    return (
        output,
        td_start,
        td_end,
        print_function
    )


def html_dict(dict_, tight=False, projection=None):
    """Pretty print a dictionary.

    dict_      : The dict to pretty print.
    tight      : Do not textwrap and do not use <pre>.
    projection : A list of fields to display"""
    (
        output,
        td_start,
        td_end,
        print_function
    ) = _table_config(tight)

    fields = None
    if projection is None:
        fields = dict_
    else:
        fields = projection
    for key in fields:
        output += ["<th>", key, "</th>"]
    output += ["</tr><tr>"]
    for key in fields:
        output += [td_start, print_function(dict_[key]), td_end]
    output += ["</table>"]
    return ipdisp.HTML('\n'.join(output))


def html_multi_dict(array_, tight=False, projection=None):
    """Pretty print an array of dictionaries.

    array_     : The multi dict to pretty print.
    tight      : Do not textwrap and do not use <pre>.
    projection : A list of fields to display"""
    (
        output,
        td_start,
        td_end,
        print_function
    ) = _table_config(tight)
    fields = None
    if projection is None:
        fields = array_[0]
    else:
        fields = projection
    if len(array_) < 1:
        return ipdisp.HTML("")
    for key in fields:
        output += ["<th>", key, "</th>"]
    for dict_ in array_:
        output += ['<tr>']
        for key in fields:
            output += [td_start, print_function(dict_[key]), td_end]
        output += ['</tr>']
    output += ["</table>"]
    return ipdisp.HTML('\n'.join(output))


def solarized():
    """Injects solarized code mirror theme."""
    html = """
        <script type="text/javascript">
        jQuery(function($){
            var solarizedStyle = [
'           <style type="text/css" id="solarizedStyle">',
'           .cm-s-ipython { background-color: #002b36; color: #839496; }',
'           .cm-s-ipython span.cm-keyword {color: #859900; font-weight: bold;}',
'           .cm-s-ipython span.cm-number {color: #b58900;}',
'           .cm-s-ipython span.cm-operator {color: #268bd2; font-weight: bold;}',
'           .cm-s-ipython span.cm-meta {color: #cb4b16;}',
'           .cm-s-ipython span.cm-comment {color: #586e75; font-style: italic;}',
'           .cm-s-ipython span.cm-string {color: #2aa198;}',
'           .cm-s-ipython span.cm-error {color: #dc322f;}',
'           .cm-s-ipython span.cm-builtin {color: #cb4b16;}',
'           .cm-s-ipython span.cm-variable {color: #839496;}',
'           </style>'].join('\\n');
            if($('#solarizedStyle').length == 0) {
                $('head').append(solarizedStyle);
            }
            else {
                $('#solarizedStyle').replaceWith(solarizedStyle);
            }
        });
        </script>"""
    return ipdisp.HTML(html)


def remove_solarized():
    """Removes solarized theme."""
    html = """
        <script type="text/javascript">
        jQuery(function($){
            $('#solarizedStyle').replaceWith('');
        });
        </script>"""
    return ipdisp.HTML(html)