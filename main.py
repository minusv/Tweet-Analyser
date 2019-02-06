import tweepy, re, requests, sys, threading, time
from collections import defaultdict
from urllib.parse import urlsplit

CONSUMER_KEY = "w7mLMuaqhImPH2AbHiW596lT4"
CONSUMER_SECRET = "uYAHdGhYFTwMDRXj7wTdlkCx87iFWzavVm0O1DZaniHAjKkqtx"
ACCESS_TOKEN = "1044217500525895680-1TE2u4GUr72MxLWDm1IWt41X4JK1ma"
ACCESS_TOKEN_SECRET = "RFxeEi6zLmQTFOhJ0HIYp3MK49B39MmJkk69Dvg9Lt3Eg"

# Setup tweepy to authenticate with Twitter credentials:
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

# Creating api to connect to twitter with creadentials
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
# wait_on_rate_limit= True;  will make the api to automatically wait for rate limits to replenish
# wait_on_rate_limit_notify= True;  will make the api  to print a notification when Tweepy is waiting for rate limits to replenish

users = defaultdict(int) #to store user report
domains = defaultdict(int) #to store link report

class StreamListener(tweepy.StreamListener):

    session = requests.session() # so connections are recycled

    def update_users(self, status):
        #to add new records to user report

        global users
        users[status.user.screen_name] += 1

    def unshorten_url(self, url):
        #to unshort any url and to update link report

        global domains
        try:
            response = self.session.head(url, allow_redirects=True) #getting url from shortened url
            base_url = "{0.netloc}".format(urlsplit(response.url)) #getting network location
            domains[base_url] += 1
            
        except requests.exceptions.InvalidURL:
            #for invalid urls
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
            print("\nUser Report will be generated shortly!", end=" ")
        else:
            print("=========================================================================")
            print("USER_NAME \t\t NO_OF_TWEETS\n")
            for user in list(users):
                print("{}\t\t{}".format(user,users[user]))
        print("\n")

    def generate_link_report(self):
        #Printing link report

        global domains
        if domains == {}:
            print("Link Report will be generated shortly!")
        else:
            print("--------------------------------------------------------------------------")
            print("TOTAL UNIQUE DOMAINS = ",len(domains))
            print("\n")
            sorted_domains = sorted(((count,domain_name) for domain_name,count in domains.items()), reverse=True)
            for domain in sorted_domains:
                print(domain)
        print("=========================================================================")


    def run(self):
        #Running thread
        while True:
            self.generate_user_report()
            self.generate_link_report()
            time.sleep(self.interval) #thread will sleep for 60s
    
#===========================================MAIN=================================================
if __name__ == "__main__":

    keyword = input("Enter the keyword: ")

    printReport = PrintReport() #Starting print thread to generate report every 60s
    stream_listener = StreamListener() #Creating object for twitter stream

    try:
        stream = tweepy.Stream(auth=api.auth, listener=stream_listener) #starting twitter stream
        stream.filter(track=[keyword],languages=["en"])
    except Exception as ex:
        print("ERROR:", ex.__class__.__name__)
        print("Terminating!")
        sys.exit()