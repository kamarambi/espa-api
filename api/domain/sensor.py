"""
Purpose: module to extract embedded information from product names and supply
configured values for each product
Author: David V. Hill
"""
import os
import re
from collections import namedtuple

import yaml

from api import ProductNotImplemented, __location__
from api.util import julian_date_check, julian_from_date

# Grab details on product restrictions
# Do it here, vs during object instantiation,
# to avoid needless repetition
with open(os.path.join(__location__, 'domain/restricted.yaml')) as f:
    restricted = yaml.load(f.read())

# Grab human-readable product names/categories
with open(os.path.join(__location__, 'domain/products.yaml')) as f:
    products = yaml.load(f.read())

class ProductNames(object):
    def groups(self, staff_role=False):
        """ Gives human-readable mappings and logical-groups to all orderable products"""
        retdata = dict()
        for category_name in products['categories']:
            if category_name not in retdata:
                retdata[category_name] = products['categories'][category_name]
                retdata[category_name]['products'] = dict()
                retdata[category_name]['display_rank'] = products['categories'][category_name]['display_rank']

            prods = {p: v for p, v in products['products'].items()
                     if v['category'] == category_name}
            for product, struct in prods.items():
                # TODO: implement staff_role by currently authenticated user
                # if not staff_role and i in restricted['all']['role']:
                #     continue
                is_plotable = (product in restricted['stats']['products']
                               if product != 'stats' else None)
                rdat = {product: {
                    'is_plotable': is_plotable if product != 'l1' else True,
                    'title': struct['title'],
                    'required_customizations': list(),
                    'display_rank': struct['display_rank']
                }}
                retdata[category_name]['products'].update(rdat)

        return retdata

    def get(self):
        """ Defines the mapping between products and sensor variables
        :return: AllProducts class (namedtuple)
        """
        # API product values
        product_names = tuple(products['products'].keys())
        prods = namedtuple('AllProducts', product_names)
        # Internal code names
        return prods(*product_names)
AllProducts = ProductNames().get()

class SensorProduct(object):
    """Base class for all sensor products"""

    # landsat sceneid, modis tile name, aster granule id, etc.
    product_id = None

    # lt05, le07, mod, myd, etc
    sensor_code = None

    # tm, etm, terra, aqua, etc
    sensor_name = None

    # four digits
    year = None

    # three digits
    doy = None

    # last 5 for LANDSAT, collection # for MODIS
    version = None

    default_resolution_m = None
    default_resolution_dd = None
    default_rows = None
    default_cols = None

    def __init__(self, product_id):
        """Constructor for the SensorProduct base class

        Keyword args:
        product_id -- The product id for the requested product
                      (e.g. Landsat is scene id, Modis is tilename, minus
                      file extension)

        Return:
        None
        """

        self.product_id = product_id
        self.sensor_code = product_id[0:3]


class Modis(SensorProduct):
    """Superclass for all Modis products"""
    short_name = None
    horizontal = None
    vertical = None
    date_acquired = None
    date_produced = None
    input_filename_extension = '.hdf'
    l1_provider = 'lpdaac'

    def __init__(self, product_id):
        super(Modis, self).__init__(product_id)

        parts = product_id.strip().split('.')

        self.short_name = parts[0]
        self.date_acquired = parts[1][1:]
        self.year = self.date_acquired[0:4]
        self.doy = self.date_acquired[4:8]

        __hv = parts[2]
        self.horizontal = __hv[1:3]
        self.vertical = __hv[4:6]
        self.version = parts[3]
        self.date_produced = parts[4]
        self.lta_json_name = self.lta_json_name.format(collection=int(self.version))
        if int(self.version) == 5:
            # MODIS Version 5 dataset does not have a version...
            self.lta_json_name = self.lta_json_name.replace('_V5', '')

    def __repr__(self):
        return 'MODIS: {}'.format(self.__dict__)



class Terra(Modis):
    """Superclass for Terra based Modis products"""

    sensor_name = 'terra'
    products = [AllProducts.l1, AllProducts.stats]


class Aqua(Modis):
    """Superclass for Aqua based Modis products"""
    sensor_name = 'aqua'
    products = [AllProducts.l1, AllProducts.stats]


class Modis09A1(Modis):
    """models modis 09A1"""
    default_resolution_m = 500
    default_resolution_dd = 0.00449155
    default_rows = 2400
    default_cols = 2400


