# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, date, time, timedelta
from odoo import api, fields, models, _
import base64
import unicodedata
import re, sys, os
import codecs
from calendar import monthrange

class PriceTag(models.Model):
    _name = 'price.tag'
    _description = 'Price Tags'

    active = fields.Boolean(default=True)
    color = fields.Integer(required=True, default=0)
    name = fields.Char(required=True)

class PriceListReport(models.Model):
    _description = "Price list report"
    _name = 'price.list.report'
    _inherit = ['ir.needaction_mixin', 'mail.thread']
    _order = 'id desc'

    @api.model
    def _needaction_domain_get(self):
        return [('name', '!=', '')]

    name = fields.Char('Code', translate=True, default="New")

    desc = fields.Char('Name', translate=True)

    obs = fields.Text('Notes', translate=True)

    date = fields.Datetime('Date', default=fields.Datetime.now)

    partner_id = fields.Many2one('res.partner', string='Customer')

    product_pricelist_id = fields.Many2one('product.pricelist', string='Product Pricelist')
    product_pricelist_suggested_id = fields.Many2one('product.pricelist', string='Product Pricelist Suggested')

    user_id = fields.Many2one('res.users', string='User', track_visibility='onchange',
                              default=lambda self: self.env.user)

    tag_ids = fields.Many2many('price.tag', string='Tags')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('downloaded', 'Downloaded'),
        ('done', 'Done')],
        string='State', index=True, readonly=True, default='draft', copy=False)

    image_medium = fields.Binary(
        "Medium-sized image",
        help="Product image")

    file_name = fields.Char("File")
    file_01 = fields.Binary(
        string='File',
        copy=False,
        help='File')

    mody_price = fields.Float("Modify price", default=1)

    list_product_ids = fields.One2many('list.product.report', 'price_list_id', string='Listado de Productos')

    @api.multi
    def exe_delete(self):
        self._cr.execute("DELETE FROM list_product_report WHERE price_list_id = '" + str(self.id) + "'")
        self.message_post(body=_("Erased: %s") % self.env.user.name)

    @api.multi
    def exe_csv(self):
        res = {}
        if self.partner_id:
            fname = '%s_price_list.csv' % (self.partner_id.name)
        else:
            fname = 'price_list.csv'


        data = u"Code,Barcode,Product,um,Price,Suggested Price" + '\n'

        for product in self.list_product_ids:
            code = "-"
            barcode = "-"
            name = "-"
            um = "-"
            price = 0
            suggested_price = 0

            if product.product_id.default_code:
                code = product.product_id.default_code

            if product.product_id.barcode:
                barcode = product.product_id.barcode

            if product.product_id.name:
                name = product.product_id.display_name

            if product.product_id.uom_id:
                um = product.product_id.uom_id.name

            if product.price:
                price = product.price

            if product.suggested_price:
                suggested_price = product.suggested_price


            data = data + code + "," \
                   + barcode + "," \
                   + name + "," \
                   + um + "," \
                   + str(price) + "," \
                   + str(suggested_price) + '\n'

        data_b64 = base64.encodestring(data.encode('utf-8'))
        doc = self.env['ir.attachment'].create({
            'name': '%s.csv' % _(fname),
            'datas': data_b64,
            'datas_fname': '%s.csv' % _(fname),
        })

        self.state = 'downloaded'

        self.message_post(body=_("Downloaded: %s") % self.env.user.name)

        return {
            'type': "ir.actions.act_url",
            'url': "web/content/?model=ir.attachment&id=" + str(
                doc.id) + "&filename_field=datas_fname&field=datas&download=true&filename=" + str(doc.name),
            'target': "current"
        }

    @api.model
    def create(self, vals):
        if vals.get('name', "New") == "New":
            vals['name'] = self.env['ir.sequence'].next_by_code('price.list.report') or "New"
        return super(PriceListReport, self).create(vals)

    @api.multi
    def name_get(self):
        res = super(PriceListReport, self).name_get()
        result = []
        for element in res:
            book_id = element[0]
            code = self.browse(book_id).name
            desc = self.browse(book_id).desc
            name = code and '[%s] %s' % (code, desc) or '%s' % desc
            result.append((book_id, name))
        return result

    @api.onchange('product_pricelist_id')
    def onchange_pricelist_id(self):
        if self.product_pricelist_id:
            for line in self.list_product_ids:
                line.price = self.product_pricelist_id.get_product_price(line.product_id, 1.0, self.partner_id)
                
    @api.onchange('product_pricelist_suggested_id')
    def onchange_pricelist_suggested_id(self):
        if self.product_pricelist_suggested_id:
            for line in self.list_product_ids:
                line.suggested_price = self.product_pricelist_suggested_id.get_product_price(line.product_id, 1.0, self.partner_id)


class List_ProductReport(models.Model):
    _name = 'list.product.report'

    product_id = fields.Many2one('product.product', string="Product")
    barcode = fields.Char('Barcode', related='product_id.barcode')
    default_code = fields.Char('Barcode', related='product_id.default_code')

    price = fields.Float("Price")
    suggested_price = fields.Float("Suggested Price")
    price_list_id = fields.Many2one('price.list.report', "Price List", ondelete='cascade')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.price_list_id.product_pricelist_id:
            self.price = 0
