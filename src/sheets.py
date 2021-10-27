import toml
import csv
import time
from datetime import date

config = toml.load("./config.toml")

class Drive:
    def __init__(self, drive_data, prev_meter):
        if drive_data['Drove as...'] == 'Committé under the computer division':
            self.drove_as = 'committee'
        elif drive_data['Drove as...'] == 'Member of the computer division':
            self.drove_as = 'member'
        elif drive_data['Drove as...'] == 'DBus Patet':
            self.drove_as = 'dbus'
        elif drive_data['Drove as...'] == 'outsider':
            self.drove_as = 'outsider'
        else:
            self.drove_as = 'INVALID'

        # Will fail if i == 0
        self.distance = str(int(drive_data['Meter indication']) - int(prev_meter))

        self.timestamp = time.strptime(drive_data['Tidstämpel'], '%Y-%m-%d %H.%M.%S' ) 
        self.email = drive_data['E-postadress']
        self.rented_hours = drive_data['Number of rented hours']
        self.name = drive_data['Booker']

    def between(self, start, stop):
        return self.timestamp >= start and self.timestamp <= stop

    def __str__(self):
        return('Date: ' + time.strftime('%Y-%m-%d', self.timestamp) + 
            ' | Email: ' + str(self.email) + 
            ' | Dist: ' + str(self.distance).rjust(4, ' ') + 'km' +
            ' | Time: ' + str(self.rented_hours).rjust(4,' ') + 'h ' +
            ' | Booker: ' + str(self.name)
            )

class Personnummer:

    def __init__(self, pnrstr):
        i = len(pnrstr)
        self.x = pnrstr[i-4:i] 
        i -= 4

        if pnrstr[i-1] == '-':
            i -= 1

        self.d = pnrstr[i-2:i]
        i -= 2

        self.m = pnrstr[i-2:i]
        i -= 2
        if int(pnrstr[i-2:i]) > int(str(date.today().year)[2:]):
            self.y = '19' + pnrstr[i-2:i]
        else:
            self.y = '20' + pnrstr[i-2:i]

    def __str__(self):
        return f'{self.y}{self.m}{self.d}-{self.x}'

    def compare(self, pnr):
        if type(pnr) != Personnummer:
            try:
                n_pnr = Personnummer(pnr)
            except:
                return False
        else:
            n_pnr = pnr
                
        return (
                self.y == n_pnr.y and 
                self.m == n_pnr.m and 
                self.d == n_pnr.d and 
                self.x == n_pnr.x
            )

class Driver:
    
    def __init__(self, driver_info):
        self.time = driver_info['Tidstämpel']
        self.email = driver_info['E-postadress']
        self.name = (driver_info['First name'] + ' ' + driver_info['Last name']).lower()
        self.pnr = Personnummer(driver_info['National identification number(Personnummer)'])
        self.member = driver_info['I am a member of the student division of computer science and engineering']
        self.other_org = driver_info['I belong to an organization outside of the student division of computer science and engineering']
        self.org_name = driver_info['Name']
        self.org_number = driver_info['Corporate Identity Number(Organisationsnummer)']
        self.invoice_email = driver_info['E-Mail for invoice']

    def __str__(self):
        print(self.name)
        return ( 
        'Name: ' + str(self.name) +
        '| Email: ' + self.email +
        '| Personnummer: ' + print(self.pnr) +
        '| Other org.: ' + self.other_org +
        '| Org. number: ' + self.org_number
        )


def parseKorjournal(start,stop):
    drives = []
    with open(config['sheets']['korjournal']) as file:
        rows = list(csv.DictReader(file))
         
        for i in range(len(rows)):
            if i == 0:
                last_meter = config['sheets']['meter_indication_base']
            else:
                last_meter = rows[i-1]['Meter indication']

            drive = Drive(rows[i], last_meter)

            if drive.between(start,stop):
                drives.append(drive)

    return sorted(drives, key=lambda d: d.email)

def parseDrivers():
    drivers = []
    with open(config['sheets']['drivers']) as file:
        rows = list(csv.DictReader(file))
         
        for row in rows:
            if row['Skrivit kontrakt? (använd \'x\')'] == 'x':
                drivers.append(Driver(row))

    return sorted(drivers, key=lambda d: d.email)


def invoiceStarted(drive, invoices_data):
    for i,invoice in enumerate(invoices_data[drive.drove_as]):
        if drive.drove_as == 'committee':
            if invoice['name'] == drive.name:
                return i
        else:
            if invoice['name'] == drive.email:
                return i
    return -1 


def startInvoice(drive, invoice_rows, drivers, kunder):

    if drive.drove_as == 'committee':
        invoice_name = drive.name
        kundId = False
        matching_drivers = [] 
    else:
        invoice_name = drive.email
        matching_drivers = list(filter(lambda d: d.email == drive.email, drivers))

        if len(matching_drivers) == 1:
            if drive.drove_as == 'outsider' and drive.other_org == 'Yes':
                matching_kunder = list(filter(lambda k: k.cin == matching_drivers[0].org_number, kunder))
            else:
                matching_kunder = list(filter(lambda k: matching_drivers[0].pnr.compare(k.cin), kunder))

            if len(matching_kunder) == 1:
                kundId = matching_kunder[0]
            else:
                kundId = False
        else:
            kundId = False

    return {
        'name': invoice_name,
        'drives': [drive],
        'kundId': kundId,
        'driver': matching_drivers[0] if len(matching_drivers) == 1 else False,
        'rows': [invoice_rows]
        }
