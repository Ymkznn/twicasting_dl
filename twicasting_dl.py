import requests
from bs4 import BeautifulSoup 
import json
import os
import threading
import tempfile

filepath = os.path.abspath(os.getcwd())
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.53'
}
cookies = {}
illegal_character = ['\\','/',':','*','?','"','<','>','|']
thread_semaphore = threading.Semaphore(500)#THREAD_MAX = 500

def main():
    if not os.system('where ffmpeg'):
        print('ffmpeg installed.')
    else:
        print("Can't find ffmpeg. Please install ffmpeg.")
        return
    twit = requests.session() #set session
    Password = {} #store password
    url = input('Stream url: ') #get stream url
    
    try:
        response = twit.get(url,headers = headers)
        if response.text.find('Enter the secret word to access.')!=-1: #if is private stream
            password = input('password: ')
            Password['password'] = password
            response = twit.post(url,data = Password,headers = headers) #request again
        else:
            cookies['did'] = response.cookies['did']
            response = twit.get(url,cookies = cookies,headers = headers) #set cookie
        response = BeautifulSoup(response.text,'html.parser')
    except:
        print('Error link.')
        return
    try:
        title = response.find('span',class_='tw-player-page__title-editor-value').getText() #get stream title
        title = reform(title)

        master_m3u8_url = response.find('div',class_='tw-player__body tw-html5-player')
        master_m3u8_url = json.loads(master_m3u8_url.find('video').get('data-movie-playlist'))['2'][0]['source']['url'] 
        master_m3u8 = twit.get(master_m3u8_url,headers = headers) #get master.m3u8

        default_url = '/'.join(master_m3u8_url.split('/')[:3]) #default https

        media_m3u8_url = default_url+master_m3u8.text.split('\n')[-2]
        media_m3u8 = twit.get(media_m3u8_url,headers = headers) #get media.m3u8

        replace_key = '/'+'/'.join(media_m3u8_url.split('/')[3:-1])+'/' #for local m3u8 writing

        with tempfile.TemporaryDirectory() as temp:
            local_master_m3u8 = master_m3u8.text.replace(replace_key, temp+'\\')
            with open('{}\\\master.m3u8'.format(temp),'w') as m3u8:
                m3u8.write(local_master_m3u8.replace('\\', '\\\\'))
            local_media_m3u8 = media_m3u8.text.replace(replace_key, temp+'\\')
            with open('{}\\media.m3u8'.format(temp),'w') as m3u8:
                m3u8.write(local_media_m3u8.replace('\\', '\\\\'))
            
            media_m3u8 = media_m3u8.text.split('\n') #split for urls
            Threads = []
            init = 0
            media = 0
            for part in media_m3u8:
                if part.find('init')!=-1:
                    download(default_url+replace_key+'init.{}.mp4'.format(init),'init.{}'.format(init),twit,temp)
                    init+=1
                if part.find('#')==-1 and len(part)!=0:
                    t = threading.Thread(target=download,args=(default_url+part,'media.{}'.format(media),twit,temp))
                    Threads.append(t)
                    media+=1
                else:
                    pass
            
            for i in Threads:
                i.start()
            for i in Threads:
                i.join()
            os.system('ffmpeg -i "{}\\master.m3u8" -c copy "{}\\{}.mp4"'.format(temp,filepath,title))
    except:
        print('Password error.')
        return

def download(url,name,twit,temp_local):
    thread_semaphore.acquire()
    try:
        source = twit.get(url,headers = headers).content
        with open('{}\\{}.mp4'.format(temp_local,name),'wb') as file:
            print('writing {}.mp4'.format(name))
            file.write(source)
    except:
        print('file {} time out, try again.'.format(name))
        download(url,name,twit,temp_local)
    thread_semaphore.release()

def reform(title):
    for illegal in illegal_character:
        title = title.replace(illegal,chr(ord(illegal)+65248))
    return title

if __name__ == '__main__':
    main()
    os.system('pause')
    