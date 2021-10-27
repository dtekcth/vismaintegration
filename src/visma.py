import json
import toml
import webbrowser
import requests
import time
from base64 import standard_b64encode

config = toml.load("./config.toml")

url_base = config['visma']['api_url']

class InvoiceRow:
    distText = 'Kilometer price for Booking as {}, {}'
    timeText = 'Hour price for Booking as {}, {}'

    def __init__(self, distance, hours, date, drove_as):
        self.distance = distance
        self.hours = hours
        self.day = time.strftime('%Y-%m-%d', date)
        self.drove_as = 'member' if drove_as == 'committee' else drove_as
        self.group = 'non member' if drove_as == 'outsider' else drove_as


    def request_data(self):
        return  [
            {'ArticleId': config['invoice'][f'{self.drove_as}_time_id'], 'IsTextRow': "false", 'Text': self.timeText.format(self.group, self.day), 'UnitPrice': config['invoice'][f'{self.drove_as}_time_price'], 'Quantity': self.hours, 'ReversedConstructionServicesVatFree': False, 'CostCenterItemId1': config['invoice']['kostnadställe']},
            {'ArticleId': config['invoice'][f'{self.drove_as}_distance_id'], 'IsTextRow': "false", 'Text': self.distText.format(self.group, self.day), 'UnitPrice': config['invoice'][f'{self.drove_as}_distance_price'], 'Quantity': self.distance, 'ReversedConstructionServicesVatFree': False, 'CostCenterItemId1': config['invoice']['kostnadställe']}
            ]

    def __str__(self):
        return ( 
            config['invoice'][f'{self.drove_as}_time_price'] + ' kr/h  | ' + 
            str(self.hours).rjust(4,' ') + ' hours |      ' + 
            self.timeText.format(self.group, self.day) + 
            '\n' + 
            config['invoice'][f'{self.drove_as}_distance_price'] + ' kr/km | ' + 
            str(self.distance).rjust(4,' ') + ' km    | ' + 
            self.distText.format(self.group, self.day)
            )

class Kund:
    def __init__(self, kund_data):
        self.id = kund_data['Id']
        self.name = kund_data['Name'].lower()
        self.cin = kund_data['CorporateIdentityNumber']
        self.adress = kund_data['InvoiceAddress1']
        self.postalcode = kund_data['InvoicePostalCode']
        self.city = kund_data['InvoiceCity']

    def __str__(self):
        return ('Name: ' + self.name + ' | ' +
                'Personnummer: ' + self.cin + 
                '\n' + 
                'Adress: ' + self.adress + ',' + 
                self.postalcode + ' ' + self.city
            )


    


def authenticate():
    __browser = webbrowser.get(config['other']['browser'])
    
    __browser.open(config['visma']['identity_url'] + '/connect/authorize?client_id={}&redirect_uri={}&scope={}&state={}&response_type=code&prompt=login'.format(config['visma']['client_ID'], config['visma']['redirect_uri'], config['visma']['scope'], 'pythonCLI'))    

    print("enter \"code\" argument from url")
    code = input()


    credentials = (config['visma']['client_ID'], config['visma']['client_secret'])

    data = {'grant_type': 'authorization_code', 'code': code, 'redirect_uri': config["visma"]["redirect_uri"]}
    
    r = requests.post(config['visma']['identity_url'] + '/connect/token', data, auth=credentials)
    print(r.url)

    
    print(json.dumps(r.json()))
    config['visma']['token'] = r.json()['access_token']

    print(config)
    
    with open('./config.toml', 'w') as f:
        toml.dump(config, f)

    return r

"""
def getOrCreateKund(s, pnr, email):
    kund = getKundByPnr(s, pnr)

    if kund == []:
        return createKund(s, pnr, email)
    else:
        return kund


def createKund(s, pnr, email, kund_info={}):
    def searchKund(s, pnr):
        payload = {'who': pnr, 'countryCode':'SE','usesCompanyCredits':'false','useOptiway':'false'}
        r = s.get(url_base + '/addresses', params=payload)
    
        return r.json()[0]

    if kund_info == {}:
        kund_info = searchKund(s, pnr)
    
    print(kund_info)
    payload = {
            'IsPrivatePerson': str(kund_info['type'] == 'privatperson'), 
            'CorporateIdentityNumber': pnr,
            'InvoiceCity': kund_info['city'],
            'InvoicePostalCode': kund_info['postalCode'],
            'InvoiceAddress1': kund_info['address'],
            'Name': kund_info['name'],
            'IsActive': 'true',
            'EmailAddress': email,
            'TermsOfPaymentId': "8f9a8f7b-5ea9-44c6-9725-9b8a1addb036"
            }

    r = s.post(url_base + '/customers', data=payload)
    return r.json() 

def getKundByPnr(s, pnr):
    params = {'filter': 'CorporateIdentityNumber eq ' + pnr }

    r = s.get(url_base + f'/customers?$filter=CorporateIdentityNumber eq \'{pnr}\'')
    
    if r.json()['Data'] == []:
        return False
    else:
        return r.json()['Data'][0]
"""

def getKunder(s):
    r = s.get(url_base + '/customers?$pagesize=1000')
    kunder = []
    for kund_data in r.json()['Data']:
        kunder.append(Kund(kund_data))

    return kunder





def createInvoice(s, kundId, rows):
    invoice_rows = []

    for row in rows:
        invoice_rows += row.request_data()

    data = {'CustomerId': kundId.id, 'RotReducedInvoicingType': '0', 'Rows': invoice_rows, 'EuThirdParty': True}
    
    r = s.post(url_base + "/customerinvoicedrafts", json=data)
