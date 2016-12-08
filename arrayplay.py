# transform data to all integers

# usage
#
# python arrayplay.py file1, file2, file3, ...
import datetime
LOG_FILE ='ERR.LOG'
with open(LOG_FILE, 'a') as sink:
    sink.write('\n{0}\n'.format(datetime.datetime.now().time()))
def log(msg):
    with open(LOG_FILE, 'a') as sink:
        sink.write('{0}\n'.format(msg))

def isolateHero(string):
    _, hero =string.split('_')
    return hero

def isolatePlatform(string):
    platform, _ =string.split('_')
    if '/' in platform:
        platform =platform.split('/')[-1]
    return platform

def toFloatOrInt(string):

    r =string
    if '%' in string:
        string =string[:-1]
        i =int(string)
        f =float(i)/100
        r =f

    elif ',' in string:
        string =string.replace(',', '')
        f =float(string)
        r =f

    elif ':' in string:
        timeparts =string.split(':')

        if 3 ==len(timeparts):
            hours, minutes, seconds =timeparts
            sumSeconds =int(seconds)
            sumSeconds +=int(minutes) *60
            sumSeconds +=int(hours) *3600
            r =sumSeconds

        elif 2 ==len(timeparts):
            minutes, seconds =timeparts
            sumSeconds =int(seconds)
            sumSeconds +=int(minutes) *60
            r =sumSeconds

    elif 'hour' in string:
        numHours, _ =string.split(' ')
        numSeconds =int(numHours) *3600
        r =numSeconds

    elif 'minute' in string:
        numMinutes, _ =string.split(' ')
        numSeconds =int(numMinutes) *60
        r =numSeconds

    elif 'second' in string:
        numSeconds, _ =string.split(' ')
        numSeconds =float(numSeconds)
        r =numSeconds

    elif '--' ==string:
        r =0

    else:
        r =float(string)

    if not (isinstance(r, int) or isinstance(r, float)):
        log('uncovered string val in toFloatOrInt; {0}'.format(string))
        assert(isinstance(r, int) or isinstance(r, float))

    return r

import sys
import numpy as np
from fieldkit.fieldkit import FieldKeeper
from sklearn.cluster import AffinityPropagation
import matplotlib.pyplot as plt

NUM_IDOL_CLUSTERS =4
MIN_IDOL_CLUSTER_SIZE =8
if __name__=='__main__':

    args =sys.argv[1:]

    # check all the same hero
    if 1 != len(set(map(isolateHero, args))):
        log('different heroes used; aborting')
        exit()

    # require different platforms
    if len(args) != len(set(map(isolatePlatform, args))):
        log('found multiple instances of same platform; aborting')
        exit()

    # create 2d list
    globalData =list()
    for inFile in args:
        with open(inFile) as source:
            for line in source:
                line =line.strip()
                if not line: continue

                namelessLine =';'.join(line.split(';')[1:])

                # turn all values into a float or int
                nonFloatOrIntFields =namelessLine.split(';')
                floatOrIntFields =list()
                for v in nonFloatOrIntFields:
                    v =toFloatOrInt(v)
                    if '--' ==v:
                        log('weird value; --;<BEGIN>\nline\n<END>')
                    floatOrIntFields.append(v)

                globalData.append(floatOrIntFields)

    # create 2d array
    arr =np.array(globalData)
    print(arr)

    #--------------------------------------------------------------------------
    # mining stuff
    #--------------------------------------------------------------------------

    # fit with Affinity Propagation
    ap =AffinityPropagation().fit(arr)

    # ap.cluster_centers_indices
    # returns a list
    # len(list) ==number of clusters
    # v =list[0]
    #   v is the idx in **arr** of cluster ZERO's medoid
    #   arr[v] is cluster ZERO's medoid
    clusterMedoids =ap.cluster_centers_indices_
    print('num clusters: {0}'.format(len(clusterMedoids)))    
    print(clusterMedoids)

    # labels_
    # returns a list
    #
    # v =list[0]
    #   v is the cluster that the FIRST member of arr belongs to
    #   arr[0] belongs to cluster v
    labels =ap.labels_
    print(labels)
    print('len of labels: {0}'.format(len(labels)))

    # collect the users into buckets
    clusterToUserList =dict()
    for idx in range(len(labels)):
        arrElement =arr[idx]
        label =labels[idx]
        if label not in clusterToUserList:
            clusterToUserList[label] =list()
        clusterToUserList[label].append(arrElement)

    # cluster(x) vs winrate(y)
    # xvals should be ~2K long (len arr == num users)
    # yvals should be ==len(yval)
    xvals =list()
    yvals =list()
    for clusterIdx in clusterToUserList:
        for user in clusterToUserList[clusterIdx]:
            xvals.append(clusterIdx)
            yvals.append(user[-1])
    plt.close('all')
    plt.figure(1)
    plt.clf()
    plt.plot(xvals, yvals, 'x')

    # show the global average
    mean =np.mean(yvals)
    plt.axhline(mean, color='g')

    # show the average winrate per cluster
    xvals =list()
    yvals =list()
    clusterIdxSRPairList =list()
    for clusterIdx in clusterToUserList:
        srList =list()
        for user in clusterToUserList[clusterIdx]:
            srList.append(user[0])
        mean =np.mean(srList)
        xvals.append(clusterIdx)
        yvals.append(mean)
        # a choice to exclude exemplary individuals
        if len(clusterToUserList[clusterIdx]) >MIN_IDOL_CLUSTER_SIZE:
            clusterIdxSRPairList.append((clusterIdx, mean))
    plt.plot(xvals, yvals, 'r+')

    # find the 4 highest multi member clusters
    decreasingPairs =sorted(clusterIdxSRPairList, key=lambda x: x[1], reverse=True)
    for i in range(NUM_IDOL_CLUSTERS):
        clusterIdx =decreasingPairs[i][0]
        plt.axvline(clusterIdx, linewidth=10, alpha=0.1)
    print('high sr clusters: {0}'.format((' '.join(str(e[0]) for e in decreasingPairs[:4]))))

    # for each dimension, plot like before
    # highlight these four
    print('num dimensions: {0}'.format(len(arr[0])))
    numDimensions =len(arr[0])
    header =FieldKeeper.getHeader('zenyatta')
    headerFields =header.split(';')
    headerFields =headerFields[1:]
    for d in range(numDimensions):
        plt.figure()
        plt.clf()
        xvals =list()
        yvals =list()
        for clusterIdx in clusterToUserList:
            for user in clusterToUserList[clusterIdx]:
                xvals.append(clusterIdx)
                yvals.append(user[d])
        plt.plot(xvals, yvals, 'x')
        # average
        xvals =list()
        yvals =list()
        for clusterIdx in clusterToUserList:
            valList =list()
            for user in clusterToUserList[clusterIdx]:
                valList.append(user[d])
            mean =np.mean(valList)
            xvals.append(clusterIdx)
            yvals.append(mean)
        plt.plot(xvals, yvals, 'r+')
        for i in range(NUM_IDOL_CLUSTERS):
            clusterIdx =decreasingPairs[i][0]
            plt.axvline(clusterIdx, linewidth =10, alpha =0.1)
        try:
            plt.ylabel(headerFields[d])
        except IndexError as i:
            print('error idx: {0}'.format(d))
        mean =np.mean(yvals)
        plt.axhline(mean, color ='g')

    plt.show()


