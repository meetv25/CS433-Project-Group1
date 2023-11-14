# CS433-Project-Group1

We are running Proxy Server using more than one systems by running our proxy server on one system and client(s) on other systems. 

### Instructions to run :
Make sure all the systems are connected with each other and the proxy system is connected to internet. 

Proxy server system : Run the main .py file and keep it running.

Client System : In order to make sure the client's request goes via the above proxy server, Go to the settings, search for proxy, click it, turn on the manual connection option, write the proxy system's public IPv4 address in the IP field, and write `8080` in the port field. Click Save. Now, all your web requests will go via the proxy system. 

Make sure the proxy .py program is running on proxy system. On client(s), go to any browser, and search for any HTTP only website. For example, `http://httpforever.com` , `http://neverssl.com` etc. Wait for some time, varying from 3 seconds to 5 minutes, to receieve a response. 

**Blacklisting**

To block or unblock a website, add `block_` or `_unblock_` before website's url, but after `://` .

For example:
After searching `http://neverssl.com`, if user wnts to block it then he can search for `http://_block_neverssl.com`  This will add `neverssl.com` in blacklist of user.
Similary use `http://_unblock_neverssl.com` to unblock the website.
