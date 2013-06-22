#! /usr/bin/python3
# -*- coding: UTF-8 -*-

import os,sys
import re
from midiutil.MidiFile3 import MIDIFile

def gregomid():
    entree = FichierTexte(sys.argv[1])
    try:
        sortie = Fichier(sys.argv[2])
    except IndexError:
        sortie = Fichier(os.path.join(entree.dossier,entree.nom) + ".mid")
    gabc = Gabc(entree.contenu)
    print(gabc.partition)
    partition = Partition(gabc = gabc.musique)
    midi = Midi(partition.pitches)
    midi.ecrire(sortie.chemin)

class Gabc:
    def __init__(self,contenu):
        self.contenu = contenu
    @property
    def partition(self):
        resultat = self.contenu
        resultat = re.sub('\n',' ',resultat)
        regex = re.compile('%%')
        resultat = regex.split(resultat)[1]
        return resultat
    @property
    def musique(self):
        resultat = []
        regex = re.compile('[cf][1234]')
        cles = regex.findall(self.partition)
        parties = regex.split(self.partition)[1:]
        for i in range(len(cles)):
            cle = cles[i]
            for n in parties[i]:
                resultat.append((cle,n))
        return resultat

class Partition:
    def __init__(self,**parametres):
        self.b = ''
        if 'partition' in parametres:
            self.pitches = parametres['pitches']
        if 'gabc' in parametres:
            self.pitches = self.g2p(parametres['gabc'])
        if 'bemol' in parametres:
            self.b = self.b + parametres['bemol']
    def g2p(self,gabc):
        notes = "abcdefghijklm"
        episeme = '_'
        point = '.'
        quilisma = 'w'
        speciaux = 'osv'
        barres = '`,;:'
        bemol = "x"
        becarre = "y"
        coupures = '/ '
        pitches = []
        b = '' + self.b
        mot = 0
        neume = 0
        neumeencours = ''
        musique = 0
        for i in range(len(gabc)):
            signe = gabc[i]
            if musique == 1:
                if signe[1].lower() in notes:
                    j = 0
                    s = 0
                    note = Note(gabc = signe, bemol = b)
                    pitches.append(note.pitch)
                    memoire = signe
                elif signe[1] in speciaux:
                    s += 1
                    if s > 1:
                        note = Note(gabc = memoire, bemol = b)
                        pitches.append(note.pitch)
                elif signe[1] == episeme:
                    neumeencours = neume
                    j -= 1
                    pitches[j][1] = 1.5
                elif signe[1] == point:
                    j -= 1
                    pitches[j][1] = 2
                elif signe[1] == quilisma:
                    pitches[-2][1] = 1.8
                elif signe[1] == bemol:
                    b = b + memoire[1]
                    pitches = pitches[:-1]
                elif signe[1] == becarre:
                    re.sub(memoire[1],'',b)
                    pitches = pitches[:-1]
                elif signe[1] in coupures:
                    if pitches[-1][1] < pitches[-2][1]:
                        pitches[-1][1] = pitches[-2][1]
                elif signe[1] in barres or signe[1] in coupures:
                    b = '' + self.b
                    if signe[1] == ';':
                        pitches[-1][1] += .5
                    elif signe[1] == ':':
                        pitches[-1][1] += 1
                elif signe[1] == ')':
                    musique = 0
                    if neumeencours == neume and pitches[-1][1] < pitches[-2][1]:
                        pitches[-1][1] = pitches[-2][1]
            if musique == 0:
                if signe[1] == ' ':
                    mot += 1
                    b = '' + self.b
                elif signe[1] == '(':
                    musique = 1
                    neume += 1
        return pitches

class Note:
    def __init__(self,**parametres):
        self.b = parametres['bemol']
        if 'pitch' in parametres:
            self.pitch = parametres['pitch']
        if 'gabc' in parametres:
            self.pitch = self.g2p(parametres['gabc'])
    def g2p(self,gabc):
        la = 57
        si = la + 2
        do = si + 1
        re = do + 2
        mi = re + 2
        fa = mi + 1
        sol = fa + 2
        octave = 12
        gamme = (la, si, do, re, mi, fa, sol)
        decalage = {
            "c4": 0,
            "c3": 2,
            "c2": 4,
            "c1": 6,
            "f4": 3,
            "f3": 5,
            "f2": 0,
            "f1": 2
        }
        cle = gabc[0]
        note = gabc[1]
        i = decalage[cle] - 1
        o = 0
        notes = {}
        for j in "abcdefghijklm":
            try:
                i += 1
                notes[j] = gamme[i] + o
            except IndexError:
                i -= 7
                o += 12
                notes[j] = gamme[i] + o
        duree = 1
        hauteur = note.lower()
        pitch = notes[hauteur]
        if hauteur in self.b:
            pitch -= 1
        return [pitch,duree]

class Midi:
    def __init__(self,partition):
        piste = 0
        temps = 0
        self.sortieMidi = MIDIFile(1)
        self.sortieMidi.addTrackName(piste,temps,"Gregorien")
        self.sortieMidi.addTempo(piste,temps, 150)
        self.sortieMidi.addProgramChange(piste,0,temps,74)
        
        for note in partition:
            channel = 0
            pitch = note[0]
            duree = note[1]
            volume = 127
            self.sortieMidi.addNote(piste,channel,pitch,temps,duree,volume)
            temps += duree
        
        # And write it to disk.
    def ecrire(self,chemin):
        binfile = open(chemin, 'wb')
        self.sortieMidi.writeFile(binfile)
        binfile.close()

class Fichier:
    def __init__(self,chemin):
        self.dossier = os.path.dirname(chemin)
        self.nom = os.path.splitext(os.path.basename(chemin))[0]
        self.chemin = chemin

class FichierTexte:
    def __init__(self,chemin):
        self.dossier = os.path.dirname(chemin)
        self.nom = os.path.splitext(os.path.basename(chemin))[0]
        self.chemin = chemin
    @property
    def contenu(self):
        fichier = open(self.chemin,'r')
        texte = fichier.read(-1)
        fichier.close()
        return texte

if __name__ == '__main__':
    gregomid()
