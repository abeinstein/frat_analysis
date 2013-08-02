# ae.py (get it? haha)
# Script that will tell you which of your friends are AEPi's! (in case you forgot)

import facebook
import networkx as nx
import pickle
from collections import defaultdict


# Change this to your access token by going here: https://developers.facebook.com/tools/explorer
# You need to give yourself access to your friends likes, gender, and your own likes.
ACCESS_TOKEN = "CAACEdEose0cBAAsW0LqyfjEwEGK34aaoC33pjWzkopmpjMViS1wJqqQ2nolqccqpBSFdAGZBSGHz1mcQKOe64FS6g0txLAPgRt67mA4KDSMWxpV7P04MsgZCq1AuxN2hcyX468NPHAUm8kfSUOhzXp8ATpoq4ZD"

AEPI_KEYWORDS = ['AEPi', 'Alpha Epsilon Pi']
PICKLE_FILE = 'fb_graph.pkl'
CAND_PICKLE_FILE = 'aepi_candidates.pkl'
THRESHOLD_CONSTANT = 0.67


def aepi_classifier(fb_graph, nx_graph):
    ''' AEPi classifier:
    First, it checks everyones likes to get a set of AEPi candidates.

    Then, we do some basic cluster analysis to get others in that cluster.
    '''
    friends_dict = fb_graph.get_connections("me", "friends")['data']
    aepi_candidates = set()
    try:
        aepi_candidates = pickle.load(open(CAND_PICKLE_FILE, 'rb'))
    except:
        # Get preliminary set of candidates
        counter = 0
        num_friends = len(friends_dict)
        for friend in friends_dict:
            counter += 1
            print "%d / %d" % (counter, num_friends)
            friend = fb_graph.get_object(friend['id'])

            # Preliminary checks:
            try:
                if friend["gender"] == "female":
                    continue
            except KeyError:
                pass

            # Check their likes to if AEPi is mentioned
            friend_likes = fb_graph.get_connections(friend["id"], "likes")
            for like in friend_likes['data']:
                if aepi_related(like['name']):
                    aepi_candidates.add(friend['id'])
                    continue

        pickle.dump(aepi_candidates, open(CAND_PICKLE_FILE, 'wb'))

    # Generate mutual friend list!
    mutual_friends = defaultdict(int)
    for cand in aepi_candidates:
        cand_mfriends = nx_graph.neighbors(cand)
        for cf_id in cand_mfriends:
            mutual_friends[cf_id] += 1

    top_mutual_friends = sorted(mutual_friends.keys(), key=lambda k: mutual_friends[k], reverse=True)
    aepis = set()
    threshold = mutual_friends[top_mutual_friends[0]] * THRESHOLD_CONSTANT
    for t in top_mutual_friends:
        if mutual_friends[t] > threshold:
            obj = identify(fb_graph, t)
            if obj:
                print obj['name']
                aepis.add(obj['name'])
    return aepis


def identify(fb_graph, uid):
    try:
        obj = fb_graph.get_object(uid)
        return obj
    except facebook.GraphAPIError:
        return None


def aepi_related(like_name):
    '''Takes a string, checks to see if AEPi related'''
    for kw in AEPI_KEYWORDS:
        if kw in like_name:
            return True
    return False


def get_graph(fb_graph):
    friends = fb_graph.get_connections("me", "friends")["data"]
    friendGraphObject = nx.Graph()
    current = 0
    total = len(friends)
    for friend in friends:
        mutualFriends = fb_graph.fql("SELECT uid1, uid2 FROM friend " +  
                                     "where uid1=" + friend['id'] + 
                                     "and uid2 in (SELECT uid2 FROM friend where uid1=me())")
        friendGraphObject.add_edges_from([(mf['uid1'], mf['uid2']) for mf in mutualFriends['data']])
        current += 1
        print(str(current) + "/" + str(total))

    nx.write_gpickle(friendGraphObject, PICKLE_FILE)
    return friendGraphObject


def run():
    fb_graph = facebook.GraphAPI(ACCESS_TOKEN)
    try:
        nx_graph = nx.read_gpickle(PICKLE_FILE)
    except IOError:
        nx_graph = get_graph(fb_graph)
    aepis = aepi_classifier(fb_graph, nx_graph)
    print aepis


if __name__ == "__main__":
    run()
