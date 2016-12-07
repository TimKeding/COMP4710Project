ID_HERO_FILE ='heroes.ids'
GLOBAL_FIELD_FILE_PREFIX ='globalFieldList.{0}'
try:
    with open(ID_HERO_FILE) as source: pass
except FileNotFoundError as f:
    ID_HERO_FILE ='fieldkit/' +ID_HERO_FILE
    GLOBAL_FIELD_FILE_PREFIX ='fieldkit/' +GLOBAL_FIELD_FILE_PREFIX

def getAllHeroStats():

    # get ID to NAME
    idToName =dict()
    with open(ID_HERO_FILE) as source:
        for line in source:
            line =line.strip()
            if not line: continue

            ID, name =line.split(':')
            idToName[ID] =name

    # create ALL_HERO_STATS
    r =dict()
    for ID in idToName:
        name =idToName[ID]
        r[name] =list()
        with open(GLOBAL_FIELD_FILE_PREFIX.format(ID)) as source:
            for line in source:
                line =line.strip()
                if not line: continue

                label, _ =line.split('|')
                r[name].append(label)

    return r

from difflib import SequenceMatcher
class FieldKeeper:

    idToName =dict()
    with open(ID_HERO_FILE) as source:
        for line in source:
            line =line.strip()
            if not line: continue

            ID, name =line.split(':')
            idToName[ID] =name

    @classmethod
    def getAllHeroStats(cls):
        r =dict()
        for ID in cls.idToName:
            name =cls.idToName[ID]
            r[name] =list()
            with open(GLOBAL_FIELD_FILE_PREFIX.format(ID)) as source:
                for line in source:
                    line =line.strip()
                    if not line: continue

                    label, _ =line.split('|')
                    r[name].append(label)
        return r

    @classmethod
    def __transformKey(cls, key):
        # in case the key is a name
        if key not in cls.idToName:
            key =key.lower()
            for i in cls.idToName:
                name =cls.idToName[i]
                if name ==key:
                    key =i
                    break
        return key

    @classmethod
    def getLibraryForm(cls, field, key):
        # in case the key is a NAME
        if key not in cls.idToName:
            key =key.lower()
            for i in cls.idToName:
                name =cls.idToName[i]
                if name ==key:
                    key =i
                    break
        if not key: return None

        # in case the field exactly matches
        # a library entry
        libraryFields =list()
        with open(GLOBAL_FIELD_FILE_PREFIX.format(key)) as source:
            for line in source:
                line =line.strip()
                if not line: continue

                libField, _ =line.split('|')
                libraryFields.append(libField)
        if field in libraryFields: return field

        # in case a synonym is given
        bestMatch =None
        for l in libraryFields:

            lparts =l.split(' ')
            fparts =field.split(' ')
            # plurally different fields still have the same number of words
            if len(lparts) ==len(fparts):

                # plurality only affects one word
                differences =list(set(lparts).symmetric_difference(set(fparts)))
                if 2 ==len(differences):

                    # plurality only affects the right side of words
                    dl, df =differences
                    if dl[-1] != df[-1]:

                        # the lowest observed ratio of similarity
                        # that correctly identifies pairs as plural
                        # forms of one another is 0.6...
                        similarityRatio =SequenceMatcher(None, dl, df).ratio()
                        if similarityRatio >0.6:

                            # perhaps a better match has already been found
                            if bestMatch:
                                if bestRatio <similarityRatio:
                                    bestMatch =l
                                    bestRatio =similarityRatio

                            else:
                                bestMatch =l
                                bestRatio =similarityRatio

        return bestMatch

    @classmethod
    def getHeader(cls, key):
        key =cls.__transformKey(key)

        header ='Username;SR;'
        allHeroStats =cls.getAllHeroStats()
        heroStats =allHeroStats[cls.idToName[key]]
        header +=';'.join(sorted(heroStats, key=lambda s: s.lower()))

        return header

if __name__=='__main__':
    print('>', FieldKeeper.getLibraryForm('Medals', 'pharah'))
    print('>', FieldKeeper.getLibraryForm('Medals', 'Pharah'))
    print('>', FieldKeeper.getLibraryForm('Turret Destroyed', 'Pharah'))
    print('>', FieldKeeper.getLibraryForm('Enemy Slept', 'Ana'))
    print('>', FieldKeeper.getLibraryForm('Teleporter Pad Destroyed', 'Mercy'))

    print('>', FieldKeeper.getHeader('Reaper'))