class Modis09GA(Modis):
    """models modis 09GA"""
    default_resolution_m = 1000
    default_resolution_dd = 0.0089831
    default_rows = 1200
    default_cols = 1200


class Modis09GQ(Modis):
    """models modis 09GQ"""
    default_resolution_m = 250
    default_resolution_dd = 0.002245775
    default_rows = 4800
    default_cols = 4800


class Modis09Q1(Modis):
    """models modis 09Q1"""
    default_resolution_m = 250
    default_resolution_dd = 0.002245775
    default_rows = 4800
    default_cols = 4800


class Modis13A1(Modis):
    """models modis 13A1"""
    default_resolution_m = 500
    default_resolution_dd = 0.00449155
    default_rows = 2400
    default_cols = 2400


class Modis13A2(Modis):
    """models modis 13A2"""
    default_resolution_m = 1000
    default_resolution_dd = 0.0089831
    default_rows = 1200
    default_cols = 1200


class Modis13A3(Modis):
    """models modis 13A3"""
    default_resolution_m = 1000
    default_resolution_dd = 0.0089831
    default_rows = 1200
    default_cols = 1200


class Modis13Q1(Modis):
    """models modis 13Q1"""
    default_resolution_m = 250
    default_resolution_dd = 0.002245775
    default_rows = 4800
    default_cols = 4800


class Modis11A1(Modis):
    """models modis 11A1"""
    default_resolution_m = 1000
    default_resolution_dd = 0.0089831
    default_rows = 1200
    default_cols = 1200


class ModisTerra09A1(Terra, Modis09A1):
    """models modis 09A1 from Terra"""
    lta_json_name = 'MODIS_MOD09A1_V{collection}'


class ModisTerra09GA(Terra, Modis09GA):
    """models modis 09GA from Terra"""
    lta_json_name = 'MODIS_MOD09GA_V{collection}'


class ModisTerra09GQ(Terra, Modis09GQ):
    """models modis 09GQ from Terra"""
    lta_json_name = 'MODIS_MOD09GQ_V{collection}'


class ModisTerra09Q1(Terra, Modis09Q1):
    """models modis 09Q1 from Terra"""
    lta_json_name = 'MODIS_MOD09Q1_V{collection}'


class ModisTerra13A1(Terra, Modis13A1):
    """models modis 13A1 from Terra"""
    lta_json_name = 'MODIS_MOD13A1_V{collection}'


class ModisTerra13A2(Terra, Modis13A2):
    """models modis 13A2 from Terra"""
    lta_json_name = 'MODIS_MOD13A2_V{collection}'


class ModisTerra13A3(Terra, Modis13A3):
    """models modis 13A3 from Terra"""
    lta_json_name = 'MODIS_MOD13A3_V{collection}'


class ModisTerra13Q1(Terra, Modis13Q1):
    """models modis 13Q1 from Terra"""
    lta_json_name = 'MODIS_MOD13Q1_V{collection}'


class ModisTerra11A1(Terra, Modis11A1):
    """models modis 11A1 from Terra"""
    lta_json_name = 'MODIS_MOD11A1_V{collection}'


class ModisAqua09A1(Aqua, Modis09A1):
    """models modis 09A1 from Aqua"""
    lta_json_name = 'MODIS_MYD09A1_V{collection}'


class ModisAqua09GA(Aqua, Modis09GA):
    """models modis 09GA from Aqua"""
    lta_json_name = 'MODIS_MYD09GA_V{collection}'


class ModisAqua09GQ(Aqua, Modis09GQ):
    """models modis 09GQ from Aqua"""
    lta_json_name = 'MODIS_MYD09GQ_V{collection}'


class ModisAqua09Q1(Aqua, Modis09Q1):
    """models modis 09Q1 from Aqua"""
    lta_json_name = 'MODIS_MYD09Q1_V{collection}'


class ModisAqua13A1(Aqua, Modis13A1):
    """models modis 13A1 from Aqua"""
    lta_json_name = 'MODIS_MYD13A1_V{collection}'


class ModisAqua13A2(Aqua, Modis13A2):
    """models modis 13A2 from Aqua"""
    lta_json_name = 'MODIS_MYD13A2_V{collection}'


