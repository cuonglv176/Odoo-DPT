from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    district_id = fields.Many2one('res.country.district', string='District', domain="[('state_id', '=?', state_id)]")
    wards_id = fields.Many2one('res.country.wards', string='Wards', domain="[('district_id', '=?', district_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', default=241)

    @api.constrains('district_id', 'state_id')
    def _check_state(self):
        for r in self:
            if r.state_id and r.district_id and r.district_id.state_id != r.state_id:
                raise ValidationError(_("The district '%s' does not belong to state '%s'. Please select another!") \
                                      % (r.district_id.name, r.state_id.name))

    @api.constrains('district_id', 'country_id')
    def _check_country(self):
        for r in self:
            if r.country_id and r.district_id and r.district_id.country_id != r.country_id:
                raise ValidationError(_("The district '%s' does not belong to country '%s'. Please select another!") \
                                      % (r.district_id.name, r.country_id.name))

    @api.onchange('country_id')
    def _onchange_country_id(self):
        super(ResPartner, self)._onchange_country_id()
        if self.country_id and self.country_id != self.state_id.country_id:
            self.district_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        super(ResPartner, self)._onchange_state()
        if self.state_id and self.state_id != self.district_id.state_id:
            self.district_id = False

    @api.onchange('district_id')
    def _onchange_district(self):
        if self.district_id:
            self.country_id = self.district_id.country_id
            self.state_id = self.district_id.state_id

    @api.model
    def _address_fields(self):
        res = super(ResPartner, self)._address_fields()
        res.append('district_id')
        return res
