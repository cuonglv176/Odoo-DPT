# -*- coding: utf-8 -*-

import html2text

from odoo import fields


def monkey_patch(cls):
    """ Return a method decorator to monkey-patch the given class. """
    def decorate(func):
        name = 'convert_to_read'
        func.super = getattr(cls, name, None)
        setattr(cls, name, func)
        return func
    return decorate


@monkey_patch(fields.Field)
def convert_to_read(self, value, record, use_display_name=True):
    r = convert_to_read.super(self, value, record, use_display_name=use_display_name)
    if record.env.context.get('read_text_only'):
        r = r or ''
    return r


@monkey_patch(fields.Html)
def convert_to_read_html(self, value, record, use_display_name=True):
    r = convert_to_read_html.super(self, value, record, use_display_name=use_display_name)
    if record.env.context.get('read_text_only'):
        r = html2text.html2text(r) if r else ''
    return r


@monkey_patch(fields.Many2one)
def convert_to_read_many2one(self, value, record, use_display_name=True):
    if record.env.context.get('read_text_only'):
        r = convert_to_read_many2one.super(self, value, record, use_display_name=True)
        r = r[1] if r else ''
    else:
        r = convert_to_read_many2one.super(self, value, record, use_display_name=use_display_name)
    return r


@monkey_patch(fields.Many2many)
def convert_to_read_many2many(self, value, record, use_display_name=True):
    if record.env.context.get('read_text_only'):
        r = ', '.join([x[1] for x in value.name_get()])
    else:
        r = convert_to_read_many2many.super(self, value, record, use_display_name=use_display_name)
    return r


@monkey_patch(fields.One2many)
def convert_to_read_one2many(self, value, record, use_display_name=True):
    if record.env.context.get('read_text_only') and record.env.context.get('read_text_only_one2many', True):
        r = value.with_context(read_text_only_one2many=False).read(fields=None)
    else:
        r = convert_to_read_one2many.super(self, value, record, use_display_name=use_display_name)
    return r


@monkey_patch(fields.Selection)
def convert_to_read_selection(self, value, record, use_display_name=True):
    r = convert_to_read_selection.super(self, value, record, use_display_name=use_display_name)
    if record.env.context.get('read_text_only'):
        reading = True
        field = self
        while reading:
            try:
                r = dict(field.selection).get(r, '')
                reading = False
            except:
                if field.related_field:
                    field = field.related_field
                else:
                    selection_function = field.args.get('selection')
                    if selection_function:
                        r = dict(selection_function(record)).get(r, '')
                    else:
                        r = ''
                    reading = False
    return r
