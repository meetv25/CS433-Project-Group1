import socket, threading, sys, time, os, signal, time

lock = threading.Lock()
if(not(os.path.exists("Logs"))): os.mkdir("Logs")
log_file_name = "Logs/logs_" + str(time.localtime()[0])[2:] + str(time.localtime()[1]) + str(time.localtime()[2]) + "_" + str(time.localtime()[3]) + str(time.localtime()[4]) + str(time.localtime()[5]) + ".txt"


# The invokations with debug_option=1, can be used to debug the program , you need to simply uncomment them.  
def logg(debug_option,message):
    print(message)
    log_file_fd = open(log_file_name,"a")
    log_file_fd.write("\n"+"Debug -> "*(debug_option==1) + str(message))
    log_file_fd.close()
    # If debug_option=0, it simply writes to log-file and the terminal output
    # If debug_option=1, it pre-pends the "Debug ->" to easily find it 


def signal_handler(signal,frame):
    """ To make the program stop when Ctrl+C is pressed. """
    logg(0,'\n\nExiting via Ctrl+C.\n\n')
    sys.exit(0)

signal.signal(signal.SIGINT,signal_handler)
logg(0,'\nPress Ctrl+C and wait for some time to exit.')



class ProxyServer:
    """ Creates an instance of our implemented smart forward proxy server. """

    def __init__(self,host,port):
        """ Creates a server on the `host` and listens to `port`. Initiates other resources. """
        self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server.bind((host,port))
        self.server.listen(5)

        self.cache = dict()                         # Stores url, response, caching time
        self.uncaching_time = 60                    # Set your unchaching duration in seconds
        self.cache_content_times = 0                # How many times cache has been updated
        self.blocked_urls = ["example.com"]         # A list of blocked urls
        
        self.blacklist = dict()                     # Stores users and their blacklisted urls
        self.ad_urls = set()                        # Stores all the advertisement websites
        try: self.load_ad_domains("easylist.txt")   # To load such websites from a local file
        except:pass

        logg(0,f"\n[*] Proxy server started on {host}:{port} .\n")


    def uncache(self):
        logg(0,"Cache Cleaner has started.\n\n")
        while(1):
            ### logg(1,f"\n Cache invalidated at this time : {time.time()} . \n")
            
            with lock:      # Because the cache is a shared resourse between Uncache thread & client_handler threads
                curr_time = time.time()
                for url in self.cache:
                    if(self.cache[url][1] - curr_time >= self.uncaching_time):
                        self.cache.pop(url)
            time.sleep(self.uncaching_time)
            
            ### logg(1,f"\n Cache Length at this time is : {len(self.cache)} . \n")
            ### logg(1,f"\n Cache status at this time is : {self.cache} . \n")
    

    def add_blacklist(self,usr,site,client_socket):
        """ Adds a url to blacklist of user. """
        if(usr not in self.blacklist):
            self.blacklist[usr] = set()
        if(site in self.blacklist[usr]):
            client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + b"This url is already in your blacklist.")
            logg(0, str(site) + " website is already in blacklist of user " + str(usr) + " .\n")
        else:
            self.blacklist[usr].add(site)
            client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + b"This url has been added to your blacklist.")
            logg(0, str(site) + " website added to blacklist of user " + str(usr) + " .\n")
        client_socket.close()
    

    def remove_blacklist(self,usr,site,client_socket):
        """ Removes a url from blacklist of user. """
        if(usr in self.blacklist):
            if(site in self.blacklist[usr]):
                self.blacklist[usr].discard(site)
                client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + b"This url has been removed from your blacklist.")
                logg(0, str(site) + " website removed from blacklist of user " + str(usr) + " .\n")
            else:
                client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + b"This url is not in your blacklist.")
                logg(0, str(site) + " website is not in blacklist of user " + str(usr) + " .\n")
        else:
            client_socket.send(b"HTTP/1.1 200 OK\r\n\r\n" + b"You have not blacklisted any website.")
            logg(0, str(usr) + " has not blacklisted any website.\n")
        client_socket.close()
    

    def load_ad_domains(self,file_path):
        """ Loads the AD-urls domains from a local file. """
        with open(file_path,'r',encoding='utf-8') as file:
            lines = file.readlines()
            for line in lines:
                domain = line.strip()
                if(domain and not domain.startswith('#')):  # To Exclude Comments
                    self.ad_urls.add(domain)


    def handle_client(self,client_socket,client_ip_and_port):
        """ Proccesses a request for a client, using our implemented proxy. """

        user_ip = client_ip_and_port[0]
        request = client_socket.recv(4096)      # Get the request from the client browser and extract info
        ### logg(1,f"This is the request :  || {request}  || .")

        if(request==b''): return
        first_line = request.split(b'\n')[0]
        url = first_line.split(b' ')[1]


        # Check for URL blockage
        for blocked_url in self.blocked_urls:
            if(blocked_url.encode() in url):
                client_socket.send(b"HTTP/1.1 403 Forbidden\r\n\r\n" + b"\nThis URL is blocked by the proxy.")
                client_socket.close()
                logg(0,f"{blocked_url} url is blocked by proxy, which is requested by user {user_ip}.\n")
                return

         
        # Check if URL is an ad
        if(url in self.ad_urls):
            client_socket.send(b"HTTP/1.1 204 No Content\r\n\r\n" + b"\nThis URL is blocked by the proxy for being recorded as an ADvertisement URL.")
            client_socket.close()
            logg(0, str(url) + " is an ADvertisement URL, accessed by user " + str(user_ip) + " .\n")
            return


        # Check for url blacklisting
        if("_block_" in str(url)):          # If the request is to block the url
            self.add_blacklist(user_ip, str(url).split(":")[0][9:], client_socket)      # Closes socket internally
            return
        elif("_unblock_" in str(url)):      # If the request is to unblock the url
            self.remove_blacklist(user_ip, str(url).split(":")[0][11:], client_socket)  # Closes socket internally
            return
        
        # If the url client requested for is blacklisted by him
        elif(user_ip in self.blacklist):
            for blocked_url in (self.blacklist[user_ip]):
                if blocked_url.encode() in url:
                    client_socket.send(b"HTTP/1.1 403 Forbidden\r\n\r\n" + b"\nYou have Blacklisted this URL. Use _unblock_<URL> to unblock it.")
                    client_socket.close()
                    logg(0,f"Blacklisted url encountered by user_ip {user_ip}\n")
                    return


        # Check for URL caching
        if url in self.cache:
            with lock:          # Cache is shared between uncaching/using
                client_socket.send(self.cache[url][0])
                client_socket.close()
                ### logg(1,"Cahed URL. Sending cached.\n")
                return


        # Otherwise, contact destination server and fetch response data

        # Extract (1) destination host , (2) destination port , (3) Domain - from the request
        http_pos = url.find(b"http://")
        if(http_pos == -1): temp = url
        else: temp = url[(http_pos+7):]
        
        port_pos = temp.find(b":")
        web_server_pos = temp.find(b"/")
        if(web_server_pos == -1): web_server_pos = len(temp)
        
        web_server = ""
        port = -1
        if(port_pos == -1 or web_server_pos < port_pos):
            port = 80
            web_server = temp[:web_server_pos]
        else:
            port = int(temp[(port_pos+1):web_server_pos])
            web_server = temp[:port_pos]


        # Connect and request for data
        try:
            destination_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            destination_server.connect((web_server,port))
            destination_server.send(b"GET / HTTP/1.1\r\nHost: " + web_server + b"\r\n\r\n")
            
            response_data = b""
            while(True):
                data = destination_server.recv(4096)
                if(len(data) <= 0): break
                response_data += data
            
            destination_server.close()
            client_socket.send(response_data)
            client_socket.close()


            # Cache the received response with its caching time 
            with lock:
                self.cache[url] = [response_data, time.time()]
                self.cache_content_times += 1
            ### logg(1,f"Times we cached the data is {self.cache_content_times} .")


        except Exception as e:
            logg(0,f"[!] Error: {e} .")
            client_socket.send(b"HTTP/1.1 500 Internal Server Error\r\n\r\n" + b"Some Error Occurred from web-server side.")
            client_socket.close()



    def run(self):
        """ To run our implemented proxy server. """

        # To start invalidating the cache / uncaching independently of any client/request
        cache_cleaner = threading.Thread(target=self.uncache)
        cache_cleaner.setDaemon(True)       # The thread exits when main exits
        cache_cleaner.start()
        
        logg(0,f"\n-> Press Ctrl+C to exit. Though, it may take some time.")
        while(1):
            client_sock, client_ip_and_port = self.server.accept()    # Get a request from a client
            logg(0,f"\n[*] Received connection from {client_ip_and_port[0]}:{client_ip_and_port[1]} .")

            # Send it in a new thread for processing and inititate it
            client_handler = threading.Thread(target=self.handle_client, args=(client_sock,client_ip_and_port))
            client_handler.setDaemon(True)
            client_handler.start()


if __name__ == "__main__":
    # Starts the proxy server onto the machine on which the code is run & listens at port 8080
    proxy = ProxyServer("0.0.0.0",8080)
    proxy.run()
