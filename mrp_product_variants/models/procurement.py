# -*- coding: utf-8 -*-
# (c) 2015 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models

class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _prepare_mo_vals(self, procurement):
        result = super(ProcurementOrder, self)._prepare_mo_vals(procurement)
        product_id = result.get('product_id')
        product = self.env['product.product'].browse(product_id)
        result['product_template_id'] = product.product_tmpl_id.id
        #result['product_attributes'] = (
        #    (0, 0, x) for x in product._get_procurement_attribute_line_dict())
        result['product_attributes'] = [(4, x.id) for x in procurement.attribute_line_ids]
        return result
