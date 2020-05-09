import cv2
import os
from midiutil.MidiFile import MIDIFile  #Import the library

import random
import os
import subprocess
import time

#used to still get a return even if the index is > array
def cyclicfind(numin, array):
    while(numin > len(array)):
        numin = numin - len(array)
    return array[numin]

#makes large jumps between notes less likely
def getNote(numin, lastnoteindex, key, intervals):
    dist = [2, 5, 9, 14, 19, 25, 32, 40, 60, 68, 75, 81, 86, 91, 95, 98, 100]
    diff = [-8, -7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]
    #print("Numin:",numin)
    i = 0;
    while numin > dist[i]:
        i = i + 1
        
    noteindex = lastnoteindex + diff[i]
    tempindex = noteindex;
    octave = 0;
    while tempindex > 6:
        tempindex = tempindex - 7
        octave = octave + 1
        
    while tempindex < 0:
        tempindex = tempindex + 7
        octave = octave - 1
    #Return Note then noteindex
    #print('Tempindex:',tempindex)
    return key + intervals[tempindex] + 12*octave, noteindex
    
    

def makeAndPlaySong(inString):
    
    #Code to Get Numbers from URL
    try:
        url = inString.split('//')[1]
        urldotsplit = url.split('.',2)
        domain = urldotsplit[1]
        afterdomain = urldotsplit[2]
        afterdomainsplit = afterdomain.split('/')
        domainsuffix = afterdomainsplit[0]
        path = afterdomainsplit[1]
    except:
        try:
            url = inString.split('//')[1]
            urldotsplit = url.split('.',2)
            domain = urldotsplit[1]
            domainsuffix = urldotsplit[2]
            path = ''
            print('Using Vanilla Url')
        except:
            try:
                url = inString.split('//')[1]
                urldotsplit = url.split('.',1)
                domain = urldotsplit[0]
                domainsuffix = urldotsplit[1]
                path = ''
                print('Using Vanilla Url that has no www.')
            except:
                print('Invalid Url, resorting to failsafe')
                domain = inString[:8]
                domainsuffix = inString[8:11]
                path = inString[11:]
    
    domainnum = str(int.from_bytes(str.encode(domain), byteorder='little')*5)
    domainsuffixnum = str(int.from_bytes(str.encode(domainsuffix), byteorder='little')*5)
    pathnum  = str(int.from_bytes(str.encode(path), byteorder='little')*5)
    #print(domainnum)
    #print(domainsuffixnum)
    print('PathNum',pathnum)
    originaldomainnum = domainnum
    
    
    #Code to build Music using Numbers
    musicpath = '/home/pi/Jenme489y/qrcodereader/music/'
    fileloc = musicpath + domain + path + '.mid'
    
    #scales
    majorints = [0, 2, 4, 5, 7, 9, 11]
    harmminorints = [0, 2, 3, 5, 7, 8, 11]
    jazzints = [0, 3, 5, 6, 6, 7, 10]
    intervals = [majorints, harmminorints, jazzints]
    tempos = [40, 60, 80, 90, 100, 110, 120, 130, 150, 200]
    durations = [.25, .5, .5, 1, 1, 1, 1.5, 2, 2, 4]
    
    
    key = 60 + int(domainnum[0]) #key
    print('Key:',key)
    domainnum = domainnum[1:]
    interval = cyclicfind(int(domainnum[0]), intervals) #scale
    print('Interval:',interval)
    domainnum = domainnum[1:]
    tempo = tempos[int(domainnum[0])]#speed
    domainnum = domainnum[1:]
    melodyvoice = int(domainnum[0:2])#instrument
    domainnum = domainnum[2:]
    
    mididata = MIDIFile(1)
    mididata.addTrackName(0,0,'Melody')
    mididata.addProgramChange(0,0,0,melodyvoice)
    mididata.addTempo(0,0,tempo)
    
    notes = []
    notedurations = []
    totalduration = 8;
    duration = 0;
    priornoteindex = key;
    #make the main phrase
    while(duration<totalduration):
        if(len(domainnum)<4):
            domainnum = domainnum + originaldomainnum
        note, priornoteindex = getNote(int(domainnum[0:2]), priornoteindex, key, interval)
        notes.append(note)
        domainnum = domainnum[2:]
        noteduration = durations[int(domainnum[0])]
        if ((noteduration + duration) > totalduration):
            notes = notes[:(len(notes)-1)]
            duration = totalduration
            break   
        notedurations.append(noteduration)
        duration = duration + noteduration
    
    #addvarience of the path
    try:
        for i in range(len(pathnum)-2):
            print(i)
            if int(pathnum[i]) == 0:
                mididata.addProgramChange(0,0,0,int(pathnum[i+1]))
            elif int(pathnum[i]) < 5:
                notes[int(pathnum[i+1])] = notes[int(pathnum[i+1])] - int(pathnum[i])
            elif int(pathnum[i]) < 9:
                notes[int(pathnum[i+1])] = notes[int(pathnum[i+1])] + int(pathnum[i])
            else:
                mididata.addTempo(0,0,tempos[int(pathnum[i+1])])
    except:  
        pass
    
    notestarttime = 0
    volume = 100
    for i in range(len(notes)):
        if(len(domainnum)<2):
            domainnum = domainnum + originaldomainnum
        mididata.addNote(0,0,notes[i],notestarttime,notedurations[i],(volume-5+int(domainnum[0])*2),annotation=None)
        notestarttime = notestarttime + notedurations[i]
        domainnum = domainnum[1:]
    
    
    #Play Midi File
    if (os.path.isfile(fileloc)) :
        pass
    fobject = open(fileloc, 'wb')
    mididata.writeFile(fobject)
    fobject.close()
    subprocess.call(['timidity',fileloc])
    
    
#QR Code Detection
command = 'sudo modprobe bcm2835-v4l2'
os.system(command)

cap = cv2.VideoCapture(0)

detector = cv2.QRCodeDetector()

lastdata = None

while True:
    
    check, img = cap.read()
    
    data, bbox, _ = detector.detectAndDecode(img)
    
    if(bbox is not None):
        for i in range(len(bbox)):
            cv2.line(img, tuple(bbox[i][0]), tuple(bbox[(i+1) % len(bbox)][0]), color = (0, 255, 0), thickness = 4)
            cv2.putText(img, data, (int(bbox[0][0][0]), int(bbox[0][0][1]) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    cv2.imshow("QR Code Playing", img)
    
    if data:
        if data != lastdata: #Avoid repeating the same URL Song
            makeAndPlaySong(data) 
            lastdata = data
    
    if(cv2.waitKey(1) == ord("q")):
        break
    
cap.release()
cv2.destroyAllWindows()