# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api, exceptions, _


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    @api.multi
    def calc_mrp_real_cost(self):
        self.ensure_one()
        return sum([-line.amount for line in
                    self.analytic_line_ids.filtered(lambda l: l.amount < 0)])

    @api.one
    @api.depends('analytic_line_ids', 'analytic_line_ids.amount',
                 'product_qty')
    def get_real_cost(self):
        self.real_cost = self.calc_mrp_real_cost()
        self.unit_real_cost = self.real_cost / self.product_qty

    @api.one
    @api.depends('avg_cost', 'real_cost')
    def get_percentage_difference(self):
        self.percentage_difference = 0
        if self.avg_cost and self.real_cost:
            self.percentage_difference = (self.real_cost * 100 / self.avg_cost)

    real_cost = fields.Float("Total Real Cost", compute="get_real_cost",
                             store=True)
    unit_real_cost = fields.Float("Unit Real Cost", compute="get_real_cost",
                                  store=True)
    percentage_difference = fields.Float(
        "% difference", compute="get_percentage_difference", store=True)

    @api.multi
    def action_production_end(self):
        res = super(MrpProduction, self).action_production_end()
        for record in self:
            mrp_cost = record.calc_mrp_real_cost()
            done_lines = record.move_created_ids2.filtered(lambda l:
                                                           l.state == 'done')
            done_lines.create_produce_cost_line(mrp_cost)
            record.real_cost = mrp_cost
            done_lines.product_price_update_production_done()
        return res

    @api.model
    def _prepare_real_cost_analytic_line(
            self, journal, name, production, product, general_account=None,
            workorder=None, qty=1, amount=0):
        """
        Prepare the vals for creating an analytic entry for real cost
        :param journal: Journal of the entry
        :param name: Name of the entry
        :param production: Origin product
        :param product: Product for the entry
        :param general_account: General account for the entry
        :param workorder: Origin workorder
        :param qty: Quantity for the entry. This quantity will multiply both
        standard and average costs for the entry costs.
        :param amount: Cost for calculating real cost.
        :return: Dictionary with the analytic entry vals.
        """
        analytic_line_obj = self.env['account.analytic.line']
        property_obj = self.env['ir.property']
        if not general_account:
            general_account = (
                product.property_account_income or
                product.categ_id.property_account_income_categ or
                property_obj.get('property_account_expense_categ',
                                 'product.category'))
        if not production.analytic_account_id:
            raise exceptions.Warning(
                _('You must define one Analytic Account for this MO: %s') %
                (production.name))
        return {
            'name': name,
            'mrp_production_id': production.id,
            'workorder': workorder and workorder.id or False,
            'account_id': self.analytic_account_id.id,
            'journal_id': journal.id,
            'user_id': self.env.uid,
            'date': analytic_line_obj._get_default_date(),
            'product_id': product and product.id or False,
            'unit_amount': qty,
            'amount': amount,
            'product_uom_id': product.uom_id.id,
            'general_account_id': general_account.id,
        }