class ModisAqua13A3(Aqua, Modis13A3):
    """models modis 13A3 from Aqua"""
    lta_json_name = 'MODIS_MYD13A3_V{collection}'


class ModisAqua13Q1(Aqua, Modis13Q1):
    """models modis 13Q1 from Aqua"""
    lta_json_name = 'MODIS_MYD13Q1_V{collection}'


class ModisAqua11A1(Aqua, Modis11A1):
    """models modis 11A1 from Aqua"""
    lta_json_name = 'MODIS_MYD11A1_V{collection}'


class Landsat(SensorProduct):
    """Superclass for all landsat based products"""
    path = None
    row = None
    station = None
    lta_product_code = None
    default_resolution_m = 30
    default_resolution_dd = 0.0002695
    default_rows = 11000
    default_cols = 11000
    input_filename_extension = '.tar.gz'
    l1_provider = 'dmid'

    def __init__(self, product_id):
        product_id = product_id.strip()
        super(Landsat, self).__init__(product_id)

        _idlist = product_id.split('_')
        self.year = _idlist[3][:4]
        self.doy = julian_from_date(_idlist[3][:4], _idlist[3][4:6], _idlist[3][6:8])
        self.julian = self.year + self.doy
        self.path = _idlist[2][:3].lstrip('0')
        self.row = _idlist[2][3:].lstrip('0')
        self.correction_level = _idlist[1]
        self.collection_number = _idlist[-2]
        self.collection_category = _idlist[-1]
        self.lta_json_name = self.lta_json_name.format(collection=int(self.collection_number))

    def __repr__(self):
        return 'Landsat: {}'.format(self.__dict__)

    # SR based products are not available for those
    # dates where we are missing auxiliary data
    def sr_date_restricted(self):
        if self.sensor_name in restricted:
            if not julian_date_check(self.julian, restricted[self.sensor_name]['by_date']['sr']):
                return True
        return False


class LandsatTM(Landsat):
    """Models Landsat TM only products"""
    products = [AllProducts.source_metadata, AllProducts.l1, AllProducts.toa, AllProducts.bt, AllProducts.sr, AllProducts.st, AllProducts.swe,
                AllProducts.sr_ndvi, AllProducts.sr_evi, AllProducts.sr_savi, AllProducts.sr_msavi, AllProducts.sr_ndmi,
                AllProducts.sr_nbr, AllProducts.sr_nbr2, AllProducts.stats, AllProducts.pixel_qa]
    lta_name = 'LANDSAT_TM'
    lta_json_name = 'LANDSAT_TM_C{collection}'
    sensor_name = 'tm'

    def __init__(self, product_id):
        super(LandsatTM, self).__init__(product_id)


class LandsatETM(Landsat):
    """Models Landsat ETM only products"""
    products = [AllProducts.source_metadata, AllProducts.l1, AllProducts.toa, AllProducts.bt, AllProducts.sr, AllProducts.st, AllProducts.swe,
                AllProducts.sr_ndvi, AllProducts.sr_evi, AllProducts.sr_savi, AllProducts.sr_msavi, AllProducts.sr_ndmi,
                AllProducts.sr_nbr, AllProducts.sr_nbr2, AllProducts.stats, AllProducts.pixel_qa]
    lta_name = 'LANDSAT_ETM_PLUS'
    lta_json_name = 'LANDSAT_ETM_C{collection}'
    sensor_name = 'etm'

    def __init__(self, product_id):
        super(LandsatETM, self).__init__(product_id)


class LandsatOLITIRS(Landsat):
    """Models Landsat OLI/TIRS only products"""
    products = [AllProducts.source_metadata, AllProducts.l1, AllProducts.toa, AllProducts.bt, AllProducts.sr, AllProducts.st, AllProducts.swe,
                AllProducts.sr_ndvi, AllProducts.sr_evi, AllProducts.sr_savi, AllProducts.sr_msavi, AllProducts.sr_ndmi,
                AllProducts.sr_nbr, AllProducts.sr_nbr2, AllProducts.stats, AllProducts.pixel_qa]
    lta_name = 'LANDSAT_8'
    lta_json_name = 'LANDSAT_8_C{collection}'
    sensor_name = 'olitirs'

    def __init__(self, product_id):
        super(LandsatOLITIRS, self).__init__(product_id)


