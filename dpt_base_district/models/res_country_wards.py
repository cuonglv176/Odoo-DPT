from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResCountryWards(models.Model):
    _name = 'res.country.wards'
    _description = 'Wards'
    
    name = fields.Char(string='Name', translate=True, required=True)
    code = fields.Char(string='Code', copy=False)
    district_code = fields.Char(string='District Code')
    district_id = fields.Many2one('res.country.district', string='District')
    state_id = fields.Many2one('res.country.state', string='State', required = True, ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', required = True, ondelete='restrict')
    
    _sql_constraints = [
        ('code_unique', 'unique (code, country_id)', "The code of the district must be unique per country!")
        ]
    
    @api.constrains('state_id', 'country_id')
    def _check_country(self):
        for r in self:
            if r.state_id.country_id != r.country_id:
                raise ValidationError(_("The state '%s' does not belong to the country '%s'. Please select another!")\
                                      %(r.state_id.name, r.country_id.name))
    
    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id and self.country_id != self.state_id.country_id:
            self.state_id = False

    @api.onchange('state_id')
    def _onchange_state(self):
        if self.state_id.country_id:
            self.country_id = self.state_id.country_id
