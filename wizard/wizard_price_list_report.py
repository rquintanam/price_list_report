# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class WizardAccountPaysheetPayment(models.TransientModel):
    _name = 'wizard.price.list.report'
    _description = 'Wizard List Price'
    pricelist_report_id = fields.Many2one('price.list.report', string='Insert in Report Pricelist')


    def action_wizard_wizard_price_list_report_acc(self):
        pricelist_report_id = self.pricelist_report_id

        if pricelist_report_id:
            record_ids = self._context.get('active_ids')

            if not record_ids:
                raise UserError('There are no selected products.')

            for product in self.env['product.product'].browse(record_ids):
                id = product.id

                vals = {
                        'product_id': id,
                        'price_list_id': pricelist_report_id.id,
                        }

                insert = self.env['list.product.report'].create(vals)