class LandsatOLI(Landsat):
    """Models Landsat OLI only products"""
    products = [AllProducts.source_metadata, AllProducts.l1, AllProducts.toa, AllProducts.stats, AllProducts.pixel_qa]
    lta_name = 'LANDSAT_8'
    lta_json_name = 'LANDSAT_8_C{collection}'
    sensor_name = 'oli'

    def __init__(self, product_id):
        super(LandsatOLI, self).__init__(product_id)


class LandsatTIRS(Landsat):
    """Models Landsat TIRS only products"""
    lta_name = 'LANDSAT_8'
    lta_json_name = 'LANDSAT_8_C{collection}'
    sensor_name = 'tirs'

    def __init__(self, product_id):
        super(LandsatTIRS, self).__init__(product_id)


class Landsat4(Landsat):
    """Models Landsat 4 only products"""

    def __init__(self, product_id):
        super(Landsat4, self).__init__(product_id)


class Landsat4TM(LandsatTM, Landsat4):
    """Models Landsat 4 TM only products"""
    sensor_name = 'tm4'

    def __init__(self, product_id):
        super(Landsat4TM, self).__init__(product_id)


class Landsat5(Landsat):
    """Models Landsat 5 only products"""

    def __init__(self, product_id):
        super(Landsat5, self).__init__(product_id)


class Landsat5TM(LandsatTM, Landsat5):
    """Models Landsat 5 TM only products"""
    sensor_name = 'tm5'

    def __init__(self, product_id):
        super(Landsat5TM, self).__init__(product_id)


class Landsat7(Landsat):
    """Models Landsat 7 only products"""

    def __init__(self, product_id):
        super(Landsat7, self).__init__(product_id)


class Landsat7ETM(LandsatETM, Landsat7):
    """Models Landsat 7 ETM only products"""
    sensor_name = 'etm7'

    def __init__(self, product_id):
        super(Landsat7ETM, self).__init__(product_id)


class Landsat8(Landsat):
    """Models Landsat 8 only products"""

    def __init__(self, product_id):
        super(Landsat8, self).__init__(product_id)


class Landsat8OLI(LandsatOLI, Landsat8):
    """Models Landsat 8 OLI only products"""
    sensor_name = 'oli8'

    def __init__(self, product_id):
        super(Landsat8OLI, self).__init__(product_id)


class Landsat8TIRS(LandsatTIRS, Landsat8):
    """Models Landsat 8 TIRS only products"""
    sensor_name = 'tirs8'

    def __init__(self, product_id):
        super(Landsat8TIRS, self).__init__(product_id)


class Landsat8OLITIRS(LandsatOLITIRS, Landsat8):
    """Models Landsat 8 OLI/TIRS only products"""
    sensor_name = 'olitirs8'

    def __init__(self, product_id):
        super(Landsat8OLITIRS, self).__init__(product_id)


