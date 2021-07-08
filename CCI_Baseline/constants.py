ICD_PATH = 'icd10_cci.csv'
ICD_ID = 'rwd_references.icd10_cci'

DIAGNOSES = '`w2ohcdata.drg.submit_diagnosis`'
DEMO_DATA = '`w2ohcwork.mastering_patients.swoop_Patient_Demographics_Master_sb_20210427`'
CLAIMS_DATA = '`w2ohcdata.drg.submit_payer`'
PROVIDERS = '`w2ohcdata.drg.submit_provider`'
PROCEDURES = '`w2ohcdata.drg.submit_procedure`'
ZIPS = 'uszips.csv'

WEST = ['WA', 'AK', 'OR', 'CA', 'NV', 'AZ', 'HI', 'NM', 'CO', 'UT', 'ID', 'WY', 'MT']
MIDWEST = ['ND', 'SD', 'NE', 'KS', 'MN', 'IA', 'MO', 'WI', 'IL', 'IN', 'OH', 'MI']
NORTHEAST = ['ME', 'VT', 'NH', 'MA', 'RI', 'CT', 'NJ', 'PA', 'NY']
SOUTH = ['TX', 'OK', 'AR', 'LA', 'MS', 'AL', 'FL', 'GA', 'SC', 'NC', 'TN', 'KY', 'WV', 'VA', 'DE', 'MD', 'DC']
REGIONS = {'West':WEST, 'Midwest':MIDWEST, 'Northeast':NORTHEAST, 'South':SOUTH}

AGE_BRACKETS = {'18-39': (18, 39),
                '40-59': (40, 59),
                '60-74': (60, 74),
                '75+': (75, 200)}
CCI_CATS = {'0': 0,
            '4+': 4,
            '3': 3,
            '2': 2,
            '1': 1}

COL_GENDER = 'Pat_Gender'
INDEX_DATE = 'index_date'

CATS = ['year', 'age_group', 'Pat_Gender', 'region', 'cci_cat', 'comorbidity']
TITLES = ['Index Year, n (%)', 'Age Category, n (%)', 'Gender, n(%)', 'Region, n(%)', 'CCI group, n (%)', 'CCI Comorbidity']

