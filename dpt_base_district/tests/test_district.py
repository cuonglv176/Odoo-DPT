try:
    # try to use UniqueViolation if psycopg2's version >= 2.8
    from psycopg2 import errors
    UniqueViolation = errors.UniqueViolation
except Exception:
    import psycopg2
    UniqueViolation = psycopg2.IntegrityError

from odoo.tests.common import TransactionCase, Form
from odoo.tests import tagged
from odoo.tools import mute_logger
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestDistict(TransactionCase):

    def setUp(self):
        super(TestDistict, self).setUp()
        # data country
        self.country_vn = self.browse_ref('base.vn')
        self.country_us = self.browse_ref('base.us')
        # data state
        self.state_vn_hn = self.browse_ref('base.state_vn_VN-HN')
        self.state_vn_tq = self.browse_ref('base.state_vn_VN-04')
        self.state_us = self.browse_ref('base.state_us_27')
        # data disrict
        self.district_1 = self.env['res.country.district'].create({
            'code': '0001',
            'name': 'Brooklyn',
            'state_id': self.state_us.id,
            'country_id': self.country_us.id
            })
        
        self.district_2 = self.env['res.country.district'].create({
            'code': '0002',
            'name': 'Manhattan',
            'state_id': self.state_us.id,
            'country_id': self.country_us.id
            })
        # district of vietname
        self.district_vn_1 = self.browse_ref('viin_base_district.district_vn_VN-QBD-001')
        self.district_vn_70 = self.browse_ref('viin_base_district.district_vn_VN-TPTQ-070')
        
    def test_11_code_unique(self):
        #  Check constraints unique (code, country_id) when creating a district
        with self.assertRaises(UniqueViolation), mute_logger('odoo.sql_db'):
            self.district_3 = self.env['res.country.district'].create({
            'code': '0001',
            'name': 'Queens',
            'state_id': self.state_us.id,
            'country_id': self.country_us.id
            })
            self.district_3.flush()
        
    def test_12_code_unique(self):
        #  Check constraints unique (code, country_id) when updating a district
        with self.assertRaises(UniqueViolation), mute_logger('odoo.sql_db'):
            self.district_2.write({'code': '0001'})
            self.district_2.flush()
            
    def test_21_check_country_district(self):
        """ 
        The Test:
            The state does not belong to the country
        model: res.country.district
        """
        with self.assertRaises(ValidationError):
            self.district_vn_1.write({
                'country_id': self.country_us.id
                })
            
    def test_22_check_state_partner(self):
        """
        The test:
            The district does not belong to the state
        model: res.partner
        """
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                    'name': 'Vendor 1',
                    'district_id': self.district_vn_1.id,
                    'state_id': self.state_us.id
                    })
        
    def test_23_check_country_partner(self):
        """
        The test:
            The district does not belong to the country
        model: res.partner
        """
        with self.assertRaises(ValidationError):
            self.env['res.partner'].create({
                    'name': 'Vendor 1',
                    'district_id': self.district_vn_1.id,
                    'country_id': self.country_us.id
                    })
                
    # ================Form test================
    def test_31_form_partner(self):
        partner_form = Form(self.env['res.partner'], view='base.view_partner_form')
        partner_form.name = 'Customer 1'
        partner_form.district_id = self.district_vn_1
        
        # Check onchange field district
        # 1. Field state
        self.assertEqual(partner_form.state_id, self.state_vn_hn, "The method onchange of the field district to fail")
        # 2. Field country
        self.assertEqual(partner_form.country_id, self.country_vn, "The method onchange of the field district to fail")
        
        # Check onchange field state_id
        partner_form.state_id = self.state_vn_tq
        self.assertFalse(partner_form.district_id, "The method onchange of the field state to fail")
        
        # Check onchange field country_id
        partner_form.country_id = self.country_us
        self.assertFalse(partner_form.district_id, "The method onchange of the field state to fail")
        partner_form.save()
    
    def test_32_form_district(self):
        district_form = Form(self.env['res.country.district'], view='viin_base_district.res_country_district_view_form')
        district_form.name = 'District 1'
        district_form.state_id = self.state_vn_hn
        district_form.country_id = self.country_vn
        
        # Check onchange field country_id
        district_form.country_id = self.country_us
        self.assertFalse(district_form.state_id, "The method onchange of the field country to fail")
        
        # Check onchange field state_id
        district_form.state_id = self.state_vn_tq
        self.assertEqual(district_form.country_id, self.country_vn, "The method onchange of the field state to fail")
        district_form.save()

    def test_onchange_parent_with_district(self):
        """
        Check onchange address when parent changed
        """
        # Create new company with state and country from VN
        company = self.env['res.partner'].create({
            'name': 'Company A',
            'company_type': 'company',
            'district_id': self.district_vn_1.id,
            'country_id': self.country_vn.id,
        })

        # Create new partner with state and country from US
        partner = self.env['res.partner'].create({
            'name': 'Partner Test',
            'company_type': 'person',
            'district_id': self.district_1.id,
            'country_id': self.country_us.id,
        })

        # Change parent_id on partner form to new company
        with Form(partner) as f:
            f.parent_id = company

        # Check if partner district is same as company
        self.assertEqual(partner.district_id.id, self.district_vn_1.id, "Partner district is not the same as company !")