class SensorCONST(object):
    # shortname: regex, class object, sample product name)
    instances = {
        'tm4_collection': (r'^lt04_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$',
                           Landsat4TM, 'lt04_l1tp_042034_20011103_20160706_01_a1'),

        'tm5_collection': (r'^lt05_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$',
                           Landsat5TM, 'lt05_l1tp_042034_20011103_20160706_01_a1'),

        'etm7_collection': (r'^le07_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$',
                            Landsat7ETM, 'le07_l1tp_042034_20011103_20160706_01_a1'),

        'olitirs8_collection': (r'^lc08_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$',
                                Landsat8OLITIRS, 'lc08_l1tp_042034_20011103_20160706_01_a1'),

        'oli8_collection': (r'^lo08_{1}\w{4}_{1}[0-9]{6}_{1}[0-9]{8}_{1}[0-9]{8}_{1}[0-9]{2}_{1}\w{2}$',
                            Landsat8OLI, 'lo08_l1tp_042034_20011103_20160706_01_a1'),

        'mod09a1': (r'^mod09a1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra09A1, 'mod09a1.A2000072.h02v09.005.2008237032813'),

        'mod09ga': (r'^mod09ga\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra09GA, 'mod09ga.A2000072.h02v09.005.2008237032813'),

        'mod09gq': (r'^mod09gq\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra09GQ, 'mod09gq.A2000072.h02v09.005.2008237032813'),

        'mod09q1': (r'^mod09q1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra09Q1, 'mod09q1.A2000072.h02v09.005.2008237032813'),

        'mod13a1': (r'^mod13a1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra13A1, 'mod13a1.A2000072.h02v09.005.2008237032813'),

        'mod13a2': (r'^mod13a2\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra13A2, 'mod13a2.A2000072.h02v09.005.2008237032813'),

        'mod13a3': (r'^mod13a3\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra13A3, 'mod13a3.A2000072.h02v09.005.2008237032813'),

        'mod13q1': (r'^mod13q1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra13Q1, 'mod13q1.A2000072.h02v09.005.2008237032813'),

        'mod11a1': (r'^mod11a1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisTerra11A1, 'mod11a1.a2000361.h24v03.006.2015111114747'),

        'myd09a1': (r'^myd09a1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua09A1, 'myd09a1.A2000072.h02v09.005.2008237032813'),

        'myd09ga': (r'^myd09ga\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua09GA, 'myd09ga.A2000072.h02v09.005.2008237032813'),

        'myd09gq': (r'^myd09gq\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua09GQ, 'myd09gq.A2000072.h02v09.005.2008237032813'),

        'myd09q1': (r'^myd09q1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua09Q1, 'myd09q1.A2000072.h02v09.005.2008237032813'),

        'myd13a1': (r'^myd13a1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua13A1, 'myd13a1.A2000072.h02v09.005.2008237032813'),

        'myd13a2': (r'^myd13a2\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua13A2, 'myd13a2.A2000072.h02v09.005.2008237032813'),

        'myd13a3': (r'^myd13a3\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua13A3, 'myd13a3.A2000072.h02v09.005.2008237032813'),

        'myd13q1': (r'^myd13q1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua13Q1, 'myd13q1.A2000072.h02v09.005.2008237032813'),

        'myd11a1': (r'^myd11a1\.a\d{7}\.h\d{2}v\d{2}\.00[5-6]\.\d{13}$',
                    ModisAqua11A1, 'myd13q1.A2000072.h02v09.005.2008237032813')
    }


def instance(product_id):
    """
    Supported MODIS products
    MOD09A1 MOD09GA MOD09GQ MOD09Q1 MYD09A1 MYD09GA MYD09GQ MYD09Q1
    MOD13A1 MOD13A2 MOD13A3 MOD13Q1 MYD13A1 MYD13A2 MYD13A3 MYD13Q1

    MODIS FORMAT:   MOD09GQ.A2000072.h02v09.005.2008237032813

    Supported LANDSAT products
    LT04 LT05 LE07 LC08 LO08

    LANDSAT FORMAT: LE07_L1TP_026027_20170912_20171008_01_T1
    """

    # remove known file extensions before comparison
    # do not alter the case of the actual product_id!
    _id = product_id.lower().strip()
    __modis_ext = Modis.input_filename_extension
    __landsat_ext = Landsat.input_filename_extension

    if _id.endswith(__modis_ext):
        index = _id.index(__modis_ext)
        # leave original case intact
        product_id = product_id[0:index]
        _id = _id[0:index]

    elif _id.endswith(__landsat_ext):
        index = _id.index(__landsat_ext)
        # leave original case intact
        product_id = product_id[0:index]
        _id = _id[0:index]

    instances = SensorCONST.instances

    for key in instances.iterkeys():
        if re.match(instances[key][0], _id):
            inst = instances[key][1](product_id.strip())
            inst.shortname = key
            return inst

    msg = u"[{0:s}] is not a supported sensor product".format(product_id)
    raise ProductNotImplemented(msg)


def available_products(input_products):
    """Lists all the available products for each input_product

    Args:
        input_products (iterable): An iterable of input_product names (str)

    Returns:
        dict: { 'tm5': {'products': [output, products],
                       'inputs': [supplied, input, products]},
                'etm7': ... }

    Raises:
        ProductNotImplemented if an unknown product is supplied
    """
    if not hasattr(input_products, '__iter__'):
        raise TypeError('input_products must be iterable')

    result = {}

    for product in input_products:
        try:
            inst = instance(product)
            name = inst.shortname
            if name not in result:
                result[name] = {'products': inst.products,
                                'inputs': [product]}
            else:
                result[name]['inputs'].append(product)
        except ProductNotImplemented:
            if 'not_implemented' not in result:
                result['not_implemented'] = [product]
            else:
                result['not_implemented'].append(product)
    return result
