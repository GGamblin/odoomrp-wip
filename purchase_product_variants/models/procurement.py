from openerp import models, fields, api, _


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'
    
    @api.multi
    def _prepare_purchase_order_line(self, po, supplier):
        self.ensure_one()
        
        result = super(ProcurementOrder, self)._prepare_purchase_order_line(po, supplier)
        result['product_template'] = self.product_id.product_tmpl_id.id
        result['product_attributes'] = [(4, x.id) for x in self.attribute_line_ids]
        return result

