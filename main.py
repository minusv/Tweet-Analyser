import tweepy, re, requests, sys, threading, time, os
from collections import defaultdict
from urllib.parse import urlsplit

CONSUMER_KEY = os.environ['CONSUMER_KEY']
CONSUMER_SECRET = os.environ['CONSUMER_SECRET']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']
ACCESS_TOKEN_SECRET = os.environ['ACCESS_TOKEN_SECRET']

# Setup tweepy to authenticate with Twitter credentials:
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Creating api to connect to twitter with creadentials
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
# wait_on_rate_limit= True;  will make the api to automatically wait for rate limits to replenish
# wait_on_rate_limit_notify= True;  will make the api  to print a notification when Tweepy is waiting for rate limits to replenish

users = defaultdict(list) #to store user report
domains = defaultdict(list) #to store link report

class StreamListener(tweepy.StreamListener):

    session = requests.session() # so connections are recycled

    def update_users(self, status):
        #to add new records to user report

        global users
        users[status.user.screen_name].append(int(time.time()))

    def unshorten_url(self, url):
        #to unshort any url and to update link report

        global domains
        try:
            response = self.session.head(url, allow_redirects=True) #getting url from shortened url
            base_url = "{0.netloc}".format(urlsplit(response.url)) #getting network location
            domains[base_url].append(int(time.time()))
            
        except requests.exceptions.InvalidURL:
            pass

        except KeyboardInterrupt:
            #terminating program on keyboard interrupt
            print("Terminating!")
            sys.exit()

        except Exception as ex:
            #catching any other exception

            print("Request failed!", ex.__class__.__name__)
            print("Try Again Later!")
            sys.exit()

    def get_url(self, status):
        #to get url from tweet

        #using regular expression:        
        regex = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        match = re.findall(regex, status.text)
        for url in match:
            self.unshorten_url(url)


    def on_status(self, status):
        #perform following function on every new tweet
        self.update_users(status)
        self.get_url(status)
        
    def on_error(self, status_code):
        if status_code == 420:
            print("Connection ERROR! Try Again!")
            sys.exit()

class PrintReport(object):
    #Thread to print reports every 1 minute.

    def __init__(self):
        self.interval = 60
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        thread.start() # Start the execution

    def generate_user_report(self):
        #Printing user report
        global users
        if users == {}:
            pass
        else:
            print("=========================================================================")
            print("USER_NAME \t\t NO_OF_TWEETS\n")
            currentTime = int(time.time())
            for user in list(users):
                userCount = 0
                for entry in users[user]:
                    if currentTime - entry <= 300: #checking if an entry was made less than or equal to 5 min ago.
                        userCount += 1
                    else:
                        users[user].remove(entry) #removing older entries
                if userCount != 0:
                    print("{}\t\t{}".format(user,userCount))
        print("\n")

    def generate_link_report(self):
        #Printing link report
        global domains
        if domains == {}:
            pass
        else:
            currentTime = int(time.time())
            tempDomainRecord = {} #to store domains of last 5 minutes
            for domain in list(domains):
                domainCount = 0
                for entry in domains[domain]:
                    if currentTime - entry <= 300: #checking if an entry was made less than or equal to 5 min ago.
                        domainCount += 1
                    else:
                        domains[domain].remove(entry) #removing older entries
                    if domainCount != 0:
                        tempDomainRecord[domain] = domainCount
            print("--------------------------------------------------------------------------")
            print("TOTAL UNIQUE DOMAINS = ",len(tempDomainRecord))
            print("\n")
            #Printing domains in sorted order
            sorted_domains = sorted(((count,domain_name) for domain_name,count in tempDomainRecord.items()), reverse=True)
            for domain in sorted_domains:
                print(domain)

        print("=========================================================================")


    def run(self):
        #Running thread
        while(True):
            self.generate_user_report()
            self.generate_link_report()
            time.sleep(self.interval) #thread will sleep for 60s

        print("Task Completed!")
        sys.exit()

#===========================================MAIN=================================================
if __name__ == "__main__":

    keyword = input("Enter the keyword: ")

    printReport = PrintReport() #Starting print thread to generate report every 60s
    stream_listener = StreamListener() #Creating object for twitter stream

    try:
        stream = tweepy.Stream(auth=api.auth, listener=stream_listener) #starting twitter stream
        stream.filter(track=[keyword],languages=["en"])

    except KeyboardInterrupt:
            #terminating program on keyboard interrupt
            print("Terminating!")
            sys.exit()
            
    except Exception as ex:
        print("ERROR:", ex.__class__.__name__)
        print("Terminating!")
        sys.exit()
