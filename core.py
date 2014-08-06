#! /mit/sashacf/bin/python3.4

FILE_PATH = '/mit/sashacf/web_scripts/soundchanger'

def reencode(s):
    return s.encode('ascii', 'xmlcharrefreplace').decode()

if __name__ == '__main__':
    print('Content-Type: text/html')
    print('')
    print(FILE_PATH + '/files/' + 'fluf')
    try:
        open(FILE_PATH + '/files/fluf')
    except Exception as e:
        print('noooo', type(e))